import numpy as np
from prefect import task
from sklearn.metrics import accuracy_score
from sklearn.linear_model import SGDClassifier

import wandb


@task(log_prints=True)
def train_sgd(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
):
    # wandb.init()
    config: dict = wandb.config
    print("WANDB Config", config)
    if not config:
        config = {
            "n_jobs": -1,
        }

    clf = SGDClassifier(**config).fit(x_train, y_train)

    y_pred_test = clf.predict(x_test)
    y_pred_train = clf.predict(x_train)

    test_acc = accuracy_score(y_test, y_pred_test)
    train_acc = accuracy_score(y_train, y_pred_train)
    print(f"Test Acc {test_acc} | Train Acc {train_acc}")

    wandb.log({"test_acc": test_acc, "train_acc": train_acc})

    wandb.sklearn.plot_confusion_matrix(y_test, y_pred_test, ["BLUE", "RED"])
    wandb.sklearn.plot_class_proportions(y_train, y_test, ["BLUE", "RED"])
    wandb.sklearn.plot_summary_metrics(clf, x_train, y_train, x_test, y_test)
    return clf
