import datetime as dt
from typing import Optional

from prefect import flow
from prefect.deployments import run_deployment


@flow(name="Full-Pipeline", log_prints=True)
def main():
    # download data
    run_deployment(
        name="Main-Workflow/Collect-Matches-All-Tiers", parameters={"max_players": 1}
    )

    # train model
    run_deployment(name="Training-Pipeline/Training-Pipeline")


if __name__ == "__main__":
    main()
