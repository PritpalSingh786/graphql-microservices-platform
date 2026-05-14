from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task


@shared_task
def send_email_task(subject, message, recipient_list):
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)


# clean_expired_tokens task REMOVED - Redis handles automatically!