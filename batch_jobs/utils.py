from typing import List, Union

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup


# class MapCategoricalData(BaseEstimator, TransformerMixin):
#     def __init__(self, champ_colums):
#         self.champs = {
#             champ: i for i, champ in enumerate(MapCategoricalData.get_existing_champs())
#         }
#         self.champs_columns =

#         self.tiers = {
#             tier: i for i, tier in enumerate(["SILVER", "GOLD", "PLATINUM", "DIAMOND"])
#         }

#     def fit(self, *args, **kwargs):
#         return self

#     def transform(
#         self,
#         X: Union[list, np.ndarray, pd.DataFrame],
#         y: Union[list, np.ndarray, pd.DataFrame],
#     ) -> np.ndarray:
#         vec = None

#         try:
#             if isinstance(champ, str):
#                 vec = np.zeros(len(self.champs))
#                 vec[self.champs[champ]] = 1
#             elif isinstance(champ, (list, np.ndarray, pd.Series)):
#                 vec = np.zeros((len(champ), len(self.champs)))
#                 for c in champ:
#                     vec[self.champs[str(c)]] = 1
#         except KeyError:
#             print(
#                 f"{champ} is not exists in champs, existing champs are {list(self.champs.keys())}"
#             )

#         return vec


#     @staticmethod
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
    # import pickle

    # m = MapChamps()
    # print(m.transform("ahri"))
    # with open("test.pkl", "wb") as f:
    #     pickle.dump(m, f)

    # with open("test.pkl", "rb") as f:
    #     y = pickle.load(f)
    print(get_existing_champs())
# print(MapChamps.get_existing_champs())
