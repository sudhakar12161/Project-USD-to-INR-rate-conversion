from datetime import datetime
from airflow import DAG
from airflow.operators.bash_operator import BashOperator


create_command = """
/home/airflow/airflow/dags/usdtoinr.sh
"""

dag = DAG('usdtoinr_dag', 
    description='Scheduling usdtoinr python script through bash',
    start_date=datetime.now()
    ,schedule_interval='10 */2 * * *'
    ,catchup=False
)

usdtoinr= BashOperator(task_id='usdtoinr_task', 
    bash_command=create_command,
    dag=dag)