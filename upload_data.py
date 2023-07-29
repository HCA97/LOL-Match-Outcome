import argparse

import pandas as pd
from google.cloud import bigquery

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project_id', type=str, help="project id")
    args = parser.parse_args()

    project_id = args.project_id

    # pylint: disable=line-too-long
    url = "https://huggingface.co/datasets/hca97/LeaugeofLegendRankedMatches/resolve/main/2023-07-19_2023-07-29_euw.parquet"
    print(f'Downloading matches from {url}...')

    df = pd.read_parquet(url)

    print(f'Download is done it total there {len(df)/10} matches...')

    client = bigquery.Client(project=project_id)

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        time_partitioning=bigquery.table.TimePartitioning(
            type_="DAY", field="gameStartTime"
        ),
        clustering_fields=[
            "teamPosition",
            "division",
        ],
    )

    table_id = f"{project_id}.datawarehouse.matches"
    print(f'Uploading the matches to {table_id}...')
    job = client.load_table_from_dataframe(
        df, table_id, job_config=job_config
    )  # Make an API request
    job.result()  # Wait for job to finish
