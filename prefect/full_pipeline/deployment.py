from prefect.deployments import Deployment
from prefect.filesystems import GCS
from prefect.server.schemas.schedules import CronSchedule

from main import main


gcs_block = GCS.load("mlops-project-deployment")

gcs_deployment_workflow = Deployment.build_from_flow(
    flow=main,
    name="Full-Workflow",
    work_queue_name="match-predictor",
    storage=gcs_block,
    path="full_pipeline",
    entrypoint="main.py:main",
    parameters={"max_players": 100},
    schedule=(CronSchedule(cron="0 0 * * *", timezone="UTC")),
)

if __name__ == "__main__":
    gcs_deployment_workflow.apply()
