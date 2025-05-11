from ManageSubscriptions import mail
from flask_login import current_user
from flask_mail import Message
from ManageSubscriptions import scheduler


def get_plan_limit():
    plan = current_user.subscription_type
    if plan == "free":
        return "200 per month"
    elif plan == "pro":
        return "20000 per day"
    elif plan == "ultimate":
        return None
    else:
        return "50 per month"
    
def send_email(subject,user_email,body):
    msg = Message(subject, 
                  sender='buisnesscybergpt05@gmail.com', 
                  recipients=[user_email])
    msg.body = body
    try:
        mail.send(msg)
        return True
    except:
        return False
    
