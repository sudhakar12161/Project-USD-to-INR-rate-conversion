import smtplib
from email.message import EmailMessage

#this is reusable module for email sending
#Need to pass the below parameters to send email
def send_email(EMAIL_ADDRESS,EMAIL_PASSWORD,sub,to,bcc,content,file_name,data_set):

    msg = EmailMessage()
    msg['Subject'] = sub
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to
    msg['Bcc'] = bcc
    msg.set_content('{0}\n\n'.format(content))

    msg.add_alternative(data_set,subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com',465) as smp:
        smp.login(EMAIL_ADDRESS,EMAIL_PASSWORD)
        smp.ehlo()
        smp.send_message(msg)
        print('Email sent sucessfully')
