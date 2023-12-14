import requests
import json,csv,pprint
import boto3
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from auth import aws_access_key_id,aws_secret_access_key


def rest_api_call():

    url = "https://coinranking1.p.rapidapi.com/coins"

    querystring = {"referenceCurrencyUuid":"yhjMzLPhuIDl","timePeriod":"24h","tiers[0]":"1","orderBy":"marketCap","orderDirection":"desc","limit":"700","offset":"0"}

    headers = {
        "X-RapidAPI-Key": "cd8cd7d41emsh4ba0432bad96d8dp186666jsn22cf5af893bf",
        "X-RapidAPI-Host": "coinranking1.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)

    with open("/opt/airflow/files/test.json",'w') as json_file:
        json.dump(response.json()["data"]["coins"],json_file)
        print("json file created")

    return 0


def json_to_csv():
    csv_file_path="//opt/airflow/files/test.csv"
    json_file_path="/opt/airflow/files/test.json"

    with open(csv_file_path,'w') as data_file:
            with open(json_file_path,'r') as json_data_file:
                json_data=json.load(json_data_file)
            
            csv_writer=csv.writer(data_file)
            csv_writer.writerow(json_data[0].keys())

            for data in json_data:
                csv_writer.writerow(data.values())
    return 0


def upload_file_csv():
    client=boto3.client("s3",aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
    client.upload_file('/opt/airflow/files/test.csv', 'my-random-bucket-002', 'coin-price-csv')
    print("csv upload completed")


def upload_file_json():
    client=boto3.client("s3",aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
    client.upload_file('/opt/airflow/files/test.json', 'my-random-bucket-002','coin-price-json')
    print("json upload completed")


create_stage_csv=f'''
CREATE OR REPLACE STAGE csv_s3_stage
URL='s3://my-random-bucket-002/coin-price-csv'
CREDENTIALS=(AWS_KEY_ID='AKIA4SXCAFHSOCMPU7LX' AWS_SECRET_KEY='DYlOTEHyogLcr0JylaJV8RdHRhCbUw9GFRzT/aEO')
DIRECTORY = (ENABLE = TRUE)
FILE_FORMAT = my_csv_format;'''


create_stage_json=f'''
CREATE OR REPLACE STAGE json_s3_stage
URL='s3://my-random-bucket-002/coin-price-json'
CREDENTIALS=(AWS_KEY_ID='AKIA4SXCAFHSOCMPU7LX' AWS_SECRET_KEY='DYlOTEHyogLcr0JylaJV8RdHRhCbUw9GFRzT/aEO')
DIRECTORY = (ENABLE = TRUE)
FILE_FORMAT = my_json_format;'''

copy_csv_data=f"""COPY INTO coin_price_csv (uuid,symbol,name ,color ,iconUrl ,marketCap,price ,
listedAt ,tier ,change ,ranking ,sparkline,lowVolume ,coinrankingUrl ,dayVolume ,btcPrice )
FROM @csv_s3_stage
FILE_FORMAT = (FORMAT_NAME = my_csv_format)
ON_ERROR=CONTINUE """


copy_json_data_variant=f"""COPY INTO coin_price_json_variant
FROM @json_s3_stage
FILE_FORMAT = (FORMAT_NAME = my_json_format)
ON_ERROR=CONTINUE """

variant_to_table=f'''
insert into coin_price_json(uuid,symbol,name ,color ,iconUrl ,marketCap,price ,
listedAt ,tier ,change ,ranking ,sparkline,lowVolume ,coinrankingUrl ,dayVolume ,btcPrice )
select my_variant_column:uuid,my_variant_column:symbol,my_variant_column:name ,my_variant_column:color ,my_variant_column:iconUrl ,my_variant_column:marketCap,my_variant_column:price ,
my_variant_column:listedAt ,my_variant_column:tier ,my_variant_column:change ,my_variant_column:ranking ,my_variant_column:sparkline,my_variant_column:lowVolume ,my_variant_column:coinrankingUrl ,my_variant_column:dayVolume ,my_variant_column:btcPrice 
from coin_price_json_variant;
'''


s3_bucket = 'my-random-bucket-002'
s3_key = "Organizations-file"
snowflake_conn_id = "snowflake_default"
snowflake_table1 = "coin_price_csv"
snowflake_table2 = "coin_price_json"
snowflake_schema = "my_schema"
file_format = "my_csv_format"


default_args = {
    'owner': 'sarthak',
    'depends_on_past': False,
    'start_date': datetime(2023, 12, 13),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(seconds=10),
}
    


with DAG(
    dag_id='restapi-pipeline',
    schedule_interval='@daily',
    start_date=datetime(2023, 12, 11),
    catchup=False,
    default_args=default_args
) as dag:
    
    py_task1=PythonOperator(
        task_id="restapi_call_json_data",
        python_callable=rest_api_call
    )
    
    py_task2=PythonOperator(
        task_id="create_csv",
        python_callable=json_to_csv
    )

    py_task3 = PythonOperator(
        task_id ="csv_file_upload_s3",
        python_callable = upload_file_csv
    )

    py_task4= PythonOperator(
        task_id="json_file_upload_s3",
        python_callable=upload_file_json
    )

    snow_task1=SnowflakeOperator(
            task_id="create_csv_external_stage",
            snowflake_conn_id=snowflake_conn_id,
            sql=create_stage_csv
        )
    
    snow_task2=SnowflakeOperator(
            task_id="create_json_external_stage",
            snowflake_conn_id=snowflake_conn_id,
            sql=create_stage_json
        )
    
    snow_task3=SnowflakeOperator(
        task_id="copy_into_csv_table",
        snowflake_conn_id=snowflake_conn_id,
        sql=copy_csv_data
    )

    snow_task4=SnowflakeOperator(
        task_id="copy_into_json_table_variant",
        snowflake_conn_id=snowflake_conn_id,
        sql=copy_json_data_variant
    )

    snow_task5=SnowflakeOperator(
        task_id="variant_table_to_multicolumn",
        snowflake_conn_id=snowflake_conn_id,
        sql=variant_to_table
    )
    

    py_task1>>py_task2>>py_task3>>snow_task1>>snow_task3
    py_task1>>py_task4>>snow_task2>>snow_task4>>snow_task5


#before copying the data from the external stage to the mtable ensure to create the required tables in snowflake db.