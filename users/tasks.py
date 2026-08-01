from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_activation_email_task(user_email, username, code):
    subject = "Ваш код подтверждения"
    message = f"""Привет {username}!
Ваш код подтверждения: {code}
Действителен 15 минут."""

    send_mail(
        subject,
        message,
        None,
        [user_email],
    )

    return f"Email sent to {user_email}"