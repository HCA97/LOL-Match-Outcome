import datetime as dt
from typing import Tuple


import pandas as pd

from prefect import flow, task
from sklearn.model_selection import train_test_split

from google.cloud import bigquery

import config as cfg
import utils


@task(log_prints=True)
def load_data(start_time: dt.datetime, end_time: dt.datetime) -> pd.DataFrame:
    pass


@task(log_prints=True)
def split_data(data: pd.DataFrame, split: float) -> Tuple[pd.DataFrame, pd.DataFrame]:
    train, test = train_test_split(data, test_size=split)
    print(f"[Split Data] Train Size: {len(train)} - Test Size: {len(test)}")
    return train, test


@task(log_prints=True)
def add_champ_statistics(
    data: pd.DataFrame, start_time: dt.datetime, end_time: dt.datetime
) -> pd.DataFrame:
    pass


@task(log_prints=True)
def upload_data(data: pd.DataFrame, save_path: str):
    pass


@task(log_prints=True)
def start_training(data_path: str) -> int:
    pass


@flow(log_prints=True)
def main(
    start_time: dt.datetime = None,
    end_time: dt.datetime = None,
    split: float = 0.2,
):
    if end_time is None:
        end_time = dt.datetime.utcnow()

    if start_time is None:
        start_time = end_time - dt.timedelta(7)

    if start_time > end_time:
        tmp = end_time
        end_time = start_time
        start_time = tmp

    data = load_data(start_time, end_time)
    data = add_champ_statistics(data, start_time, end_time)
    data_train, data_test = split_data(data, split)
    train_path = upload_data(
        data_train,
        f'{start_time.strftime("%m-%d-%Y_%H:%M:%S")}-{end_time.strftime("%m-%d-%Y_%H:%M:%S")}-train.parquet',
    )
    test_path = upload_data(
        data_test,
        f'{start_time.strftime("%m-%d-%Y_%H:%M:%S")}-{end_time.strftime("%m-%d-%Y_%H:%M:%S")}-test.parquet',
    )

    status = start_training(train_path, test_path)

    print(f"{status}")


if __name__ == "__main__":
    main()
