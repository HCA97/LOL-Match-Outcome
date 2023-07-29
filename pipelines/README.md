# Prefect Pipelines

There are 5 pipelines:
* `Collect-Matches` - Collects soloque matches for given division and tier
* `Collect-Matches-All-Tiers` - Collect soloque matches for all the divisions and tiers (calls `Collect-Matches` multiple times)
* `Train-Model` - Train the classifier to predict the winner
* `Training-Pipeline` - Transform and do feature engineering on the data and then call `Train-Model`
* `Full-Workflow` - Running the full pipeline (`Collect-Matches-All-Tiers` -> `Training-Pipeline`)

As you can see some of the pipelines are derived from each other. The most important pipelines are `Collect-Matches`, `Train-Model` and `Training-Pipeline`.

If you don't want to collect your own data and want to use the provided data then you can just use `Training-Pipeline`.


## Collect-Matches Workflow

![Alt text](../docs/collect_matches_dag.png?raw=true "Title")

## Train-Model Workflow

![Alt text](../docs/train_model_dag.png?raw=true "Title")

## Training-Pipeline Workflow

![Alt text](../docs/training_pipeline.png?raw=true "Title")
