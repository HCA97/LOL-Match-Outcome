check-python-lint:
	isort .
	black .
	pylint --recursive=y .

check-terraform:
	cd terraform; \
	terraform fmt --recursive; \
	terraform validate 

check: check-python-lint check-terraform

prefect-setup: 
	prefect cloud login
	prefect block register -m prefect_gcp.cloud_run

local-setup: 
	pip install -r requirements.txt	
	pre-commit

terraform-setup:
	cd terraform; terraform init

setup: local-setup prefect-setup terraform-setup

prefect-blocks:
	python prefect/blocks.py --sa_path $(sa_path) --riot_api_key $(riot_api_key)

deploy-collect-matches:
	cd prefect/collect_matches; python deployment.py

deploy-full-pipeline:
	cd prefect/full_pipeline; python deployment.py

deploy-train-model:
	cd prefect/train_model; python deployment.py

deploy-traininig-pipeline:
	cd prefect/training_pipeline; python deployment.py

deploy-prefect: deploy-collect-matches deploy-train-model deploy-traininig-pipeline deploy-full-pipeline
	

deploy-terraform: terraform-setup check-terraform
	gcloud auth login
	gcloud auth application-default login
	cd terraform; \
	terraform apply \
		-var="project=$(project_id)" \
		-var="prefect_key=$(prefect_api_key)" \
		-var="prefect_account_id=$(prefect_account_id)" \
		-var="prefect_workspace_id=$(prefect_workspace_id)" \
		-var="wandb_key=$(wandb_key)" 
