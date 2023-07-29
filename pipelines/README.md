# Prefect Pipelines

There are five pipelines:
* `Collect-Matches` - Collects solo queue matches for the given division and tier.
* `Collect-Matches-All-Tiers` - Collects solo queue matches for all the divisions and tiers (calls `Collect-Matches` multiple times).
* `Train-Model` - Trains the classifier to predict the winner.
* `Training-Pipeline` - Transforms and performs feature engineering on the data and then calls `Train-Model`.
* `Full-Workflow` - Runs the full pipeline (`Collect-Matches-All-Tiers` -> `Training-Pipeline`).

As you can see, some of the pipelines are derived from each other. The most important pipelines are `Collect-Matches`, `Train-Model`, and `Training-Pipeline`.

> ***Note***
> If you don't want to collect your own data and want to use the provided data, you can just use `Training-Pipeline`.

## Collect-Matches Workflow

![Alt text](../docs/collect_matches_dag.png?raw=true "Title")

## Train-Model Workflow

![Alt text](../docs/train_model_dag.png?raw=true "Title")

## Training-Pipeline Workflow

![Alt text](../docs/training_pipeline.png?raw=true "Title")
