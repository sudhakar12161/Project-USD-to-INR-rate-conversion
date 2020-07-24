# Project - USD-to-INR rate change notification

## Table of Content

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Code Setup](#code-setup)
- [ETL Process](#etl-process)
- [Data Result](#data-result)
- [Conclusion](#conclusion)

## Introduction
- **USD-to-INR rate change notification** is a easy way of  getting notified whenever there is a change in **USD to INR** rate conversion in [Compare Remit](https://www.compareremit.com/todays-best-dollar-to-rupee-exchange-rate/) website. 
- The code is written in **Python**, scheduled in **Apache Airflow** and stored data in **Postgres** database.

## Prerequisites

To run the application, you need to install following packages
- Python (3.6 or higher)
- Apache Airflow (1.10.10)
- PostgreSQL (12.2)

## Code Setup 
Import the following libraries

    from  bs4  import  BeautifulSoup  as  bs
    import  requests
    from  selenium  import  webdriver
    import  pandas  as  pd
    from  datetime  import  datetime,timedelta
    import  logging
    from  os  import  path
    import  os
    import  email_sender
    from  airflow  import  DAG
    from  airflow.operators.bash_operator  import  BashOperator
    from  airflow.operators.python_operator  import  PythonOperator
    from  airflow.operators.dummy_operator  import  DummyOperator
    from  airflow.models  import  Variable
    from  airflow.hooks.postgres_hook  import  PostgresHook

## ETL Process

## Data Result

## Conclusion
