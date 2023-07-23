import os


WANDB_KEY = os.getenv("WANDB_API_KEY")
WANDB_PROJECT = os.getenv("WANDB_PROJECT", "lol-match-predictor")
WANDB_ENTITY = os.getenv("WANDB_ENTITY", "hca97")
