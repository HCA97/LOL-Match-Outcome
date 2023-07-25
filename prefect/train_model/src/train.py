import numpy as np

import wandb

from sklearn.linear_model import SGDClassifier

from sklearn.metrics import accuracy_score

from prefect import task


@task(log_prints=True)
def train_sgd(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
):
    # wandb.init()
    config: dict = wandb.config
    print("WANDB Config", config)
    if not config:
        config = {
            "n_jobs": -1,
        }

    clf = SGDClassifier(**config).fit(X_train, y_train)

    y_pred_test = clf.predict(X_test)
    y_pred_train = clf.predict(X_train)

    test_acc = accuracy_score(y_test, y_pred_test)
    train_acc = accuracy_score(y_train, y_pred_train)
    print(f"Test Acc {test_acc} | Train Acc {train_acc}")

    wandb.log({"test_acc": test_acc, "train_acc": train_acc})

    wandb.sklearn.plot_confusion_matrix(y_test, y_pred_test, ["BLUE", "RED"])
    wandb.sklearn.plot_class_proportions(y_train, y_test, ["BLUE", "RED"])
    wandb.sklearn.plot_summary_metrics(clf, X_train, y_train, X_test, y_test)
    return clf
