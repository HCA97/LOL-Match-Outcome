from typing import Dict, Tuple
from multiprocessing import Lock

import flask as F
import model as m
import config as cfg

app = F.Flask(__name__)

cached_models: Dict[str, m.MatchPredictor] = {}

lock = Lock()


def _predict(data: dict) -> Tuple[dict, int]:
    run_id = data.get("run_id", cfg.DEFAULT_RUN_ID)

    if run_id not in cached_models:
        with lock:  # to be thread safe
            try:
                print(
                    f'Locking because we dont have {run_id},'
                    f'existing models [{list(cached_models.keys())}]'
                )
                if (
                    run_id not in cached_models
                ):  # so, they will not over-write each other
                    cached_models[run_id] = m.MatchPredictor(
                        run_id, cfg.WANDB_PATH, cfg.DATA_LAKE
                    )
            # pylint: disable=broad-except
            except Exception as e:
                print(f"Error: {e}")
                return {"error": "Failed to load the model"}, 500
    return cached_models[run_id].predict(data)


@app.route("/predict", methods=["POST"])
def predict():
    return _predict(F.request.get_json())


if __name__ == "__main__":
    app.run("0.0.0.0", 8080, True)
