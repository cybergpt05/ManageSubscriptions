from ManageSubscriptions import scheduler, db, app
from ManageSubscriptions.models import Client,APIUsageTrack,ClientSubscriber
import csv,secrets,os
from ManageSubscriptions.helpers import send_email
from .helpers import send_logs
from datetime import datetime


@scheduler.task('cron', id='daily_notifications', hour=0, minute=0)
def notify_expiring_subs():
    with app.app_context():
        clients = Client.query.all()
        
        for client in clients:
            try:
                # Decrement remaining days for paid subscriptions
                if client.subscription_type != 'free' and client.remaining_days > 0:
                    client.remaining_days = int(client.remaining_days) - 1
                    db.session.commit()
                
                # Check for plan limit exceeded or about to exceed
                if client.subscription_type != 'free':
                    if not bool(client.notified_for_limit):
                        remaining_requests = client.allowed_requests - client.requests
                        
                        # Almost out of requests notification
                        if (0 < remaining_requests < 200) and (client.remaining_days > 0):
                            subject = 'Subly - Your API Request Quota is Almost Finished'
                            body = f'''
    Hi {client.name},

    We noticed that your remaining API request quota for your {client.subscription_type} tier subscription is below 200.

    To ensure uninterrupted service, we recommend upgrading your subscription or monitoring your usage more closely.

    You can view your usage details here: https://subly.io/my/dashboard

    Best regards,  
    The Subly.io Team
    '''
                            if send_email(subject, client.email, body):
                                client.notified_for_limit = True
                                db.session.commit()
                        
                        # Out of requests notification
                        elif (remaining_requests <= 0) and (client.remaining_days > 0):
                            subject = 'Subly - You Have Reached Your API Request Limit'
                            body = f'''
    Hi {client.name},

    You've used all your API requests for the current period.

    Your API token are now paused until your quota resets or you upgrade your plan. To resume access, please visit:

    https://subly.io/pricing

    Thank you for using Subly.io.

    Best regards,  
    The Subly.io Team
    '''
                            if send_email(subject, client.email, body):
                                client.notified_for_limit = True
                                db.session.commit()
                
                # Check for expiring subscriptions
                if client.subscription_type != 'free':
                    if not client.notified_for_expiration and client.remaining_days == 3:
                        subject = 'Subly - Your Subscription is About to Expire'
                        body = f'''
    Hi {client.name},

    Just a reminder — your subscription will expire in {client.remaining_days} days.

    To avoid losing access to your service and data, please consider renewing or upgrading your plan.

    Manage your subscription here: https://subly.io/my/account

    Best regards,  
    The Subly.io Team
    '''
                        if send_email(subject, client.email, body):
                            client.notified_for_expiration = True
                            db.session.commit()
                    
                    elif client.remaining_days == 0:
                        subject = 'Subly - Your Subscription Has Expired'
                        body = f'''
    Hi {client.name},

    Your subscription on Subly.io has expired.

    You no longer have access to your API services until your plan is renewed. To continue using our services without interruption, please renew or upgrade your plan here:

    https://subly.io/pricing

    We're here to support you if you need any help.

    Best regards,  
    The Subly.io Team
    '''
                        if send_email(subject, client.email, body):
                            client.notified_for_expiration = True
                            db.session.commit()
                            
            except:
                db.session.rollback()


@scheduler.task('cron', id='daily_reset_subscriptions', hour=1, minute=0)
def reset_subscribtions():
    with app.app_context():
        all_clients = Client.query.all()
        if all_clients:
            for client in all_clients:
                if client.subscription_type != 'free':
                    if client.remaining_days == 0:
                        client.requests = 0
                        client.allowed_requests = 200
                        client.subscribers_limit = 30
                        client.plans_limit = 1
                        client.subscription_type = 'free'
                        client.notified_for_limit = False
                        client.notified_for_expiration = False
                        client.api_logs_chart = None
                        client_logs = APIUsageTrack.query.filter_by(client_id=client.id).all()
                        if client_logs:
                            csv_file_path = f'{secrets.token_hex(12)}_{client.id}.csv'
                            file_path = os.path.join(app.root_path, 'static' , 'api_logs_backups' , csv_file_path)
                            with open(file_path, 'w', newline='') as csvfile:
                                fieldnames = ['Date', 'Requests sent']
                                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                writer.writeheader()
                                for log in client_logs:
                                    writer.writerow({
                                        "Date":log.usage_date,
                                        "Requests sent":log.usage_quantity
                                    })
                                
                                body= f'''
    Hello {client.name},

    Your subscription has ended and has been reset to the free plan.
    Attached you'll find your API usage logs before they were removed from our system.

    Thank you for using our services.

    Best regards,
    subly.io Team
    '''
                                try:
                                    email_status = send_logs(subject='Subly - API usage for this month', user_email= 'mjalmousa2005@gmail.com', body=body, attachment_file=file_path)
                                    if not email_status:
                                        with open(f'{str(datetime.now().date())}.txt', 'a') as error_file:
                                            error_file.write(f'Failed to send API logs file to {client.email}, logs file name : {csv_file_path}, time: {str(datetime.now())}')
                                            error_file.close()
                                except Exception as error:
                                    with open(f'{str(datetime.now().date())}.txt', 'a') as error_file:
                                        error_file.write(f'Failed to send API logs file to {client.email}, logs file name : {csv_file_path}, time: {str(datetime.now())}, error: {error}')
                                        error_file.close()
                            for log in client_logs:
                                db.session.delete(log)
                        db.session.commit()

@scheduler.task('cron', id='daily_decrease_clients_subscribers', hour=1, minute=30)
def decrease_clients_subscribers():
    with app.app_context():
        all_subs = ClientSubscriber.query.all()
        if all_subs:
            for sub in all_subs:
                if sub.remaining_days != 0:
                    sub.remaining_days -= 1
                else:
                    if sub.is_active != False:
                        sub.is_active = False
            db.session.commit()