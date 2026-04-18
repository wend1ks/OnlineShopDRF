from django.apps import AppConfig
import stripe
from django.conf import settings
class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop'

    def ready(self):
        # Импортируем настройки и устанавливаем ключ Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
