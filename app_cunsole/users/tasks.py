from celery import shared_task

from .models import User


@shared_task()
def get_users_count():
    """A pointless Celery task to demonstrate usage."""
    return User.objects.count()



from celery import shared_task
from django.core.mail import send_mail

# @shared_task
# def send_test_emails(email_data):
#     """
#     Send a test email using Celery.
#     """
#     subject = email_data['subject']
#     message = email_data['message']
#     recipient_list = email_data['recipient_list']

#     send_mail(
#         subject,
#         message,
#         'rushikesh@cunsole.com',  # Change this to your 'from' email address
#         recipient_list,
#         fail_silently=False,
#     )



# @shared_task
# def send_test_emails(email_data):
#     """
#     Send a test email using Celery.
#     """
#     subject = email_data['subject']
#     message = email_data['message']
#     recipient_list = email_data['recipient_list']
#     cc_list = email_data.get('cc_list', [])  # Default to empty list if not provided

#     send_mail(
#         subject,
#         message,
#         'rushikesh@cunsole.com',  # Change this to your 'from' email address
#         recipient_list,
#         cc=cc_list,  # Pass CC list to send_mail
#         fail_silently=False,
#     )


import logging

logger = logging.getLogger(__name__)

@shared_task
def send_test_emails(email_data):
    """
    Send a test email using Celery.
    """
    subject = email_data['subject']
    message = email_data['message']
    recipient_list = email_data['recipient_list']
    cc_list = email_data.get('cc_list', [])  # Default to empty list if not provided

    logger.info(f"Sending email to: {recipient_list}, CC: {cc_list}")  # Log the recipients

    send_mail(
        subject,
        message,
        'rushikesh@cunsole.com',  # Change this to your 'from' email address
        recipient_list,
        cc=cc_list,  # Pass CC list to send_mail
        fail_silently=False,
    )







# @shared_task
# def send_test_emails(email_data):
#     """
#     Send a test email using Celery.
#     """
#     from django.core.mail import EmailMessage
#     import logging

#     logger = logging.getLogger(__name__)
    
#     try:
#         subject = email_data['subject']
#         message = email_data['message']
#         recipient_list = email_data['recipient_list']
#         cc_list = email_data.get('cc', [])  # Changed from cc_list to cc
#         from_email = 'rushikesh@cunsole.com'

#         # Ensure recipient_list and cc_list are lists
#         if isinstance(recipient_list, str):
#             recipient_list = [recipient_list]
#         if isinstance(cc_list, str):
#             cc_list = [cc_list]

#         logger.info(f"Attempting to send email to {recipient_list} with CC {cc_list}")

#         # Create EmailMessage object
#         email = EmailMessage(
#             subject=subject,
#             body=message,
#             from_email=from_email,
#             to=recipient_list,
#             cc=cc_list,
#         )

#         # Send the email
#         email.send(fail_silently=False)
#         logger.info("Email sent successfully")
        
#         return {
#             'status': 'success',
#             'to': recipient_list,
#             'cc': cc_list
#         }
        
#     except Exception as e:
#         logger.error(f"Failed to send email: {str(e)}")
#         raise