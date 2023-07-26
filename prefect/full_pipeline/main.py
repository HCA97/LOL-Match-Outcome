import datetime as dt
from typing import Optional

from prefect import flow
from prefect.flows import FlowRun
from prefect.deployments import run_deployment


@flow(name="Full-Pipeline", log_prints=True)
def main(start_time: Optional[dt.datetime] = None, max_players: int = 100):
    # download data
    data_flow: FlowRun = run_deployment(
        name="Main-Workflow/Collect-Matches-All-Tiers",
        parameters={"start_time": start_time, "max_players": max_players},
    )

    print(
        f"[Data Flow] Flow Status: {data_flow.state_name}"
        f" - Took: {data_flow.total_run_time.total_seconds()}s"
    )

    # train model
    ml_flow: FlowRun = run_deployment(
        name="Training-Pipeline/Training-Pipeline",
        parameters={"end_time": start_time, "start_time": None},
    )

    print(
        f"[ML Flow] Flow Status: {ml_flow.state_name} "
        f"- Took: {ml_flow.total_run_time.total_seconds()}s"
    )


if __name__ == "__main__":
    max_players = 1
    main(max_players=1)
