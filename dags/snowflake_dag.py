
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from auth import aws_access_key_id,aws_secret_access_key

snowflake_conn_id = "snowflake_2"
snowflake_table1 = "webpage"
snowflake_table2 = "webpage_sales"
snowflake_schema = "demo_schema"
file_format = "my_csv_format"

create_table=f'''
create or replace table webpage(
webpage_sk int,
webpage_id varchar(20),
url varchar(100),
ad_count int);
create or replace table webpage_sales(
webpage_sk int,
orderno int,
qty int,
net_profit number(10,2)
);
'''

data_load_1='''
insert into DEMO_DB2.DEMO_SCHEMA.webpage(webpage_sk,webpage_id,url,ad_count)
select WP_WEB_PAGE_SK,WP_WEB_PAGE_ID,WP_URL,WP_MAX_AD_COUNT from SNOWFLAKE_SAMPLE_DATA.TPCDS_SF100TCL.WEB_PAGE
limit 500;
'''

data_load_2='''
insert into DEMO_DB2.DEMO_SCHEMA.webpage_sales(webpage_sk,orderno,qty,net_profit)
select WS_WEB_PAGE_SK,WS_ORDER_NUMBER,WS_QUANTITY,WS_NET_PROFIT from SNOWFLAKE_SAMPLE_DATA.TPCDS_SF100TCL.WEB_SALES
limit 50000;
'''

joined_table='''
create or replace table webpage_total as
select wp.webpage_sk,wp.webpage_id,wp.url,wp.ad_count,wps.orderno,wps.qty,wps.net_profit from webpage wp
left join webpage_sales wps
on wp.webpage_sk=wps.webpage_sk;
'''

default_args = {
    'owner': 'sarthak',
    'depends_on_past': False,
    'start_date': datetime(2023, 12, 14),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(seconds=10),
}

dag=DAG(
    dag_id='snow_pipeline',
    schedule_interval='@daily',
    start_date=datetime(2023, 12, 11),
    catchup=False,
    default_args=default_args) 

task1=SnowflakeOperator(
    task_id="creating_tables",
    snowflake_conn_id=snowflake_conn_id,
    sql=create_table,
    dag=dag
)

task2=SnowflakeOperator(
    task_id="data_loading_table1",
    snowflake_conn_id=snowflake_conn_id,
    sql=data_load_1,
    dag=dag
)
    
task3=SnowflakeOperator(
    task_id="data_loading_table2",
    snowflake_conn_id=snowflake_conn_id,
    sql=data_load_2,
    dag=dag
)

task4=SnowflakeOperator(
    task_id="joined_table",
    snowflake_conn_id=snowflake_conn_id,
    sql=joined_table,
    dag=dag
)

task1>>[task2,task3]>>task4