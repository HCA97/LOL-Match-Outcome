from typing import Dict
from multiprocessing import Lock

import config as cfg
from flask import Flask, request
from model import MatchPredictor

app = Flask(__name__)

cached_models: Dict[str, MatchPredictor] = {}

lock = Lock()


@app.route("/predict", methods=["POST"])
def predict():
    data: dict = request.get_json()
    run_id = data.get("run_id", cfg.DEFAULT_RUN_ID)

    if run_id not in cached_models:
        with lock:  # to be thread safe
            try:
                if (
                    run_id not in cached_models
                ):  # so, they will not over-write each other
                    cached_models[run_id] = MatchPredictor(
                        run_id, cfg.WANDB_PATH, cfg.DATA_LAKE
                    )
            # pylint: disable=broad-except
            except Exception as e:
                print(f"Error: {e}")
                return {"error": "Failed to load the model"}, 500
    return cached_models[run_id].predict(data)


if __name__ == "__main__":
    app.run("0.0.0.0", 8080, True)
