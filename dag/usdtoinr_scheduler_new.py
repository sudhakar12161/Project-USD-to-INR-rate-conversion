from bs4 import BeautifulSoup as bs
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from datetime import datetime, timedelta
import time
import logging
from os import path
import os
import email_sender
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.models import Variable
from airflow.hooks.postgres_hook import PostgresHook


#gets the todays datetime in str format
today = str(datetime.now().replace(microsecond=0)).replace(' ','_').replace(':','_')

def read_webpage(**kwargs):
    '''
    This method reads a dynamic webpage and stores it in a variable dictionary.
    param:
    **kwargs
    '''
    try:
        #location of the browser driver
        path = Variable.get('airflow_chromedriver_path')
        logging.info('Web driver located at:  {0}'.format(path))
        options = webdriver.ChromeOptions()
        #adding options to the webdriver
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--incognito")
        options.add_argument("--headless")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("test-type")
        options.add_argument("--disable-notifications")
        logging.info('Added web driver options to Chrome driver')
        #creating driver obj with options
        driver = webdriver.Chrome(path,options=options)
        logging.info('Created driver object for Chrome WebDriver')
        #making request to the webpage
        driver.get(Variable.get('airflow_web_addr'))
        logging.info('Request sent to web page {path}'.format(path=Variable.get('airflow_web_addr')))
        #lopping the webpage until it loads the required elements
        #if the page loaded SEND NOW link text in the page then it returns the length of 8 and that means it loaded all the required elements
        page_load_len=0
        try:
            while page_load_len == 0 or page_load_len is None:
                page_load_ind = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.LINK_TEXT, "SEND NOW")))
                page_load_len = len(page_load_ind.text)
                logging.info('page_load_length: {}'.format(page_load_len))
        except BaseException as e:
            logging.error('Webpage reading failed with error: {}'.format(e))
            raise e
        
        #assigning the HTML code to a variable
        src = driver.page_source
        logging.info('Reading webpage completed.')
        #closing the wep page
        driver.quit()
        #creating a dictionary
        usdtoinr = {'src': src}
        #saving it in usdtoinr variable
        Variable.set('usdtoinr',value=usdtoinr)
        logging.info('usdtoinr variable created')
    except BaseException  as e:
        logging.error('read_webpage method failed: , {0}'.format(e))
        raise ValueError('Web driver issue')
 
