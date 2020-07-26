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
Follow the below steps to setup **USD-to-INR rate change notification** application
- <a href ='https://medium.com/@taufiq_ibrahim/apache-airflow-installation-on-ubuntu-ddc087482c14'> Steps </a>to install Python, Pip, Postgres and Airflow packages.
- After completeing the previous step, install the following packages through pip.
  ```
  requests #to make web page requests
  bs4 #BeautifulSoup
  selenium # to read dynamic webpage
  pandas
  
  ```
- Make the [Less Secure apps]('https://support.google.com/accounts/answer/6010255') and [Enable IMAP]('https://support.google.com/mail/answer/7126229?hl=en') chnages to your gamil account to enable SMTP feature and to send emails through programatically.

- Copy all files from [dag]('https://github.com/sudhakar12161/USD-to-INR/tree/master/dag') folder into your dag folder located in Airflow Home directory.
- Restart Airflow services if you don't see new dags in Airflow web UI.



## ETL Process

## Data Result

## Conclusion


