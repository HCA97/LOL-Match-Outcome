import argparse
from typing import Tuple, Dict, Any, List
import itertools
from functools import partial

import numpy as np
import pandas as pd
import wandb
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix

import config as cfg
import utils

WANDB = False


def load_data(data_path: str) -> pd.DataFrame:
    df = pd.read_csv(data_path)
    df.dropna(inplace=True)

    return df


def preprocess_data(
    data: pd.DataFrame, cat_columns: List[str] = [], num_columns: List[str] = []
) -> Tuple[np.ndarray, np.ndarray]:
    # convert categorical data to one-hot vectors

    # num_columns = [
    #     f"{team}_team_{lane}_{feat}"
    #     for team, lane, feat in itertools.product(
    #         ["blue", "red"],
    #         ["top", "jg", "mid", "bot", "sup"],
    #         ["winRate", "champPickRate"],
    #     )
    # ]
    # categorical columns
    if not cat_columns:
        cat_columns = [
            "tier",
        ] + [
            f"{team}_team_{lane}"
            for team, lane in itertools.product(
                ["blue", "red"], ["top", "jg", "mid", "bot", "sup"]
            )
        ]

    champs = utils.get_existing_champs()
    tiers = ["silver", "gold", "platinum", "diamond"]
    end = OneHotEncoder(
        categories=[tiers] + [champs for _ in range(1, len(cat_columns))],
        sparse_output=False,
    )
    # end = LabelEncoder()
    # end.classes_ = np.array(champs)

    y = np.array(data["winner"] == "RED", dtype=float)

    # numerical columns
    if num_columns:
        X_num = np.array(data[num_columns])
    else:
        X_num = np.array(data.drop(columns=["winner"] + cat_columns))

    # tier_map = {tier: i for i, tier in enumerate(tiers)}
    # champ_map = {champ: i for i, champ in enumerate(champs)}

    # cat_map = {**tier_map, **champ_map}

    X_cat = np.array(
        data[cat_columns]
        .apply(lambda x: x.astype(str).str.lower())
        .replace("monkeyking", "wukong")  # funny story
    )

    X_onehot = end.fit_transform(X_cat)

    X = np.concatenate((X_onehot, X_num), axis=1)

    return X, y


def sweep(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    sweep_config: Dict[str, Any],
    count: int = 5,
):
    def _train():
        nonlocal X_train, y_train, X_test, y_test
        wandb.init()
        config: dict = wandb.config

    sweep_id = wandb.sweep(
        sweep_config, project=cfg.WANDB_PROJECT, entity=cfg.WANDB_ENTITY
    )
    wandb.agent(
        sweep_id,
        partial(
            train_rf, X_train=X_train, y_train=y_train, X_test=X_test, y_test=y_test
        ),
        count=count,
        project=cfg.WANDB_PROJECT,
        entity=cfg.WANDB_ENTITY,
    )
    wandb.config


def train_rf(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    sweep_run: bool = False,
):
    # if sweep_run:
    wandb.init()
    config: dict = wandb.config
    print("WANDB Config", config)
    rfc = RandomForestClassifier(**config)
    rfc.fit(X_train, y_train)

    y_pred_test = rfc.predict(X_test)
    y_pred_train = rfc.predict(X_train)

    test_acc = accuracy_score(y_test, y_pred_test)
    train_acc = accuracy_score(y_train, y_pred_train)
    print(f"Test Acc {test_acc} | Train Acc {train_acc}")

    wandb.log({"test_acc": test_acc, "train_acc": train_acc})


def main(
    train_path: str,
    test_path: str,
    mode: str = "train",
    sweep_config: Dict[str, Any] = {},
):
    global WANDB

    # wandb.init(project=cfg.WANDB_PROJECT, entity=cfg.WANDB_ENTITY)
    WANDB = wandb.login(relogin=True, key=cfg.WANDB_KEY)

    if WANDB:
        train_data = load_data(train_path)

        test_data = load_data(test_path)

        X_train, y_train = preprocess_data(train_data)
        X_test, y_test = preprocess_data(test_data)

        if mode == "train":
            train_rf(X_train, y_train, X_test, y_test)
        elif mode == "sweep":
            sweep(X_train, y_train, X_test, y_test, sweep_config=sweep_config)
        else:
            raise ValueError(
                f"Unknown mode {mode}, only exists 'train' and 'sweep' modes"
            )
    else:
        raise RuntimeError("Failed to login to wandb.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Train model from given csv files.")
    parser.add_argument("--train_path", type=str, help="training data path")
    parser.add_argument("--test_path", type=str, help="testing data path")
    parser.add_argument(
        "--sweep_path", type=str, default=None, help="sweep config path"
    )
    parser.add_argument(
        "--mode", choices=["sweep", "train"], default="train", help="train or sweep"
    )

    args = parser.parse_args()

    # main(args.train_path, args.test_path, args.mode)
    sweep_config = {
        "method": "bayes",
        "metric": {"name": "test_acc", "goal": "maximize"},
        "parameters": {
            "max_depth": {
                "distribution": "int_uniform",
                "min": 1,
                "max": 20,
            },
            "n_estimators": {
                "distribution": "int_uniform",
                "min": 10,
                "max": 50,
            },
            "min_samples_split": {
                "distribution": "int_uniform",
                "min": 2,
                "max": 10,
            },
            "min_samples_leaf": {
                "distribution": "int_uniform",
                "min": 1,
                "max": 4,
            },
        },
    }
    if args.sweep_config:
        sweep_config = args.sweep_config

    # if args.mode == "sweep" and args.sweep_path:
    #     sweep_config = utils.load_json_from_gcs(args.sweep_path)
    # mode = "sweep"
    # train_path = "gs://mlops-zoomcamp-project-data-lake-1234/train_model/data/07-18-2023-07-23-2023-train.csv.gz"
    # test_path = "gs://mlops-zoomcamp-project-data-lake-1234/train_model/data/07-18-2023-07-23-2023-test.csv.gz"
    main(args.train_path, args.test_path, sweep_config=sweep_config, mode=args.mode)
