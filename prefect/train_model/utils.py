from typing import List


import requests
from bs4 import BeautifulSoup


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


if __name__ == "__main__":
    print(get_existing_champs())
