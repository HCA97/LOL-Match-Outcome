terraform {
  required_version = ">= 1.0"
  backend "gcs" {
    bucket = "mlops-project-tfstate"
    prefix = "terraform/state"
  }
  required_providers {
    google = {
      source = "hashicorp/google"
    }
  }
}

provider "google" {
  project = var.project
  region  = var.region
}


#
# Infra
#

resource "google_project_service" "project" {
  for_each = toset([
    "compute.googleapis.com",
    "iamcredentials.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "run.googleapis.com"
  ])
  project = var.project
  service = each.key
}

#
# Prefect
#

resource "google_storage_bucket_iam_member" "storage_permission" {
  for_each = toset([
    google_storage_bucket.data-lake-bucket.name,
    google_storage_bucket.prefect-bucket.name
  ])
  bucket = each.value
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.compute_engine_sa.email}"
}


resource "google_bigquery_dataset_iam_member" "dataset_iam_member" {
  for_each = toset([
    "roles/bigquery.dataEditor",
    "roles/bigquery.user"
  ])
  dataset_id = google_bigquery_dataset.datawarehouse.dataset_id
  role       = each.value
  member     = "serviceAccount:${google_service_account.compute_engine_sa.email}"
}


resource "google_project_iam_member" "permissions" {
  for_each = toset([
    "roles/bigquery.jobUser",
    "roles/bigquery.readSessionUser",
    "roles/storage.insightsCollectorService"
  ])
  project = var.project
  role    = each.key
  member  = "serviceAccount:${google_service_account.compute_engine_sa.email}"
}

resource "google_service_account" "compute_engine_sa" {
  project      = var.project
  account_id   = "compute-engine-sa"
  display_name = "Service Account for Compute Engine"

  depends_on = [
    google_project_service.project
  ]
}


resource "google_compute_instance" "prefect" {
  name                = "prefect"
  machine_type        = "e2-medium"
  zone                = "${var.region}-b"
  deletion_protection = false


  metadata_startup_script = templatefile("${path.module}/install.tftpl", {
    prefect_key          = var.prefect_key
    prefect_account_id   = var.prefect_account_id
    prefect_workspace_id = var.prefect_workspace_id,
    wandb_key            = var.wandb_key
  })

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2004-lts"
      size  = 30
    }
  }

  network_interface {
    network = "default"
    access_config {
      // Ephemeral public IP
    }
  }

  service_account {
    email  = google_service_account.compute_engine_sa.email
    scopes = ["cloud-platform"]
  }

  depends_on = [
    google_project_service.project
  ]
}

resource "google_storage_bucket" "data-lake-bucket" {
  name     = "mlops-zoomcamp-project-data-lake-1234"
  location = var.region

  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  force_destroy = true
}

resource "google_storage_bucket" "prefect-bucket" {
  name     = "mlops-zoomcamp-project-prefect-code-1234"
  location = var.region

  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  force_destroy = true
}

#
# BIGQUERY
#

resource "google_bigquery_dataset" "datawarehouse" {
  dataset_id = "datawarehouse"
  project    = var.project
  location   = var.region
}



locals {
  table_name = "matches"
  champ_stats_query = templatefile("${path.module}/champ_stats.tftpl", {
    project    = var.project
    dataset_id = google_bigquery_dataset.datawarehouse.dataset_id
    table_name = local.table_name
  })
  matches_query = templatefile("${path.module}/matches.tftpl", {
    project    = var.project
    dataset_id = google_bigquery_dataset.datawarehouse.dataset_id
    table_name = local.table_name
  })
}

resource "google_bigquery_job" "champ_stats" {
  job_id   = "champ_stats_query-${md5(local.champ_stats_query)}"
  project  = google_bigquery_dataset.datawarehouse.project
  location = google_bigquery_dataset.datawarehouse.location


  query {
    query              = local.champ_stats_query
    create_disposition = ""
    write_disposition  = ""
    use_query_cache    = true
  }
}


resource "google_bigquery_job" "matches" {
  job_id   = "matches_query-${md5(local.matches_query)}"
  project  = google_bigquery_dataset.datawarehouse.project
  location = google_bigquery_dataset.datawarehouse.location


  query {
    query              = local.matches_query
    create_disposition = ""
    write_disposition  = ""
    use_query_cache    = true
  }
}


#
# WANB Secret
#

resource "google_secret_manager_secret" "wandb-key" {
  secret_id = "wandb_api_key"
  project   = var.project

  replication {
    automatic = true
  }

  depends_on = [google_project_service.project]
}

resource "google_secret_manager_secret_version" "wandb-key-secret" {
  secret = google_secret_manager_secret.wandb-key.id

  secret_data = var.wandb_key
}


#
# API
# 

resource "google_artifact_registry_repository" "api-repo" {
  location      = var.region
  repository_id = "api-repo"
  description   = "docker repo for api"
  format        = "DOCKER"
  depends_on    = [google_project_service.project]
}

data "archive_file" "api-zip" {
  type        = "zip"
  source_dir  = "${path.module}/../api"
  output_path = "${path.module}/../tmp/api.zip"
}

locals {
  docker_tag = "${var.region}-docker.pkg.dev/${var.project}/${google_artifact_registry_repository.api-repo.name}/api:${data.archive_file.api-zip.output_md5}"
}
resource "null_resource" "build_docker_image" {
  triggers = {
    api_md5 = data.archive_file.api-zip.output_md5
  }
  provisioner "local-exec" {
    command = <<EOT

      gcloud auth configure-docker --quiet

      cd ../api
      docker build -t ${local.docker_tag} .
      docker push ${local.docker_tag}

    EOT
  }

}

resource "google_storage_bucket_iam_member" "api-storage-permission" {
  bucket = google_storage_bucket.data-lake-bucket.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.api_sa.email}"
}

resource "google_project_iam_member" "api-permissions" {
  for_each = toset([
    "roles/secretmanager.secretAccessor",
    "roles/storage.insightsCollectorService",
    "roles/run.invoker"
  ])
  project = var.project
  role    = each.key
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

resource "google_service_account" "api_sa" {
  project      = var.project
  account_id   = "api-sa"
  display_name = "Service Account for Cloud run"

  depends_on = [
    google_project_service.project
  ]
}



resource "google_cloud_run_service" "api" {
  name     = "predictor-api"
  location = var.region


  template {
    spec {
      timeout_seconds       = 10
      container_concurrency = 30
      service_account_name  = google_service_account.api_sa.email
      containers {
        image = local.docker_tag
        env {
          name = "WANDB_API_KEY"
          value_from {
            secret_key_ref {
              key  = "latest"
              name = google_secret_manager_secret.wandb-key.secret_id
            }
          }
        }
      }

    }

    metadata {

      annotations = {
        "autoscaling.knative.dev/maxScale" = "1"
        "run.googleapis.com/client-name"   = "terraform"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [null_resource.build_docker_image, google_project_service.project, google_project_iam_member.api-permissions]
}


data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  location    = google_cloud_run_service.api.location
  project     = google_cloud_run_service.api.project
  service     = google_cloud_run_service.api.name
  policy_data = data.google_iam_policy.noauth.policy_data
}
