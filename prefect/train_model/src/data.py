from typing import Tuple, List, Union, Any
import itertools

import numpy as np
import pandas as pd

from prefect import task

from sklearn.preprocessing import OneHotEncoder

from src.utils import get_existing_champs
from src.logging import log_preprocess


@task(log_prints=True)
def load_data(data_path: str) -> pd.DataFrame:
    df = pd.read_csv(data_path)
    df.dropna(inplace=True)

    return df


@task(log_prints=True)
def preprocess_data(
    data: pd.DataFrame,
    cat_columns: List[str] = [],
    num_columns: List[str] = [],
    return_model: bool = False,
) -> Union[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray, Any]]:
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

    if not num_columns:
        num_columns = list(data.select_dtypes(include=["float"]).columns)

    champs = get_existing_champs()
    tiers = ["silver", "gold", "platinum", "diamond"]
    enc = OneHotEncoder(
        categories=[tiers] + [champs for _ in range(1, len(cat_columns))],
        sparse_output=False,
    )

    y = np.array(data["winner"] == "RED", dtype=float)

    # numerical columns
    X_num = np.array(data[num_columns])

    X_cat = np.array(
        data[cat_columns]
        .apply(lambda x: x.astype(str).str.lower())
        .replace("monkeyking", "wukong")  # funny story
    )

    X_onehot = enc.fit_transform(X_cat)

    X = np.concatenate((X_onehot, X_num), axis=1)
    if return_model:
        return X, y, enc
    return X, y
