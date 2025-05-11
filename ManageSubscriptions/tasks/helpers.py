from flask_mail import Message
from ManageSubscriptions import mail

def send_logs(subject,user_email,body,attachment_file):
    msg = Message(subject, 
                sender='buisnesscybergpt05@gmail.com', 
                recipients=[user_email])
    msg.body = body
    with open(attachment_file, 'rb') as file:
        msg.attach('api_usage_logs.csv', 'text/csv', file.read())
    try:
        mail.send(msg)
        return True
    except:
        return False