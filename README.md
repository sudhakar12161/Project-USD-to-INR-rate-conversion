# Project - USD-to-INR rate change notification

## Table of Content

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Code Setup](#code-setup)
- [ETL Process](#etl-process)
- [Data Result](#data-result)
- [Conclusion](#conclusion)

![](https://img.shields.io/badge/python-3.5%20%7C%203.6%20%7C%203.7-blue) ![](https://img.shields.io/badge/Airflow-1.10.10-brightgreen) ![](https://img.shields.io/badge/Postgres-10%20%7C%2011%20%7C%2012-orange) ![](https://img.shields.io/badge/license-BSD-green)
## Introduction
-  **USD-to-INR rate change notification** is a easy way of  getting notified whenever there is a change in **USD to INR** rate conversion in [Compare Remit](https://www.compareremit.com/todays-best-dollar-to-rupee-exchange-rate/) website.
- The code is written in **Python**, scheduled in **Apache Airflow** and stored data in **Postgres** database.

## Prerequisites

To run the application, you need to install following packages:
- Python (3.5 or higher)
- Pip (latest version)
- Apache Airflow (1.10.10)
- PostgreSQL (10 or higher)
- Google Chrome driver



## Code Setup
Follow the below steps to setup **USD-to-INR rate change notification** application.
- <a href ='https://medium.com/@taufiq_ibrahim/apache-airflow-installation-on-ubuntu-ddc087482c14' > Steps</a> to install Python, Pip, Postgres and Airflow packages.
- After completeing the previous step, install the following packages through pip.
  ```
  requests #to make web page requests
  bs4 #BeautifulSoup
  selenium # to read dynamic webpage
  pandas
  ```
- Make the [Less Secure Apps](https://support.google.com/accounts/answer/6010255) and [Enable IMAP](https://support.google.com/mail/answer/7126229?hl=en) changes to your gmail account to enable SMTP feature and to send emails through programatically and note down the 16 characters passwords.

- Update the following code in **airflow.cfg** file located in Airflow Home directory.
  ```
  executor = LocalExecutor
  sql_alchemy_conn = postgresql+psycopg2://airflow:a1rflow@localhost:5432/airflow

  [smtp]
  #If you want airflow to send emails on retries, failure, and you want to use
  # the airflow.utils.email.send_email_smtp function, you have to configure an
  # smtp server here
  smtp_host = smtp.gmail.com
  #localhost
  smtp_starttls = False
  smtp_ssl = True
  # Example: smtp_user = airflow
  smtp_user = your@gmail.com
  # Example: smtp_password = airflow
  smtp_password = 16 character gmail password
  smtp_port = 465
  smtp_mail_from = your@gmail.com

  broker_url = sqla+mysql://airflow:airflow@localhost:3306/airflow
  result_backend = db+mysql://airflow:airflow@localhost:3306/airflow
  ```
- Run the following commands to start the Airflow services.
  ```
  airflow initdb
  airflow webserver
  airflow scheduler
  ```
- Create the following variables in airflow web UI.
  ```
  Key : Value
  airflow_chromedriver_path : /usr/bin/chromedriver
  airflow_failure_notification_list : ['update with email address']
  airflow_owner : airflow
  airflow_usd_to_inr_bcc_list : ['email 1', 'email 2']
  airflow_web_addr : https://www.compareremit.com/todays-best-dollar-to-rupee-exchange-rate/
  ```
- After creating variables, you will see the following screen in Airflow web UI.
  
  <img src='https://github.com/sudhakar12161/Project-USD-to-INR-rate-conversion/blob/master/pictures/airflow_variables.png' alt='Airflow Variable Web UI' />

- Connect to Postgres database and run the following statements.
  ```
  sudo -u postgres psql #to connect to postgres database
  
  CREATE USER usdtoinr PASSWORD 'usdtoinr';
  CREATE DATABASE rate_conversion;
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO usdtoinr;

  #disconnect from the postgres database and connect with usdtoinr user.

  psql -d rate_conversion -U usdtoinr 

  CREATE TABLE compare_rate_usd_to_inr (
	  Date_id TIMESTAMP NOT NULL, 
	  Agent_Name VARCHAR(50) NOT NULL, 
	  New_User_Rate FLOAT, 
	  Regular_Rate FLOAT, 
	  Transfer_Fee_Rate FLOAT, 
	  CONSTRAINT Compare_Rate_USD_to_INR_PK PRIMARY KEY (Date_Id, Agent_Name)
  );
  ```
- Next Create the **Postgres** connection in Airflow as shown below.

  <img src='https://github.com/sudhakar12161/Project-USD-to-INR-rate-conversion/blob/master/pictures/airflow_postgres_conn.png' alt='Airflow Variable Web UI' />

- Copy all files from [dag](https://github.com/sudhakar12161/Project-USD-to-INR-rate-conversion/tree/master/dag) folder into your dag folder located in Airflow Home directory.

- Restart Airflow services if you don't see new dags in Airflow web UI.

- After above steps you should see the **usdtoinr_dag** in your dag list.
<img src='https://github.com/sudhakar12161/Project-USD-to-INR-rate-conversion/blob/master/pictures/airflow_main_screen.png' alt='Airflow main web UI' />



## ETL Process
The ETL process is divided into tasks in a dag in Airflow. There are 4 PythonOperator tasks and 2 DummyOperators tasks as shown below.

<img src='https://github.com/sudhakar12161/Project-USD-to-INR-rate-conversion/blob/master/pictures/airflow_dag.png' alt='Airflow dag screen' />

#### ETL Steps:

- DummyOperator: The Start_Task and End_Task are just to show the process begin and end positions and there is no logic in these tasks.

- PythonOperator:
  - Read_Webpage:
    - This task reads a dynamic web-page using **Selenium** and **Chrome Driver** libraries and returns a HTML page. 
    - The HTML page will be stored in a **Airflow Variable** to pass to the next section.
  - Extract_USD_to_INR_Data:
    - This task reads web-page using **BeautifulSoup** library from a variable.
    - Extracts the elements/data from a web-page that we are interested in.
    - Adding all the extracted elements to a list and store that list in a variable to pass into the next task.
  - Load_USD_to_INR_Data:
    - In this task we will read the list from a variable returned by the previous task and convert it into a **Pandas** DataFrame.
    - We will connect to the database and get the prior agents rate information and store it in a DataFrame.
    - After that, we will perform transformations on data sets and compare both the DataFrames.
    - Load data into **Postgres** database using **Postgres hook** only if there a difference in the rate.
    - Convert the DataFrame which has modified rate information into HTML format and store it in a variable to pass it to the next task. 
  - Send_Email:
    - Email task uses **email_sender.py** user defined module which uses **smtplib** and **email** libraries to send emails.
    - Email task triggeres and sends email notification whenever there is a change in the rate.

#### ETL Recovery and Notification:
- As we defined in the **DAG** default arguments in the code, the process will re-run for one time if the process failed for unknown reason. 
- If it fails second time, it will send email notification (need to setup **SMTP** section in airflow.cfg file) and fail the task.
- Below is a sample email notification when the task fails.


## Data Result

## Conclusion

