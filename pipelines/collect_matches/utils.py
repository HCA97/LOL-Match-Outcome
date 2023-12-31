import json
import datetime as dt

import config as cfg
from google.cloud import storage
from prefect.blocks.system import Secret

# -------------------------- #
# GCS UTILS                  #
# -------------------------- #


def upload_blob_from_memory(bucket_name, contents, destination_blob_name, credentials):
    """Uploads a file to the bucket."""
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(contents, content_type="application/json")


def download_blob_to_memory(bucket_name, file_name, credentials):
    """Downloads a file from bucket to memory."""
    client = storage.Client(credentials=credentials)
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)
    return json.loads(blob.download_as_text(encoding="utf-8"))


def blob_exists(bucket_name, file_name, credentials):
    """Checks if blob exists in the bucket"""
    client = storage.Client(credentials=credentials)
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)
    return blob.exists()


#
#  GET SUMMONER IDS
#


def get_all_ids_by_summoner_id(summoner_id):
    with cfg.SESSION.get(
        f'{cfg.REQUEST_URLS["SUMMONER-V4"]}/lol/summoner/v4/summoners/{summoner_id}',
        headers={"X-Riot-Token": Secret.load("riot-api-key").get()},
    ) as req:
        if req.status_code == 200:
            return req.json()
    return {}


def get_all_ids_by_summoner_name(summoner_name):
    with cfg.SESSION.get(
        f'{cfg.REQUEST_URLS["SUMMONER-V4"]}/lol/summoner/v4/summoners/by-name/{summoner_name}',
        headers={"X-Riot-Token": cfg.RIOT_API_KEY},
    ) as req:
        if req.status_code == 200:
            return req.json()
    return {}


def get_summoner_ids(summoner_name: str, summoner_id: str) -> str:
    file_name = f"players/{summoner_name}_{summoner_id}.json"

    # check if it exists in data lake
    if blob_exists(cfg.DATA_LAKE, file_name, cfg.CREDENTIALS):
        return download_blob_to_memory(cfg.DATA_LAKE, file_name, cfg.CREDENTIALS)

    # if not call riot api
    data = get_all_ids_by_summoner_name(summoner_name)

    if not data:
        print(
            f"Summoner Name ({summoner_name}) not exists using Summoner ID ({summoner_id})."
        )
        data = get_all_ids_by_summoner_id(summoner_id)

    # save the result and return the puuid
    if not data:
        return ""

    upload_blob_from_memory(
        cfg.DATA_LAKE, json.dumps(data, indent=4), file_name, cfg.CREDENTIALS
    )

    return data


#
# GET MATCH INFO
#


def match_history(
    summoner_puuid: str,
    start_time: dt.datetime,
    end_time: dt.datetime,
    count: int = 100,
    match_type: str = "ranked",
) -> list:
    file_name = (
        f'match-history/{summoner_puuid}-{match_type}'
        f'-{start_time.strftime("%m-%d-%Y_%H:%M:%S")}-'
        f'{end_time.strftime("%m-%d-%Y_%H:%M:%S")}.json'
    )

    if blob_exists(cfg.DATA_LAKE, file_name, cfg.CREDENTIALS):
        return download_blob_to_memory(cfg.DATA_LAKE, file_name, cfg.CREDENTIALS)

    match_ids = []
    start = 0

    while True:
        with cfg.SESSION.get(
            f'{cfg.REQUEST_URLS["MATCH-V5"]}/lol/match/v5/matches/by-puuid/{summoner_puuid}/ids',
            params={
                "startTime": int(start_time.timestamp()),
                "endTime": int(end_time.timestamp()),
                "type": match_type,
                "count": count,
                "start": start,
            },
            headers={"X-Riot-Token": Secret.load("riot-api-key").get()},
        ) as req:
            data = []
            if req.status_code == 200:
                data = req.json()

            if not data:
                break

            match_ids.extend(data)
            start += count

            if len(data) < count:
                break

    print(f"In total matches played is {len(match_ids)}.")

    upload_blob_from_memory(
        cfg.DATA_LAKE, json.dumps(match_ids), file_name, cfg.CREDENTIALS
    )

    return match_ids


def get_match_info(match_id: str) -> dict:
    file_name = f"matches/{match_id}.json"

    if blob_exists(cfg.DATA_LAKE, file_name, cfg.CREDENTIALS):
        return download_blob_to_memory(cfg.DATA_LAKE, file_name, cfg.CREDENTIALS)

    with cfg.SESSION.get(
        f'{cfg.REQUEST_URLS["MATCH-V5"]}/lol/match/v5/matches/{match_id}',
        headers={"X-Riot-Token": cfg.RIOT_API_KEY},
    ) as req:
        if req.status_code == 200:
            data = req.json()
            upload_blob_from_memory(
                cfg.DATA_LAKE,
                json.dumps(data, indent=4),
                file_name,
                cfg.CREDENTIALS,
            )

            return data

        print(f"Failed to do request ({req.status_code})")
        return {}


def match_transform(match: dict) -> list:
    retrieve_time = dt.datetime.utcnow()

    match_id = match["metadata"]["matchId"]

    # creation time
    creation_time = dt.datetime.fromtimestamp(match["info"]["gameCreation"] / 1000.0)
    game_start_time = dt.datetime.fromtimestamp(
        match["info"]["gameStartTimestamp"] / 1000.0
    )
    # game length
    duration_min = match["info"]["gameDuration"] / 60

    metadata_info = {
        "matchId": match_id,
        "gameCreation": creation_time,
        "gameStartTime": game_start_time,
        "gameDuration": duration_min,
        "retrieveTime": retrieve_time,
    }
    participants = []

    for participant in match["info"]["participants"]:
        challenges_info = {
            key: value
            for key, value in participant["challenges"].items()
            if key in cfg.CHALLENGES
        }

        participant_info = {
            key: value
            for key, value in participant.items()
            if key in cfg.PARTICIPANT_INFO
        }

        all_info = {**challenges_info, **participant_info, **metadata_info}

        participants.append(all_info)

    return participants
