# pylint: disable=import-outside-toplevel

import sys
import pathlib

import pandas as pd

sys.path.append('./pipelines/training_pipeline')


def test_add_champ_statistics():
    DIR = pathlib.Path(__file__).parent.resolve()

    matches = pd.read_csv(DIR / "data/training_pipeline/10_matches.csv")

    stats = pd.read_csv(DIR / "data/training_pipeline/champ_stats.csv.gz")

    from main import add_champ_statistics

    actual = add_champ_statistics.fn(matches, stats)
    expected = pd.read_csv(DIR / "data/training_pipeline/10_matches_resuts.csv")
    pd.testing.assert_frame_equal(expected, actual)