def extract_usdtoinr_data(**kwargs):
    '''
    This method reads HTML page and extracts the agent information
    params:
    kwargs
    '''
    try:
        #reading the webpage from a variable was returned by the previous task
        src_dict = eval(Variable.get('usdtoinr'))
        src = src_dict['src']
        #converting it into HTML format using bs4 library
        if src is not None:
            soup = bs(src,'lxml')
            logging.info('Converted the response into HTML format')
        else:
            logging.error('Returned empty webpage')
            raise ValueError('Returned empty webpage')
        #creating empty list to store the final agent info
        output = []
        logging.info('Created empty output list')
        #assign top level div info to a variable
        today_rates = soup.find_all('div',class_='table-1 best-row active')
        logging.info('Assigned the main division from HTML to today_rates')
        #reading one by one agent info
        logging.info('Processing each Agent info')
        logging.info('Creating row_output variable to process each Agent info')
        for agents in today_rates:
            #creating list to hold row by row data
            row_output = []
            #print(agents,end='\n\n')
            #extracting the name of the agent
            agent_logo = agents.find('div',class_='text-center').img['alt']
            agent_logo = agent_logo.replace('Logo','').rstrip()
            #print(agent_logo)
            #getting agent info one by one
            agent_info = agents.find('div',class_="row table-row")
            #print(agent_info,end='\n\n')
            #extracting the rate headers
            agent_lbl_info =  agent_info.find_all('div', class_='small-gray-text rate lbl')
            #print(agent_lbl_info,end='\n\n')
            #extracting the rate amount
            agent_rate_info =  agent_info.find_all('div', class_="text-2 rate amt")
            #print(agent_rate_info,end='\n\n')
            #extracting trasfer charges
            agent_charge_info =  agent_info.find_all('div', class_="rate amt")
            #print(agent_charge_info,end='\n\n')
            #rate into and charges info appending to list and passing along with rate types to dictionary
            agent_rate_list = list(agent_rate_info)
            agent_rate_list.extend(agent_charge_info)
            #print(agent_rate_list)
            dict_agent_info = dict(zip(agent_lbl_info,agent_rate_list))
            #print(dict_agent_info,end='\n\n')
        
            #adding agent name to the logo
            row_output.append(agent_logo)
            #iterating the dictionary and checking it has 2 rates or not
            for lbl_info,rate_info in dict_agent_info.items():
                #if they only only one offer for all the customers then ==2
                #re naming the columns names
                if len(agent_lbl_info) ==2:
                    lbl_name = lbl_info.text.lstrip().rstrip()
                    rate_amt = float(rate_info.text[2:].lstrip().rstrip())
                    if lbl_name == 'Rate':
                        lbl_name = 'Regular Rate'
                        extra_lbl_name = 'First Time User Rate or more than 2000'
                        row_output.append(extra_lbl_name)
                        row_output.append(rate_amt)
                    row_output.append(lbl_name)
                    row_output.append(rate_amt)
                #if it has 2nd offer for customer we will process that here
                else:
                    lbl_name = lbl_info.text.lstrip().rstrip()
                    if lbl_name.find('Less') == 0:
                        lbl_name = 'Regular Rate'
                    if lbl_name == 'First Time User Rate' or lbl_name.find('More') == 0 :
                        lbl_name = 'First Time User Rate or more than 2000'
                    rate_amt = float(rate_info.text[2:].lstrip().rstrip())
                    row_output.append(lbl_name)
                    row_output.append(rate_amt)
                    #print(lbl_name,end='\n')
                    #print(rate_amt,end='\n')
            #appending the record to output list
            #appending each agent info to output list
            output.append(row_output)
        logging.info('web scraping completed and saved output in a list')
        #adding the list to a dictionary
        src_dict['list_data'] = output
        #updating the usdtoinr variable with value
        Variable.set('usdtoinr',value = src_dict)
           
    except BaseException  as e:
        logging.error('Issue with the webpage returned by Chrome driver: {0}'.format(e))
        raise Exception('Issue with the webpage returned by Chrome driver: {0}'.format(e))
       

