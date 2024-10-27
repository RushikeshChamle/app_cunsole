from celery import shared_task

from .models import User


@shared_task()
def get_users_count():
    """A pointless Celery task to demonstrate usage."""
    return User.objects.count()



from celery import shared_task
from django.core.mail import send_mail




import logging

logger = logging.getLogger(__name__)
from django.core.mail import EmailMessage

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

    # Create the email message
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email='rushikesh@cunsole.com',  # Change this to your 'from' email address
        to=recipient_list,
        cc=cc_list,  # Pass CC list to EmailMessage
    )

    # Send the email
    email.send(fail_silently=False)

    
