from airflow import DAG
from datetime import datetime, timedelta
# from airflow.operators.python import PythonOperator
from airflow.operators.python_operator import PythonOperator
import boto3
from auth import aws_access_key_id,aws_secret_access_key
from datetime import datetime, timedelta
from airflow.hooks.S3_hook import S3Hook
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator



s3_bucket = 'my-random-bucket-001'
s3_key = "Organizations-file"
snowflake_conn_id = "snowflake_default"
snowflake_table = "organizations"
snowflake_schema = "my_schema"
file_format = "my_csv_format"

sql_cmd=f"""COPY INTO organizations (Index,Organization_Id,Name,Website,Country,Description,Founded,Industry,Number_of_employees)
FROM @my_s3_stage
FILE_FORMAT = (FORMAT_NAME = my_csv_format)
ON_ERROR=CONTINUE """

sql_transform=f""" 
CREATE OR REPLACE TABLE organizations_trans
  AS (SELECT Organization_Id,Name,Website,Country,Industry FROM organizations)"""


def upload_file():
    client=boto3.client("s3",aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
    client.upload_file('/opt/airflow/files/organizations-100.csv', 'my-random-bucket-001', 'Organizations-file')

    print("upload completed")


def download_from_s3():
    try:
        hook = S3Hook(aws_conn_id='aws_default')
        file_name = hook.download_file(key=s3_key, bucket_name=s3_bucket)
        return file_name
    except Exception as e:
        # Handle the exception (log, raise, etc.)
        raise

default_args = {
    'owner': 'sarthak',
    'depends_on_past': False,
    'start_date': datetime(2023, 12, 10),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(seconds=10),
}

with DAG(
    dag_id='pipeline',
    schedule_interval='@daily',
    start_date=datetime(2023, 12, 11),
    catchup=False,
    default_args=default_args
) as dag:
    
    task1 = PythonOperator(
        task_id ="s3_file_upload",
        python_callable = upload_file
    )

    task2 = PythonOperator(
        task_id='download_from_s3',
        python_callable=download_from_s3
    )

    snow_task1=SnowflakeOperator(
            task_id="copy_into_snow_table",
            snowflake_conn_id=snowflake_conn_id,
            sql=sql_cmd
            
        )
    
    snow_task2=SnowflakeOperator(
        task_id="data_transformation",
        snowflake_conn_id=snowflake_conn_id,
        sql=sql_transform
    )
    task1>>task2 >> snow_task1>>snow_task2