def load_usdtoinr_data(**kwargs):
    '''
    This method reads a list and process the list into a dataframe and compare with prior data from database.
    And inserts into database table if there is a change.
    '''
    try:
        #reading the output from previous task through a variable
        src_output = eval(Variable.get('usdtoinr'))
        output = src_output['list_data']
        #logging.info(output)
        logging.info('Below is the output from Extract Data task')
        if len(output)>=1 and type(output) is list:
            for row in output:
                logging.info(row)
            
            #creating postgres hooker
            postgres= PostgresHook(postgres_conn_id='postgres_rate_conversion')
            #creating engine to insert data from a dataframe into table
            postgres_engine = postgres.get_sqlalchemy_engine()
            #creating conn to read data from a table into DataFrame
            postgres_conn = postgres.get_conn()
            #reading old data from table
            old_record = pd.read_sql('''SELECT * FROM compare_rate_usd_to_inr 
                                        WHERE "Date_Id" = (SELECT max("Date_Id") FROM compare_rate_usd_to_inr)''',
                                     postgres_conn, parse_dates={'Date_Id'})
            #Removing date_id column
            old_record = old_record.iloc[:,1:]
            #Sorting the old data by agent name to compare
            old_record = old_record.sort_values(by='Agent_Name').reset_index(drop=True)
            
            #converting list to dataframe and adding columns
            raw_agent_data = pd.DataFrame(output,columns=['Agent_Name','New_User','New_User_Rate','Regular_User','Regular_Rate','Transfer_Fee','Transfer_Fee_Rate'])
            logging.info('Converted into DataFrame and added columns')
            #droping the header names from rows
            raw_agent_data=raw_agent_data.drop(['New_User','Regular_User','Transfer_Fee'],axis=1).sort_values(by='Agent_Name').reset_index(drop=True)
            logging.info('Dropped desc fileds')
            #dropping XE Money Transfer agent from the data frame as it is not consistent
            raw_agent_data = raw_agent_data.query('Agent_Name != "XE Money Transfer"').reset_index(drop=True)
            #the below line is for testing purpose
            #raw_agent_data.loc[raw_agent_data['Agent_Name']=='Xoom','New_User_Rate']=74.40
            #imp_agent_names are the one i am interested in
            imp_agent_names =['RIA Money Transfer','Remitly','Western Union','Xoom']
            #creating not matching recrods by comparaing old data and current data
            not_matching_records = pd.DataFrame(columns=raw_agent_data.columns)
            not_matching_records['New_User_Rate_Difference'] = None
            not_matching_records['New_User_Rate_Difference_desc'] = None
            not_matching_records['Regular_Rate_Difference'] = None
            #comparing the no of agents with prior data
            row_matching_ind = True if len(raw_agent_data) == len(old_record) else False
            #logging.info(raw_agent_data)
            #logging.info(old_record)
            #cnt is helpfull to notedown the index in the loop
            cnt = 0
            logging.info('Assigned header row to the not_matching_records DataFrame')
            for i in range(len(raw_agent_data)):
                #logging.info(row_matching_ind)
                #comparing the dataframes
                if  row_matching_ind and not (old_record.iloc[i].equals(raw_agent_data.iloc[i])):
                    not_matching_records = not_matching_records.append(raw_agent_data.iloc[i],ignore_index=True)
                    not_matching_records.loc[cnt,'New_User_Rate_Difference']=raw_agent_data.loc[i,'New_User_Rate']-old_record.loc[i,'New_User_Rate']
                    not_matching_records.loc[cnt,'New_User_Rate_Difference_desc']='Increased' if not_matching_records.loc[cnt,'New_User_Rate_Difference']>0 else 'Decreased'
                    not_matching_records.loc[cnt,'Regular_Rate_Difference']=raw_agent_data.loc[i,'Regular_Rate']-old_record.loc[i,'Regular_Rate']
                    cnt = cnt+1
            logging.info('Proccessed not matching records and added the difference')
            #appending/inserting the data to table
            #adding Data_id column
            raw_agent_data.insert(0,'Date_Id', datetime.now().replace(microsecond=0))
            #inserting data into database table if the conditions met
            if not (row_matching_ind) or len(not_matching_records)>0:
                raw_agent_data.to_sql('compare_rate_usd_to_inr',postgres_engine,index=False,if_exists='append')
                logging.info('Data has been inserted into the databse')
            else:
                logging.info('0 records inserted into database')
            #keeping only prefeered agents
            not_matching_records = not_matching_records.query('Agent_Name in @imp_agent_names')
            logging.info('Filtered non matching records based on imp_agent_names')
            logging.info(not_matching_records)
            not_matching_records_len = not_matching_records.shape[0]
            logging.info('not_matching_records_len: {}'.format(not_matching_records_len))
            
            #latest values
            today_agent_data = raw_agent_data.loc[:,['Agent_Name','New_User_Rate']]
            today_agent_data = today_agent_data.query('Agent_Name in @imp_agent_names')
            today_agent_data = today_agent_data.sort_values(by='New_User_Rate', ascending=False).reset_index(drop=True)
            #logging.info(today_agent_data)
            #assigning the output data in a dictionary to read in the next task
            src_output['today_agent_data'] = today_agent_data.to_html(index=False)
            src_output['match_ind'] = row_matching_ind
            src_output['non_match_records'] = not_matching_records.to_html(index=False)
            src_output['non_match_record_cnt'] = not_matching_records_len
            #overriding the variable
            Variable.set('usdtoinr',value=src_output)
            logging.info('converting_into_dataframe processing completed')
            logging.info('The no of agents matching with prior ind: {0}'.format(row_matching_ind))

        else:
            logging.error('Data Extraction or converting into list failed from webpage')
            raise Exception('Data Extraction or converting into list failed from webpage')
    except BaseException as e:
        logging.error('load_usdtoinr_data method logic issue: {0}'.format(e))
        raise Exception('load_usdtoinr_data method logic issue')

