import os

import requests
from prefect_gcp import GcpCredentials
from requests.adapters import Retry, HTTPAdapter

from prefect.blocks.system import Secret

SESSION = requests.Session()
retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[429])
SESSION.mount("https://", HTTPAdapter(max_retries=retries))

TABLE_ID = os.getenv("TABLE_ID", "datawarehouse")
DATA_LAKE = os.getenv("DATA_LAKE", "mlops-zoomcamp-project-data-lake-1234")

CREDENTIALS = GcpCredentials.load(
    "mlops-project-sa"
).get_credentials_from_service_account()

RIOT_API_KEY = Secret.load("riot-api-key").get()

REQUEST_URLS = {
    "LEAUGE-V4": "https://euw1.api.riotgames.com",
    "SUMMONER-V4": "https://euw1.api.riotgames.com",
    "MATCH-V5": "https://europe.api.riotgames.com",
}


CHALLENGES = [
    "kda",
    "killParticipation",
    "multikills",
    "turretPlatesTaken",
    "visionScoreAdvantageLaneOpponent",
    "visionScorePerMinute",
    "teamDamagePercentage",
    "controlWardsPlaced",
    "goldPerMinute",
]

PARTICIPANT_INFO = [
    "assistMePings",
    "dangerPings",
    "onMyWayPings",
    "deaths",
    "kills",
    "firstBloodAssist",
    "firstBloodKill",
    "largestKillingSpree",
    "pentaKills",
    "quadraKills",
    "tripleKills",
    "teamPosition",
    "totalDamageDealtToChampions",
    "totalDamageTaken",
    "totalHeal",
    "totalHealsOnTeammates",
    "totalTimeCCDealt",
    "visionScore",
    "wardsPlaced",
    "visionWardsBoughtInGame",
    "goldEarned",
    "championName",
    "win",
    "teamId",
]
