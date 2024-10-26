from celery import shared_task

from .models import User


@shared_task()
def get_users_count():
    """A pointless Celery task to demonstrate usage."""
    return User.objects.count()



from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_test_email(email_data):
    """
    Send a test email using Celery.
    """
    subject = email_data['subject']
    message = email_data['message']
    recipient_list = email_data['recipient_list']

    send_mail(
        subject,
        message,
        'rushikesh@cunsole.com',  # Change this to your 'from' email address
        recipient_list,
        fail_silently=False,
    )
