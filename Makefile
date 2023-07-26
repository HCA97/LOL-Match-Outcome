check-python-lint:
	isort .
	black .
	pylint --recursive=y .

check-terraform:
	cd terraform
	terraform fmt --recursive
	terraform validate 
	cd ..

check: check-python-lint check-terraform

prefect-setup: 
	prefect cloud login
	prefect block register -m prefect_gcp.cloud_run

local-setup: 
	pip install -r requirements.txt	
	pre-commit

terraform-setup:
	cd terraform
	terraform init
	cd ..

setup: local-setup prefect-setup terraform-setup