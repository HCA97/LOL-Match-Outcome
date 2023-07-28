# LOL-Match-Outcome


## Setup

We need following tools:
* gcloud
* docker
* python=3.9

### Test

```bash
make test
```

### Prefect Development

### API Development

## Deployment

### 0. Create Prefect Cloud & GCP Credentials

Create GCP account and project.
Create Prefect Cloud account and .

### 1. Terraform Deployment

Deploy GCP infra:
```bash
make deploy-terraform \
project_id=${project_id} \
prefect_api_key=${prefect_api_key} \
prefect_account_id=${prefect_account_id} \
prefect_workspace_id=${prefect_workspace_id} \
wandb_key=${wandb_key}
```

> ***Note:**
> I didnt wanted to use github actions because I didn't feel safe putting keys in github secrets.*

> ***Note:**
> Before you approve apply make sure you double check the changes.*

### 2. Prefect Blocks

```bash
make prefect-blocks \
sa_path=${SA_PATH} \
riot_api_key=${RIOT_API_KEY}
```

### 3. Prefect Deployment

> Note:
> If you want to skip the data collection path and want to use the public data then you need deploy training pipelines. (`deploy-train-model & deploy-traininig-pipeline`)

To deploy the all the pipelines run:
```bash
deploy-prefect
```
