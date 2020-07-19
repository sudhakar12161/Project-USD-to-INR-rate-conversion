from bs4 import BeautifulSoup as bs
import requests
from selenium import webdriver
import pandas as pd
from sqlalchemy import create_engine,Table,MetaData,Column,PrimaryKeyConstraint,String,Integer,Float,DateTime
from datetime import datetime
import logging
from os import path
import os
import email_sender


#from apscheduler.schedulers.background import BackgroundScheduler
#from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
#from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor

#log file setup
today = str(datetime.now().replace(microsecond=0)).replace(' ','_').replace(':','_')
#log_file_name = r'C:\Users\sudamire\OneDrive - Capgemini\Documents\GitHub\dev\log\usdtoinr.log'
log_file_name = '/home/airflow/airflow/my_logs/usdtoinr_'+today+'.log'


logger = logging.getLogger('usdtoinr.py')
logger.setLevel(logging.INFO)
formater = logging.Formatter('%(asctime)s: %(name)s: %(levelname)s: %(funcName)s: %(message)s')
file_handler = logging.FileHandler(log_file_name,'w+')
file_handler.setFormatter(formater)
logger.addHandler(file_handler)

#processing HTML file and extracting datas

def processing_usd_to_inr_page(soup):
    
    try:
        output = []
        logger.info('Created empty output list')
        #assign top level div info to a variable
        today_rates = soup.find_all('div',class_='table-1 best-row active')
        logger.info('Assigned the main division from HTML to today_rates')
        #reading one by one agent info
        logger.info('Processing each Agent info')
        logger.info('Creating row_output variable to process each Agent info')
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
                    #print()
                    rate_amt = float(rate_info.text[2:].lstrip().rstrip())
                    row_output.append(lbl_name)
                    row_output.append(rate_amt)
                    #print(lbl_name,end='\n')
                    #print(rate_amt,end='\n')

            #print(row_output)
            #appending the record to output list
            output.append(row_output)
        logger.info('Process done and returning output list')
        return output
           
    except BaseException  as e:
        logger.error('Issue with the returned webpage by Chrome driver: {0}'.format(e))
        raise Exception('Issue with the returned webpage by Chrome driver: {0}'.format(e))

def converting_into_dataframe(output):
    try:
        
        #creating database conn to sqlite databse
        engine = create_engine('sqlite:////home/airflow/airflow/rate_conversion.db')
        metadata = MetaData(engine)
        #creating table or accessing
        table = Table('Compare_Rate_USD_to_INR',metadata,
            Column('Date_Id',DateTime),
            Column('Agent_Name',String(50)),
            Column('New_User_Rate',Float),
            Column('Regular_Rate',Float),
            Column('Transfer_Fee_Rate',Float),
            PrimaryKeyConstraint('Date_Id','Agent_Name',name='Compare_Rate_USD_to_INR_PK')
             )
        #creating table
        metadata.create_all()
        logger.info('Created/Connected rate_conversion.db database, sqlite engine, table, metadata')
        #print(raw_agent_data)
        #pulling data from sqlite table and loading into dataframe
        old_record = pd.read_sql('''SELECT * from Compare_Rate_USD_to_INR 
                                    WHERE Date_Id = (SELECT max(Date_Id) FROM Compare_Rate_USD_to_INR) 
                                    ORDER BY Agent_Name''',engine,parse_dates={'Date_Id'})
        #Removing date_id column
        old_record = old_record.iloc[:,1:]
        
        #converting list to dataframe and adding columns
        raw_agent_data = pd.DataFrame(output,columns=['Agent_Name','New_User','New_User_Rate','Regular_User','Regular_Rate','Transfer_Fee','Transfer_Fee_Rate'])
        logger.info('Converted into DataFrame and added columns')
        raw_agent_data=raw_agent_data.drop(['New_User','Regular_User','Transfer_Fee'],axis=1).sort_values(by='Agent_Name').reset_index(drop=True)
        logger.info('Dropped desc fileds')
        #the below line is for testing purpose
        #raw_agent_data.loc[raw_agent_data['Agent_Name']=='Xoom','New_User_Rate']=75.2
        #Below line for testing
        #raw_agent_data.loc[raw_agent_data['Agent_Name']=='Xoom','New_User_Rate']=75.2
        #imp_agent_names is preferred agents
        imp_agent_names =['RIA Money Transfer','Remitly','Western Union','Xoom']
        #creating not matching recrods with old data
        not_matching_records = pd.DataFrame(columns=raw_agent_data.columns)
        not_matching_records['New_User_Rate_Difference'] = None
        not_matching_records['New_User_Rate_Difference_desc'] = None
        not_matching_records['Regular_Rate_Difference'] = None
        #comparing the no of agents with prior data
        row_matching_ind = True if len(raw_agent_data) == len(old_record) else False
        #cnt is helpfull to notedown the index in the loop
        cnt = 0
        logger.info('Assigned header row to the not_matching_records DataFrame')
        for i in range(len(raw_agent_data)):
            if  row_matching_ind and not (old_record.iloc[i].equals(raw_agent_data.iloc[i])):
                not_matching_records = not_matching_records.append(raw_agent_data.iloc[i],ignore_index=True)
                not_matching_records.loc[cnt,'New_User_Rate_Difference']=raw_agent_data.loc[i,'New_User_Rate']-old_record.loc[i,'New_User_Rate']
                not_matching_records.loc[cnt,'New_User_Rate_Difference_desc']='Increased' if not_matching_records.loc[cnt,'New_User_Rate_Difference']>0 else 'Decreased'
                not_matching_records.loc[cnt,'Regular_Rate_Difference']=raw_agent_data.loc[i,'Regular_Rate']-old_record.loc[i,'Regular_Rate']
                cnt = cnt+1
        logger.info('Proccessed not matching records and added the difference')
        #appending/inserting the data to table
        #adding Data_id column
        raw_agent_data.insert(0,'Date_Id', datetime.now().replace(microsecond=0))
        if not (row_matching_ind) or len(not_matching_records)>0:
            raw_agent_data.to_sql('Compare_Rate_USD_to_INR',engine,index=False,if_exists='append')
            logger.info('Data has been inserted into the databse')
        else:
            logger.info('0 records inserted into database')
        #keeping only prefeered agents
        not_matching_records = not_matching_records.query('Agent_Name in @imp_agent_names')
        logger.info('Filtered non matching records based on imp_agent_names')
        return not_matching_records,row_matching_ind

    except BaseException  as e:
        logger.error('converting_into_dataframe method logic issue: {0}'.format(e))
        raise Exception('converting_into_dataframe method logic issue: {0}'.format(e))

