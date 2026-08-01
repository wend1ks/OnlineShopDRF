from django.conf import settings
from django.core.mail import send_mail
from celery import shared_task


@shared_task
def send_activation_email_task(user_email, username, code):
    subject = "Код подтверждения"

    message = f"""
Здравствуйте, {username}!

Ваш код подтверждения:

{code}

Код действует 15 минут.
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
    )