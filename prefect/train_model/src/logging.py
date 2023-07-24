import os
import datetime as dt
from typing import List, Any

import wandb

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from prefect import task
import matplotlib

matplotlib.use("Agg")

from src.utils import dump_pickle, load_pickle


@task(log_prints=True)
def log_register_models(project: str, entity: str, run_id: str):
    artifact_cfl = wandb.use_artifact(
        f"{entity}/{project}/lol-match-predictor-clf:latest",
        type="model",
    )
    clf_path = artifact_cfl.download()
    clf_path = f"{clf_path}/{os.listdir(clf_path)[0]}"

    artifact_preprocess = wandb.use_artifact(
        f"{entity}/{project}/lol-match-predictor-preprocess:latest",
        type="model",
    )
    enc_path = artifact_preprocess.download()
    enc_path = f"{enc_path}/{os.listdir(enc_path)[0]}"

    clf = load_pickle(clf_path)
    enc, cat_columns, num_columns = load_pickle(enc_path)

    os.makedirs("models", exist_ok=True)
    curr_date = dt.datetime.today().strftime("%Y-%m-%d")
    path = f"models/clf-enc-{curr_date}.pkl"
    dump_pickle((clf, enc, cat_columns, num_columns), path)

    artifact_all = wandb.Artifact("lol-match-predictor-clf-end", type="model")
    artifact_all.add_file(path)
    wandb.log_artifact(artifact_all)

    wandb.run.link_artifact(
        artifact_all,
        f"{entity}/model-registry/{project}",
        aliases=["latest", run_id],
    )


@task(log_prints=True)
def log_model(model, run_id: str):
    os.makedirs("models", exist_ok=True)
    path = f"models/clf-{run_id}.pkl"
    wandb.init()
    dump_pickle(model, path)
    artifact = wandb.Artifact("lol-match-predictor-clf", type="model")
    artifact.add_file(path)
    wandb.log_artifact(artifact)


@task(log_prints=True)
def log_preprocess(
    enc: Any, cat_columns: List[str], num_columns: List[str], run_id: str
):
    os.makedirs("models", exist_ok=True)
    path = f"models/preprocess-{run_id}.pkl"
    wandb.init()
    dump_pickle((enc, cat_columns, num_columns), path)
    artifact = wandb.Artifact("lol-match-predictor-preprocess", type="model")
    artifact.add_file(path)
    wandb.log_artifact(artifact)


@task(log_prints=True)
def log_data(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    run_id: str,
):
    os.makedirs("data", exist_ok=True)
    path = f"data/{run_id}.pkl"
    dump_pickle((X_train, y_train, X_test, y_test), path)

    artifact = wandb.Artifact(
        "lol-match-predictor-dataset", type="preprocessed_dataset"
    )
    artifact.add_dir("data/")
    wandb.log_artifact(artifact)


@task(log_prints=True)
def log_feat_importance(model, num_columns: list, cat_columns: list):
    coef = model.coef_[0]
    feat_names = cat_columns + num_columns

    sfg_importances = pd.Series(coef, index=feat_names)

    fig, ax = plt.subplots()
    sfg_importances.plot.bar(ax=ax)
    ax.set_title("Feature importances of SGD")
    ax.set_ylabel("SGD Weight")
    fig.tight_layout()
    wandb.log({"plot": plt})
