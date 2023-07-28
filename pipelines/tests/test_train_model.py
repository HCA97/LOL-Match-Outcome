# pylint: disable=import-outside-toplevel
import sys
import json
import pathlib
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

sys.path.append('./pipelines/train_model')

DIR = pathlib.Path(__file__).parent.resolve()


def test_process_data():
    data = pd.read_csv(DIR / "data/training_pipeline/10_matches_resuts.csv")

    from src.data import preprocess_data
    from src.utils import load_pickle

    # default
    x_actual, y_actual = preprocess_data.fn(data)
    x_expected, y_expected = load_pickle(
        DIR / "data/train_model/10_matches_process_data.pkl"
    )
    np.testing.assert_array_almost_equal(x_expected, x_actual)
    np.testing.assert_almost_equal(y_expected, y_actual)


with open(DIR / "data/train_model/champs.html", 'r', encoding='utf-8') as ff:
    content = ff.read()


@patch(
    "requests.get",
    return_value=MagicMock(
        status_code=200,
        content=content,
    ),
)
def test_get_existing_champs(_):
    from src.utils import get_existing_champs

    actual = get_existing_champs()
    with open(DIR / "data/train_model/champs.json", 'r', encoding='utf-8') as ff:
        expected = json.load(ff)

    assert expected == actual
