from main import train_classifier
from prefect.deployments import Deployment
from prefect.filesystems import GCS

gcs_block = GCS.load("mlops-project-deployment")

gcs_deployment_tain_model = Deployment.build_from_flow(
    flow=train_classifier,
    name="Train-Model",
    work_queue_name="match-predictor",
    storage=gcs_block,
    path="train_model",
    entrypoint="main.py:train_classifier",
)


if __name__ == "__main__":
    gcs_deployment_tain_model.apply()
