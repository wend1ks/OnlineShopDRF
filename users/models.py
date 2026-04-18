from django.db import models
from django.contrib.auth.models import AbstractUser
import random
from django.utils import timezone
from datetime import timedelta

# Create your models here.

class CustomUser(AbstractUser):
    user_image = models.ImageField(
        blank=True,
        null=True,
        help_text='Фото профиля (рекомендуемый размер 400x400)',
        upload_to='Users/user_image/'
    )
    USER_ROLES = (
        ("customer", "Покупатель"),
        ("seller", "Продавец")
    )
    role = models.CharField(max_length=20, choices=USER_ROLES, default='customer')
    phone_number = models.CharField(max_length=32)
    def is_customer(self):
        return self.role == "customer" or self.groups.filter(name="customer").exists()
    def is_seller(self):
        return self.role == "seller" or self.groups.filter(name="seller").exists()
    
    def __str__(self):
        return self.username

class Seller(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    payout_details = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.user.username

def random_code():
        letters = [str(random.randint(0, 9)) for _ in range(4)]
        return ''.join(letters)

class ActivationCode(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activation_codes')
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0) 
    
    @classmethod
    def create_for_user(cls, user, lifetime_minutes=15):
        raw_code = random_code()
        obj = cls.objects.create(
            user=user,
            code=raw_code,
            expires_at=timezone.now() + timedelta(minutes=lifetime_minutes)
        )
        return obj, raw_code

    def is_valid(self):
        return (not self.used) and (timezone.now() <= self.expires_at)
    
    def check_code(self, code, max_attempts=5):
        if self.used:
            return False, 'Код уже использован'
        
        if timezone.now() > self.expires_at:
            print(f"DEBUG: timezone.now() = {timezone.now()}")
            print(f"DEBUG: expires_at = {self.expires_at}")
            print(f"DEBUG: Difference = {self.expires_at - timezone.now()}")
            return False, 'Срок действия кода истек'
        
        if self.attempts >= max_attempts:
            return False, 'Слишком много попыток'
        
        if self.code == code:
            self.used = True
            self.save()
            return True, None
        
        self.attempts += 1
        self.save()
        return False, 'Неверный код'
    
    def __str__(self):
        return f"{self.user.email} - {self.code} - {'Использован' if self.used else 'Активен'} до {self.expires_at}"
    

    