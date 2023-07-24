import os


PROJECT_ID = os.getenv("PROJECT_ID", "mlops-project-391611")
DATASET_ID = os.getenv("TABLE_ID", "datawarehouse")
DATA_LAKE = os.getenv("DATA_LAKE", "mlops-zoomcamp-project-data-lake-1234")
GCP_CRED_BLOCK = os.getenv("GCP_CRED_BLOCK", "mlops-project-sa")
