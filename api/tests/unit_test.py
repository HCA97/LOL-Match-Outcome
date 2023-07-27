# pylint: disable=import-outside-toplevel,protected-access
import sys
import threading as T
from unittest.mock import MagicMock, patch

# we mock pandas.read_csv so we need to use from
from pandas import read_csv

sys.path.append('./api')


@patch("model.MatchPredictor")
def test_caching(mock_predictor: MagicMock):
    from app import _predict

    data = {"run_id": "123"}
    t1 = T.Thread(target=_predict, args=(data,))
    t2 = T.Thread(target=_predict, args=(data,))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    assert mock_predictor.call_count == 1


def _csv(path: str):
    if path == "gs://dmy/train_model/data/07-19-2023-07-20-2023/champ_stats.csv.gz":
        return read_csv(
            "api/tests/artifacts/data/train_model_data_07-19-2023-07-20-2023_champ_stats.csv.gz"
        )
    return None


@patch(
    "model.download_model",
    side_effect=lambda run_id, wand_path: "api/tests/artifacts/model"
    if f'{wand_path}:{run_id}' == "test/path:07-19-2023-07-20-2023"
    else None,
)
@patch('pandas.read_csv', side_effect=_csv)
def test_match_predictor(_):
    from model import MatchPredictor

    clf = MatchPredictor("07-19-2023-07-20-2023", "test/path", "dmy")

    # test if feature retuns correct values
    kwargs = {
        "columns": ["normalizeVisionscore", "normalizeKills"],
        "team_id": "blue",
        "tier": "gold",
        "team": ["darius", "masteryi", "ahri", "ezreal", "soraka"],
    }
    actual = clf.features(**kwargs)
    expected = [
        [0.6487493534250265, 1.015343444004159],
        [0.7810664502721668, 1.394523590006252],
        [0.775975054151874, 1.0475598444758634],
        [0.6898663722153164, 1.0992038372118953],
        [2.073586783537367, 0.1464478594286921],
    ]

    assert expected == actual

    # test if both teams features merged correctly
    b_f = [[f"b-{i}-{j}" for i in range(2)] for j in range(2)]
    r_f = [[f"r-{i}-{j}" for i in range(2)] for j in range(2)]

    actual = clf._merge_teams_features(b_f, r_f)
    expected = ['b-0-0', 'r-0-0', 'b-1-0', 'r-1-0', 'b-0-1', 'r-0-1', 'b-1-1', 'r-1-1']
    assert expected == actual

    # test if column names extracted correctly
    c_c = ["b_team_jg", "b_team_TOP", "r_team_top_idk"]
    n_c = ["b_team_top_aa", "r_team_aa", "bb"]

    a1, a2 = clf._columns(c_c, n_c)
    e1, e2 = ['championName', "idk"], ["aa"]
    assert set(a1) == set(e1)
    assert set(a2) == set(e2)
