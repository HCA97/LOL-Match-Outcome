# LOL-Match-Outcome

Introducing Match Predictor, an innovative application specifically designed for the European server of League of Legends. As a fellow League of Legends player, I understand the importance of making informed decisions and strategizing effectively. That's why I am developing Match Predictor to enhance the gaming experience for personal and friend usage alike. By leveraging the power of machine learning, this api determines which team will win based on team composition.

## Setup

We need following tools:
* gcloud
* docker
* terraform
* python=3.9

### Test

You can run the tests using:

```bash
make test
```

### Prefect Development

You can easly run each prefect locally like you run python code. But before you start running them don't forget to create necessary prefect blocks and deployments.

### API Development

If you are using vscode you can run the api in the debug mode easly.

> ***Note:**
> Before you started the api don't forget to login `wandb` and `gcloud`*

> ***Note:**
> You can find example request in [example.http](example.http). You might need to install [
REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)*

## Deployment

> There are some config parameters you need to update.
> Please check each `config.py` and determine which variables you want to change.

### 0. Create Prefect Cloud & GCP Credentials

Create GCP account and project.
Create Prefect Cloud account and workspace.


### 0.1. Leauge of Legends API Key (Optinal)

If you want to run all the pipeline then

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
