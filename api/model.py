import os
import pickle
from typing import List, Tuple, Union, Any
import numpy as np
import pandas as pd

import wandb

import config as cfg


def download_model(run_id: str, wand_path: str) -> str:
    success = wandb.login(key=cfg.WANDB_API_KEY)
    if not success:
        print('Failed to login to wandb')
        raise RuntimeError("Wrong credentials")

    run = wandb.init()
    artifact: wandb.Artifact = run.use_artifact(f"{wand_path}:{run_id}", type="model")
    return artifact.download()


class MatchPredictor:
    def __init__(self, run_id: str, wand_path: str, gcs_path: str):
        self.model = self._load_model(run_id, wand_path)
        self.champ_stats = self._load_champ_stats(run_id, gcs_path)
        self.run_id = run_id

    def _load_model(self, run_id: str, wand_path: str) -> tuple:
        artifact_dir = download_model(run_id, wand_path)
        model_path = os.path.join(artifact_dir, os.listdir(artifact_dir)[0])
        with open(model_path, "rb") as f:
            model = pickle.load(f)

        return model

    def _load_champ_stats(self, run_id: str, gcs_path: str) -> pd.DataFrame:
        return (
            pd.read_csv(f"gs://{gcs_path}/train_model/data/{run_id}/champ_stats.csv.gz")
            .apply(lambda x: x.astype(str).str.lower())
            .replace("monkeyking", "wukong")
        )

    def features(
        self, team_id: str, tier: str, team: List[str], columns: List[str]
    ) -> List[list]:
        def _float(r: str) -> Union[str, float]:
            try:
                return float(r)
            # pylint: disable=broad-except
            except Exception:
                return r

        champ_stats_team = self.champ_stats[
            (self.champ_stats.mapSide == team_id.lower())
            & (self.champ_stats.tier == tier.lower())
        ]

        feat = []

        for lane, champ in zip(["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"], team):
            res = champ_stats_team[
                (champ_stats_team.position == lane.lower())
                & (champ_stats_team.championName == champ.lower())
            ][columns].values.tolist()[0]

            res = [_float(r) for r in res]

            feat.append(res)

        return feat

    def _columns(
        self, cat_columns: List[str], num_columns: List[str]
    ) -> Tuple[List[str], List[str]]:
        num_champ_columns, cat_champ_columns = set(), set()

        for col in cat_columns:
            s = col.split("_")
            if len(s) > 1:
                if s[-1].lower() in ["top", "jg", "mid", "bot", "sup"]:
                    cat_champ_columns.add("championName")
                else:
                    cat_champ_columns.add(s[-1])

        for col in num_columns:
            s = col.split("_")
            if len(s) > 1:
                num_champ_columns.add(s[-1])
        return list(cat_champ_columns), list(num_champ_columns)

    def _merge_teams_features(
        self, blue_team_features: List[List[Any]], red_team_features: List[List[Any]]
    ) -> List[Any]:
        features = []
        for b_feats, r_feats in zip(blue_team_features, red_team_features):
            for bf, rf in zip(b_feats, r_feats):
                features.append(bf)
                features.append(rf)

        return features

    def predict(self, x: dict) -> Tuple[dict, int]:
        # pylint: disable=too-many-locals
        try:
            tier: str = x["tier"]
            blue_team: List[str] = x["blue_team"]
            red_team: List[str] = x["red_team"]
        except KeyError as e:
            return {"error": f"Keyerror: {e}"}, 400

        clf, enc, cat_columns, num_columns = self.model

        if len(blue_team) != 5 or len(red_team) != 5:
            # pylint: disable=line-too-long
            return {
                "error": "Blue and Red team must have 5 players in following order (top, jg, mid, bot, sup)"
            }, 400
            # pylint: enable=line-too-long

        # this logic should be in the model!

        cat_champ_columns, num_champ_columns = self._columns(cat_columns, num_columns)

        blue_team_features_num = self.features(
            "BLUE", tier, blue_team, num_champ_columns
        )
        blue_team_features_cat = self.features(
            "BLUE", tier, blue_team, cat_champ_columns
        )

        red_team_features_num = self.features("RED", tier, red_team, num_champ_columns)
        red_team_features_cat = self.features("RED", tier, red_team, cat_champ_columns)

        cat_features = [tier.lower()] + self._merge_teams_features(
            blue_team_features_cat, red_team_features_cat
        )
        x_cat = np.array([cat_features])

        num_features = self._merge_teams_features(
            blue_team_features_num, red_team_features_num
        )
        x_num = np.array([num_features])

        x_cat_onehot = enc.transform(x_cat)
        x = np.concatenate((x_cat_onehot, x_num), axis=1)

        p = clf.predict(x)[0]
        winner = "BLUE"
        if p > 0.5:
            winner = "RED"

        return {
            "winner": winner,
            "prob": p,
            "run_id": self.run_id,
        }, 200
        # pylint: enable=too-many-locals


if __name__ == "__main__":
    run_id = "07-14-2023-07-21-2023"
    wand_path = "hca97/model-registry/lol-match-predictor"
    gcs_path = "mlops-zoomcamp-project-data-lake-1234"
    model = MatchPredictor(run_id, wand_path, gcs_path)

    data = {
        "tier": "gold",
        "blue_team": ["fiora", "shaco", "ezreal", "twitch", "lulu"],
        "red_team": ["nasus", "masteryi", "ahri", "vayne", "braum"],
    }
    print(model.predict(data))
