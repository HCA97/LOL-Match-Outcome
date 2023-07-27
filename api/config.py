import os

WANDB_API_KEY = os.getenv("WANDB_API_KEY")

WANDB_PATH = os.getenv("WANDB_PATH", "hca97/model-registry/lol-match-predictor")

# TODO: Select the latest `run_id`
DEFAULT_RUN_ID = os.getenv("DEFAULT_RUN_ID", "07-14-2023-07-21-2023")

DATA_LAKE = os.getenv("DATA_LAKE", "mlops-zoomcamp-project-data-lake-1234")
