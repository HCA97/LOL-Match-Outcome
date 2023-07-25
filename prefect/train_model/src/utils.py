from typing import List
import pickle
import shutil

import requests
from bs4 import BeautifulSoup
import wandb
from prefect import task


def get_existing_champs() -> List[str]:
    champs = []

    # the dragon data is 1.6GB, i only needed the champion names
    url = f"https://www.leagueoflegends.com/en-us/champions/"
    req = requests.get(url)
    if req.status_code == 200:
        soup = BeautifulSoup(req.content, "html.parser")

        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            if href.startswith("/en-us/champions/"):
                champ = href[len("/en-us/champions/") : -1].replace("-", "")
                champs.append(champ)

    print(f"In total {len(champs)} are retrieved.")
    return champs


def dump_pickle(obj, filename: str):
    with open(filename, "wb") as f_out:
        return pickle.dump(obj, f_out)


def load_pickle(filename: str):
    with open(filename, "rb") as f_in:
        return pickle.load(f_in)


@task(log_prints=True)
def clean_up():
    print("Finish Wandb...")
    wandb.finish()
    print("Clean Up...")
    shutil.rmtree("data", ignore_errors=True)
    shutil.rmtree("models", ignore_errors=True)
    shutil.rmtree("artifacts", ignore_errors=True)
    shutil.rmtree("wandb", ignore_errors=True)
