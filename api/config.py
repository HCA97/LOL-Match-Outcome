import os
import wandb

WANDB_API_KEY = os.getenv("WANDB_API_KEY")
# assert WANDB_API_KEY, "WANDB Key must be provided"

WANDB_PATH = os.getenv("WANDB_PATH", "hca97/model-registry/lol-match-predictor")

assert wandb.login(key=WANDB_API_KEY), "Failed to login to WANDB"

DEFAULT_RUN_ID = os.getenv("DEFAULT_RUN_ID", "07-14-2023-07-21-2023")

DATA_LAKE = os.getenv("DATA_LAKE", "mlops-zoomcamp-project-data-lake-1234")