def diff_send_email(**kwargs):
    '''
    This method sends email notification if there is a change in the rates.
    params:
    kwargs
    '''
    try:
        #reading the data from a variable returned by previous task
        src_output = eval(Variable.get('usdtoinr'))
        not_matching_records_len = int(src_output['non_match_record_cnt'])
        today = str(datetime.now().replace(microsecond=0)).replace(' ','_').replace(':','_')
        #checking if there are any changes in rates
        if not_matching_records_len>=1:
            logging.info('Preparing to send email notification')
            EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
            #print(EMAIL_ADDRESS)
            EMAIL_PASSWORD = os.environ.get('EMAIL_PASS')
            #print(EMAIL_PASSWORD)
            #Creating email inputs
            subject = "Today's Best US Dollars to Indian Rupees (USD to INR) Exchange Rate: "+today
            to = EMAIL_ADDRESS
            bcc = eval(Variable.get('airflow_usd_to_inr_bcc_list'))
            content1  = """Below are the updated rates:
            """
            content2 = """
Today's USD to INR rates:
            """
            footer = """
            
            
Thanks,
Sudhakar
            
            """
            file_name = ''
            #attachig the file to email
            #with open('remetely_rate_difference.csv','w') as f:
            #    not_matching_records.to_csv(f,index=False,sep='\t',float_format='%.2f')
            
            try:
                data_set = src_output['non_match_records'] #Variable.get('usdtoinr_non_match_records')
                today_data_set = src_output['today_agent_data'] #Variable.get('usdtoinr_today_agent_data')
                
                body = {content1 : data_set,
                        content2 : today_data_set,
                        footer : ''}
                #logging.info(body)
                #calling email sender script by passing the info
                email_sender.send_email(EMAIL_ADDRESS, EMAIL_PASSWORD, subject, to, bcc, body, file_name)
                logging.info('Sent email sucessfully')
            except BaseException  as e:
                logging.error('Sending email process failed: {0}'.format(e))
                raise Exception('Sending email process failed')
        else:
            logging.info('No change in agent information')
        
        #overriding the usdtoinr variable with execution date
        next_exec_date = {'next_execution_date': str(kwargs['next_execution_date'])}
        Variable.set('usdtoinr',value=next_exec_date)
        
    except BaseException  as e:
        logging.error('send_email method logic issue: {0}'.format(e))
        raise Exception('send_email method logic issue: {0}'.format(e))

#defining default arguments for the DAG
default_args = {
    'owner': Variable.get('airflow_owner'),
    #'start_date': datetime.now(),
    'start_date': datetime(2020,7,25),
    'email': eval(Variable.get('airflow_failure_notification_list')),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

#defining a DAG
dag = DAG('usdtoinr_dag', 
    description='Scheduling USD to INR web scraping and sending email job through python operators',
    schedule_interval='10 */6 * * *',
    catchup=False,
    default_args=default_args
)

#start dummy task
start = DummyOperator(task_id='Start_Task', dag=dag)

#reading webpage task
read_webpage = PythonOperator(task_id='Read_Webpage', 
    python_callable=read_webpage,
    provide_context=True,
    dag=dag)

#extracting data task
extract_usdtoinr_data = PythonOperator(task_id='Extract_USD_to_INR_Data', 
    python_callable=extract_usdtoinr_data,
    provide_context=True,
    dag=dag)

#processing data task
load_usdtoinr_data = PythonOperator(task_id='Load_USD_to_INR_Data', 
    python_callable=load_usdtoinr_data,
    provide_context=True,
    dag=dag)

#send email task
send_email = PythonOperator(task_id='Send_Email', 
    python_callable= diff_send_email,
    provide_context=True,
    dag=dag)

#end dummy task
end = DummyOperator(task_id='End_Task', dag=dag)

#task dependency
start >> read_webpage >> extract_usdtoinr_data >> load_usdtoinr_data >> send_email >> end
