from django.contrib import admin
from .models import CustomUser, Seller
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
# Register your models here.

@admin.register(CustomUser)
class UserAdmin(DjangoUserAdmin):
    model = CustomUser
    list_display = ("username", "email", "first_name","last_name", "role")
    fieldsets = (
        *DjangoUserAdmin.fieldsets,
        ("Дополнительно", {"fields": ("photo", "role")})
    )

@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    model = Seller
    list_display = ("user", "rating", "balance", "payout_details")