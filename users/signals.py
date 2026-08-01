
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import CustomUser
from .activation import create_activation_for_user
from django.core.mail import send_mail
from django.conf import settings

def send_activation_code(user):
    """Создаёт код в Redis и отправляет email синхронно после коммита транзакции."""

    raw_code = create_activation_for_user(user)

    def _after_commit():
        subject = "Код подтверждения"
        message = f"""
Здравствуйте, {user.username}!

Ваш код подтверждения:

{raw_code}

Код действует 15 минут.
"""
        try:
            result = send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
            # result == number of successfully delivered messages (recipients)
            print(f"send_activation_email: sent={result}, to={user.email}, from={settings.DEFAULT_FROM_EMAIL}, host={getattr(settings, 'EMAIL_HOST', None)}, port={getattr(settings, 'EMAIL_PORT', None)}")
        except Exception as e:
            # Print exception to platform logs to aid debugging (no sensitive data like passwords)
            print(f"send_activation_email: failed to send to {user.email}: {e}")

    transaction.on_commit(_after_commit)
    return raw_code


@receiver(post_save, sender=CustomUser)
def check_registration(sender, instance, created, **kwargs):
    if created:
        send_activation_code(instance)