#main function and triggers automatically when script triggered
def compare_rate_web_scraping():
    
    try:
        #location of the browser driver
        path = '/usr/bin/chromedriver'
        logger.info('Web driver located at:  {0}'.format(path))
        options = webdriver.ChromeOptions()
        #adding options to the webdriver
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--incognito")
        options.add_argument("--headless")
        options.add_argument("--disable-popup-blocking");
        options.add_argument("test-type");
        logger.info('Added web driver options to Chrome driver')
        #creating driver with options
        driver = webdriver.Chrome(path,options=options)
        logger.info('Created driver object for Chrome WebDriver')
        #calling the wep page
        driver.get('https://www.compareremit.com/todays-best-dollar-to-rupee-exchange-rate/')
        logger.info('Request sent to web page https://www.compareremit.com/todays-best-dollar-to-rupee-exchange-rate/')
        #assigning the HTML code to a variable
        src = driver.page_source
        #print('Web page read')
        logger.info('Loaded web page source into a variable called src')
        if src is not None:
            soup = bs(src,'lxml')
            logger.info('Converted the response into HTML format')
            #calling processing method
            logger.info('Sending the HTML page to a method to process and return list')
            output = processing_usd_to_inr_page(soup)
            #print(output)
            logger.info('Below is the output from processing_usd_to_inr_page()')
            for i in output:
                logger.info(i)
            if len(output)>=1:
                logger.info('Passing the list to converting_into_dataframe method to process the data')
                not_matching_records,row_matching_ind=converting_into_dataframe(output)
                #generate only if changes are there
                logger.info('converting_into_dataframe processing completed')
                logger.info('The no of agents matching with prior ind: {0}'.format(row_matching_ind))
                not_matching_records_len = not_matching_records.shape[0]
                if not_matching_records_len>=1:
                    logger.info('Preparing to send email notification')
                    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
                    #print(EMAIL_ADDRESS)
                    EMAIL_PASSWORD = os.environ.get('EMAIL_PASS')
                    #print(EMAIL_PASSWORD)
                    subject = "Today's Best US Dollars to Indian Rupees (USD to INR) Exchange Rate: "+today
                    to = EMAIL_ADDRESS
                    bcc = EMAIL_ADDRESS
                    content  = """"Today's Best US Dollars to Indian Rupees (USD to INR) Exchange Rate: {today}""".format(today=today)
                    file_name = ''
                    #attachig the file to email
                    #with open('remetely_rate_difference.csv','w') as f:
                    #    not_matching_records.to_csv(f,index=False,sep='\t',float_format='%.2f')
                    
                    try:
                        data_set = not_matching_records.to_html()
                        #print(data_set)
                        email_sender.send_email(EMAIL_ADDRESS,EMAIL_PASSWORD,subject,to,bcc,content,file_name,data_set)
                        logger.info('Sent email sucessfully')
                    except BaseException  as e:
                        logger.error('Failed process of sending email: {0}'.format(e))
                        raise Exception('Failed process of sending email: {0}'.format(e))
                else:
                    print('No difference found in agent rates')
                    logger.info('No difference found in agent rates')
            else:
                logger.error('Agnet Web scraping failed because of add or something')
        else:
            logger.info('Returned empty webpage')
    except BaseException  as e:
        logger.error('Web driver issue, {0}'.format(e))
        

def main_test():
    try:
        #Start the scheduler
        #Scheduler setup
        logger.info('Program execution started at: {0}'.format(datetime.now()))
        #logger.info('Invoking scheduler')
        #jobstores = {'default': SQLAlchemyJobStore(url='sqlite:///usatoinr_schedule_job_list.db')}
        #executors = {'default': ThreadPoolExecutor(20)}
        #job_defaults = {'coalesce': True,'max_instances': 1,'misfire_grace_time': 1}
        #scheduler = BackgroundScheduler(executors=executors,jobstores=jobstores,job_defaults=job_defaults,daemon=True)
        #scheduler.add_job(compare_rate_web_scraping, 'interval', minutes=10)
        #print('test')
        #scheduler.start()
        #scheduler.add_job(compare_rate_web_scraping, 'interval', minutes=10)
        #print('passed')
        compare_rate_web_scraping()
    
    except BaseException  as e:
        logger.error('main_test method failed: {0}'.format(e))
        raise Exception('main_test method failed: {0}'.format(e))
        #logging.error('Schedule failed to Start')


# Schedule job_function to be called every two hours

if __name__ == '__main__':
    main_test()
