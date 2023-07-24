variable "project" {
  description = "Your GCP Project ID"
}

variable "region" {
  description = "Region for GCP resources. Choose as per your location: https://cloud.google.com/about/locations"
  default     = "europe-west1"
  type        = string
}


variable "prefect_key" {
  description = "PREFECT API KEY"
  type        = string
  sensitive   = true
}

variable "prefect_account_id" {
  description = "PREFECT CLOUD ACCOUNT ID"
  type        = string
  sensitive   = true
}

variable "prefect_workspace_id" {
  description = "prefect cloud workspace id"
  type        = string
  sensitive   = true
}

variable "wandb_key" {
  description = "weight and bais api key"
  type        = string
  sensitive   = true
}
