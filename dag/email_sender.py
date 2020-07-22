import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#this is reusable module for email sending
#Need to pass the below parameters to send email
def send_email(EMAIL_ADDRESS, EMAIL_PASSWORD, sub, to, bcc, body, file_name):
    
    COMMASPACE = ', '
    msg = MIMEMultipart()
    msg['Subject'] = sub
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to
    msg['Bcc'] = COMMASPACE.join(bcc)
    for key,value in body.items():
        msg.attach(MIMEText(key,'plain'))
        msg.attach(MIMEText(value,'html'))
    #part1 = MIMEText(content,'plain')
    #part2 = MIMEText(data_set,'html')
    #msg.attach(part1)
    #msg.attach(part2)
   
    with smtplib.SMTP_SSL('smtp.gmail.com',465) as smp:
        smp.login(EMAIL_ADDRESS,EMAIL_PASSWORD)
        smp.ehlo()
        smp.send_message(msg)
        print('Email sent sucessfully')
