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
  
- Make the [Less Secure apps]('https://support.google.com/accounts/answer/6010255') and [Enable IMAP]('https://support.google.com/mail/answer/7126229?hl=en') chnages to your gamil account to enable SMTP feature and to send emails through programatically and note down the 16 characters passwords.

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
  After creating variables, you will see the following screen in Airflow web UI.
  <img src='https://github.com/sudhakar12161/USD-to-INR/blob/master/pictures/airflow_variables.png' alt='Airflow Variable Web UI' />
  
- Copy all files from [dag]('https://github.com/sudhakar12161/USD-to-INR/tree/master/dag') folder into your dag folder located in Airflow Home directory.

- Restart Airflow services if you don't see new dags in Airflow web UI.

- After above steps you should see the **usdtoinr_dag** in your dag list.
<img src='https://github.com/sudhakar12161/USD-to-INR/blob/master/pictures/airflow_main_screen.png' alt='Airflow main web UI' />



## ETL Process

## Data Result

## Conclusion

