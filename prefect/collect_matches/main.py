import datetime as dt
from typing import Optional, List, Dict, Any
import itertools
import asyncio

import pandas as pd

from prefect import flow, task
from prefect.deployments import run_deployment

from google.cloud import bigquery

import config as cfg
import utils


#
# REFECT TASKS
#


@task(name="Solo-Queue-Players", log_prints=True)
def solo_queue_players(division: str, tier: str, max_size: int = 100) -> List[dict]:
    page = 1

    data = []

    while len(data) < max_size:
        with cfg.SESSION.get(
            f'{cfg.REQUEST_URLS["LEAUGE-V4"]}/lol/league/v4/entries/RANKED_SOLO_5x5/{tier}/{division}',
            params={"page": page},
            headers={"X-Riot-Token": cfg.RIOT_API_KEY},
        ) as req:
            if req.status_code != 200:
                print(f"Status code is not 200 it is {req.status_code}")
                break

            res = req.json()

            if not res:
                print("Result is an empty list most likely the end is reached.")
                break

            data.extend(res)

            print(f"Page size {page} - in total {len(res)} new players are added.")

    print(f"In total {tier}-{division} players exists {len(data)}.")
    return data[:max_size]


@task(name="Add-PUUID", log_prints=True)
def add_puuid(players: List[dict]) -> List[dict]:
    new_players = []

    for i, player in enumerate(players):
        if i % 10 == 0:
            print(f"[ADD PUUID] {i}/{len(players)} are done.")

        summoner_name, summoner_id = player["summonerName"], player["summonerId"]
        ids = utils.get_summoner_ids(summoner_name, summoner_id)

        if ids:
            player["summonerPuuid"] = ids["puuid"]
            player["summonerLevel"] = ids["summonerLevel"]
            new_players.append(player)

    print(f"[ADD PUUID] In total {len(new_players)}/{len(players)} puiids obtained.")

    return new_players


@task(name="Upload-To-BQ", log_prints=True)
def upload_to_bq(
    data: List[dict],
    table_name: str,
    partitioning_field: str,
    partitioning_type: str = "DAY",
    clustering_fields: Optional[list] = None,
) -> None:
    client = bigquery.Client(
        project=cfg.CREDENTIALS.project_id, credentials=cfg.CREDENTIALS
    )
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        time_partitioning=bigquery.table.TimePartitioning(
            type_=partitioning_type, field=partitioning_field
        ),
        clustering_fields=clustering_fields,
    )

    table_id = f"{cfg.TABLE_ID}.{table_name}"
    job = client.load_table_from_dataframe(
        pd.DataFrame(data), table_id, job_config=job_config
    )  # Make an API request
    job.result()  # Wait for job to finish


@task(name="Match-History", log_prints=True)
def players_match_history(
    players: list, start_time: dt.datetime, end_time: dt.datetime
) -> list:
    match_histories = []
    for i, summoner_puuid in enumerate(players):
        if i % 10 == 0:
            print(f"{i}/{len(players)} are done.")
        matches = utils.match_history(summoner_puuid, start_time, end_time)
        match_histories.extend(matches)

    return list(set(match_histories))


@task(name="Match-Infos", log_prints=True)
def match_infos(match_ids: list) -> pd.DataFrame:
    participants = []

    for i, match_id in enumerate(match_ids):
        try:
            if i % 10 == 0:
                print(f"[PROCESS MATCHES] {i}/{len(match_ids)} are done.")
            data = utils.get_match_info(match_id)
            participants.extend(utils.match_transform(data))
        except Exception as e:
            print(f"Match Id: {match_id} - Error : {e}")

    return participants


#
# PREFECT FLOWS
#


@flow(name="Collect-Soloque-Players", log_prints=True)
def collect_soloque_players(
    division: str, tier: str, max_players: int = 100
) -> List[str]:
    """collects soloque players for given `division` and `tier` and returns their puuids."""

    # get players
    players = solo_queue_players(division, tier, max_players)

    # get their puuid
    players = add_puuid(players)

    # return puuids for getting match history
    return [player["summonerPuuid"] for player in players]


@flow(name="Process-Matches", log_prints=True)
def collect_matches(
    puuids: list, start_time: dt.datetime, end_time: dt.datetime
) -> None:
    """gets match history of given players and start time."""

    # get match ids
    match_ids = players_match_history(puuids, start_time, end_time)
    print(f"Total games are {len(match_ids)}.")

    # get match infos
    participants = match_infos(match_ids)

    return participants


@flow(name="Workflow", log_prints=True)
def workflow(
    division: str,
    tier: str,
    start_time: Optional[dt.datetime] = None,
    end_time: Optional[dt.datetime] = None,
    max_players: int = 100,
) -> None:
    """get the soloque players and their matches."""

    # get the soloque players players
    puuids = collect_soloque_players(division, tier, max_players)

    # get their matches matches
    if start_time is None:
        # get yesterdays data if start_time is none
        start_time = dt.datetime.utcnow() - dt.timedelta(1)

    if end_time is None:
        end_time = dt.datetime.utcnow()

    matches = collect_matches(puuids, start_time, end_time)

    for match in matches:
        match["division"] = division
        match["tier"] = tier

    # upload to bq
    upload_to_bq(
        matches,
        "matches_test",
        partitioning_field="gameStartTime",
        partitioning_type="DAY",
        clustering_fields=[
            "lane",
            "division",
        ],
    )


async def build_subflow(n: int, deploy_name: str, params: Dict[str, Any]) -> str:
    @flow(name=f"Deploy-Runner-{n}", log_prints=True)
    async def deploy_runner_wrapper(deploy_name: str, params: Dict[str, Any]) -> str:
        print(f"Deployment: {deploy_name} - Params: {params}")
        flow_run = await run_deployment(
            deploy_name, parameters=params, flow_run_name=f"Flow-{n}"
        )
        print(
            f"Flow Status: {flow_run.state_name} - Took: {flow_run.total_run_time.total_seconds()}s"
        )

    await deploy_runner_wrapper(deploy_name, params)


@flow(name="Main-Workflow", log_prints=True)
async def main_workflow(
    start_time: Optional[dt.datetime] = None,
    end_time: Optional[dt.datetime] = None,
    max_players: int = 100,
):
    tiers = ["SILVER", "GOLD", "PLATINUM", "DIAMOND"]
    divisions = ["I", "II", "III", "IV"]

    tasks = []
    for i, (division, tier) in enumerate(itertools.product(divisions, tiers)):
        print(f"[Main-Workflow] {division}-{tier} Running...")
        tasks.append(
            (
                i + 1,
                "Workflow/Collect-Matches",
                {
                    "tier": tier,
                    "division": division,
                    "start_time": start_time,
                    "end_time": end_time,
                    "max_players": max_players,
                },
            )
        )

        if len(tasks) >= 2:
            print(
                f"[Main-Workflow] Waiting for {len(tasks)} number of jobs to finish..."
            )
            await asyncio.gather(*[build_subflow(*task) for task in tasks])
            tasks = []


if __name__ == "__main__":
    division = "I"
    tier = "GOLD"
    start_time = None

    # workflow("I", "GOLD", max_players=1)
    asyncio.run(main_workflow(max_players=3))
