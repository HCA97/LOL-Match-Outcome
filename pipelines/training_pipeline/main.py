import datetime as dt
from typing import Tuple

import config as cfg
import pandas as pd
from prefect import flow, task
from prefect.flows import FlowRun
from prefect.deployments import run_deployment
from sklearn.model_selection import train_test_split
from prefect_gcp.cloud_storage import GcsBucket


@task(log_prints=True)
def load_matches(start_time: dt.datetime, end_time: dt.datetime) -> pd.DataFrame:
    start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.%f")
    end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S.%f")
    df = pd.read_gbq(
        f"""
        SELECT DISTINCT * EXCEPT(dayHour, weekDay)
        FROM `{cfg.PROJECT_ID}.{cfg.DATASET_ID}.matches`(
            DATETIME('{start_time_str}'), DATETIME('{end_time_str}')
        )
    """,
        cfg.PROJECT_ID,
    )

    return df


@task(log_prints=True)
def load_champ_stats(start_time: dt.datetime, end_time: dt.datetime) -> pd.DataFrame:
    start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.%f")
    end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S.%f")
    df = pd.read_gbq(
        f"""
        SELECT *
        FROM `{cfg.PROJECT_ID}.{cfg.DATASET_ID}.champ_stats`(
            DATETIME('{start_time_str}'), DATETIME('{end_time_str}')
        )
        """,
        cfg.PROJECT_ID,
    )
    return df


@task(log_prints=True)
def split_data(data: pd.DataFrame, split: float) -> Tuple[pd.DataFrame, pd.DataFrame]:
    train, test = train_test_split(data, test_size=split)
    print(f"[Split Data] Train Size: {len(train)} - Test Size: {len(test)}")
    return train, test


@task(log_prints=True)
def add_champ_statistics(
    matches: pd.DataFrame, champ_stats: pd.DataFrame
) -> pd.DataFrame:
    lane_map = {
        "top": "TOP",
        "jg": "JUNGLE",
        "mid": "MIDDLE",
        "bot": "BOTTOM",
        "sup": "UTILITY",
    }
    columns_remove = [
        "mapSide",
        "championName",
        "position",
        "champTotalMatches",
    ]

    df = matches.copy()

    for lane in ["top", "jg", "mid", "bot", "sup"]:
        for team in ["blue", "red"]:
            lane_and_team = f"{team}_team_{lane}"
            df = pd.merge(
                df,
                champ_stats[
                    (champ_stats.position == lane_map[lane])
                    & (champ_stats.mapSide == team.upper())
                ],
                how="inner",
                left_on=["tier", lane_and_team],
                right_on=["tier", "championName"],
            )
            columns_rename = {
                col: f"{lane_and_team}_{col}"
                for col in champ_stats.columns
                if col != "tier"
            }

            # clean up
            df.drop(columns_remove, inplace=True, axis=1)
            df.rename(columns_rename, axis=1, inplace=True, errors="ignore")

    return df


@task(log_prints=True)
def upload_data(data: pd.DataFrame, save_path: str) -> str:
    save_path = f"train_model/data/{save_path}"
    bucket = GcsBucket(bucket=cfg.DATA_LAKE)

    bucket.upload_from_dataframe(data, save_path)

    return f"gs://{cfg.DATA_LAKE}/{save_path}"


@flow(name="Start-Training", log_prints=True)
def start_training(train_path: str, test_path: str):
    flow_run: FlowRun = run_deployment(
        name="Train-Classifier/Train-Model",
        parameters={
            "train_path": train_path,
            "test_path": test_path,
            "wandb_project": cfg.WANDB_PROJECT,
            "wandb_entity": cfg.WANDB_ENTITY,
        },
        flow_run_name="Train-Model",
    )
    print(
        f"Flow Status: {flow_run.state_name} - Took: {flow_run.total_run_time.total_seconds()}s"
    )


@flow(name="Training-Pipeline", log_prints=True)
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
        start_time, end_time = end_time, start_time

    matches_df = load_matches.submit(start_time, end_time)
    champs_stats_df = load_champ_stats.submit(start_time, end_time)

    upload_data.submit(
        champs_stats_df,
        f'{start_time.strftime("%m-%d-%Y")}-{end_time.strftime("%m-%d-%Y")}/champ_stats.csv.gz',
    )

    data = add_champ_statistics.submit(matches_df, champs_stats_df)

    data_train, data_test = split_data.submit(data, split).result()

    train_path = upload_data.submit(
        data_train,
        f'{start_time.strftime("%m-%d-%Y")}-{end_time.strftime("%m-%d-%Y")}/train.csv.gz',
    )
    test_path = upload_data.submit(
        data_test,
        f'{start_time.strftime("%m-%d-%Y")}-{end_time.strftime("%m-%d-%Y")}/test.csv.gz',
    )

    start_training(train_path.result(), test_path.result())


if __name__ == "__main__":
    end_time = dt.datetime.utcnow()
    start_time = end_time - dt.timedelta(1)
    main(start_time, end_time)
