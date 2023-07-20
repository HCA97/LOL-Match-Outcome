from prefect.deployments import Deployment
from prefect.filesystems import GCS

from main import workflow


# gcs_block = GCS.load("mlops-project-deployment")

# gcs_deployment = Deployment.build_from_flow(
#     flow=workflow,
#     name="Collect-Matches",
#     work_queue_name="match-predictor",
#     storage=gcs_block,
#     entrypoint="collect_matches/main.py:workflow",
#     parameters={"max_players": 1, "tier": "GOLD", "division": "I"},
# )

# if __name__ == "__main__":
#     gcs_deployment.apply()


from main import main_workflow


gcs_block = GCS.load("mlops-project-deployment")

gcs_deployment = Deployment.build_from_flow(
    flow=main_workflow,
    name="main-workflow",
    work_queue_name="main-workflow",
    storage=gcs_block,
    entrypoint="collect_matches/main.py:main_workflow",
    parameters={"max_players": 1},
)

if __name__ == "__main__":
    gcs_deployment.apply()
