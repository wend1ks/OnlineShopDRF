
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import CustomUser
from .activation import create_activation_for_user
from .tasks import send_activation_email_task

def send_activation_code(user):
    """Создаёт код в Redis и отправляет email через Celery после коммита транзакции."""

    raw_code = create_activation_for_user(user)

    def _after_commit():
        send_activation_email_task(user.email, user.username, raw_code)

    transaction.on_commit(_after_commit)
    return raw_code


@receiver(post_save, sender=CustomUser)
def check_registration(sender, instance, created, **kwargs):
    if created:
        send_activation_code(instance)