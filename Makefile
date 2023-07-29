check-python-lint:
	isort .
	black .
	pylint --recursive=y .

check-terraform: terraform-setup
	cd terraform; \
	terraform fmt --recursive; \
	terraform validate

check: check-python-lint check-terraform

prefect-setup:
	prefect cloud login
	prefect block register -m prefect_gcp.cloud_run

local-setup:
	pip install -r requirements.txt
	pre-commit install

terraform-setup:
	cd terraform; terraform init

setup: local-setup prefect-setup terraform-setup

prefect-blocks:
	python pipelines/blocks.py --sa_path $(sa_path) --riot_api_key $(riot_api_key)

deploy-collect-matches:
	cd pipelines/collect_matches; python deployment.py

deploy-full-pipeline:
	cd pipelines/full_pipeline; python deployment.py

deploy-train-model:
	cd pipelines/train_model; python deployment.py

deploy-traininig-pipeline:
	cd pipelines/training_pipeline; python deployment.py

deploy-prefect: deploy-collect-matches deploy-train-model deploy-traininig-pipeline deploy-full-pipeline

gcloud-auth:
	gcloud auth login
	gcloud auth application-default login

deploy-terraform: gcloud-auth terraform-setup check-terraform
	cd terraform; \
	terraform apply \
		-var="project=$(project_id)" \
		-var="prefect_key=$(prefect_api_key)" \
		-var="prefect_account_id=$(prefect_account_id)" \
		-var="prefect_workspace_id=$(prefect_workspace_id)" \
		-var="wandb_key=$(wandb_key)"

test-api:
	python -m pytest api/tests/ --disable-warnings

test-prefect:
	ln -sf \
	$(shell pwd)/api/tests/artifacts/data/train_model_data_07-19-2023-07-20-2023_champ_stats.csv.gz \
	$(shell pwd)/pipelines/tests/data/training_pipeline/champ_stats.csv.gz
	python -m pytest pipelines/tests/test_train_model.py --disable-warnings
	python -m pytest pipelines/tests/test_training_pipeline.py --disable-warnings

test: test-api test-prefect

create-dataset: gcloud-auth
	python upload_data.py --project_id $(project_id)
