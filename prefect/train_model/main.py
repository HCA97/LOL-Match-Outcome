import os
import itertools

import wandb
from prefect import flow

import src


@flow(name="Train-Classifier", log_prints=True)
def train_classifier(
    train_path: str, test_path: str, wandb_project: str, wandb_entity: str
) -> None:
    if wandb.login(key=os.getenv("WANDB_API_KEY")):
        wandb.init(project=wandb_project, entity=wandb_entity)

        run_id = train_path.split("/")[-2]

        train_data = src.load_data.submit(train_path)

        test_data = src.load_data.submit(test_path)

        num_columns = [
            f"{team}_team_{lane}_{feat}"
            for (lane, team, feat) in itertools.product(
                ["top", "jg", "mid", "bot", "sup"],
                ["blue", "red"],
                [
                    "champPickRate",
                    "winRate",
                    "normalizeKda",
                ],
            )
        ]
        cat_columns = ["tier"]

        X_train, y_train, enc = src.preprocess_data.submit(
            train_data,
            cat_columns=cat_columns,
            num_columns=num_columns,
            return_model=True,
        ).result()

        lp = src.log_preprocess.submit(enc, cat_columns, num_columns, run_id)

        X_test, y_test = src.preprocess_data.submit(
            test_data, cat_columns=cat_columns, num_columns=num_columns
        ).result()

        src.log_data(X_train, y_train, X_test, y_test, run_id)

        model = src.train_sgd.submit(X_train, y_train, X_test, y_test).result()

        lm = src.log_model.submit(model, run_id)

        src.log_feat_importance.submit(
            model, num_columns, ["silver", "gold", "platinum", "diamond"]
        )

        lrm = src.log_register_models.submit(
            wandb_project, wandb_entity, run_id, wait_for=[lp, lm]
        )

        # delete models, data and artifact folders
        src.clean_up.submit(wait_for=[lrm])
    else:
        raise RuntimeError("Failed to login to wandb.")


if __name__ == "__main__":
    test_path = "gs://mlops-zoomcamp-project-data-lake-1234/train_model/data/07-19-2023-07-24-2023/test.csv.gz"
    train_path = "gs://mlops-zoomcamp-project-data-lake-1234/train_model/data/07-19-2023-07-24-2023/train.csv.gz"
    wandb_project = "lol-match-predictor"
    wandb_entity = "hca97"
    train_classifier(train_path, test_path, wandb_project, wandb_entity)
