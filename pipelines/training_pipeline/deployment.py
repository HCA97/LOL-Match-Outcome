import datetime as dt

from main import main
from prefect.deployments import Deployment
from prefect.filesystems import GCS

gcs_block = GCS.load("mlops-project-deployment")

gcs_deployment_tain_model = Deployment.build_from_flow(
    flow=main,
    name="Training-Pipeline",
    work_queue_name="match-predictor",
    storage=gcs_block,
    description="Training pipeline for match predictor.",
    path="training_pipeline",
    entrypoint="main.py:main",
    parameters={
        "start_time": dt.datetime(2023, 7, 20),
        "end_time": dt.datetime(2023, 7, 21),
    },
)


if __name__ == "__main__":
    gcs_deployment_tain_model.apply()
