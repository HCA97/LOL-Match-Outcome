from prefect.deployments import Deployment
from prefect.filesystems import GCS
from prefect.server.schemas.schedules import CronSchedule

from main import workflow, main_workflow


gcs_block = GCS.load("mlops-project-deployment")

gcs_deployment_workflow = Deployment.build_from_flow(
    flow=workflow,
    name="Collect-Matches",
    work_queue_name="match-predictor",
    storage=gcs_block,
    entrypoint="collect_matches/main.py:workflow",
    parameters={"max_players": 1, "tier": "GOLD", "division": "I"},
)

gcs_deployment_main_workflow = Deployment.build_from_flow(
    flow=main_workflow,
    name="main-workflow",
    work_queue_name="main-workflow",
    storage=gcs_block,
    entrypoint="collect_matches/main.py:main_workflow",
    parameters={"max_players": 100},
    schedule=(CronSchedule(cron="0 0 * * *", timezone="UTC")),
)

if __name__ == "__main__":
    gcs_deployment_workflow.apply()
    gcs_deployment_main_workflow.apply()
