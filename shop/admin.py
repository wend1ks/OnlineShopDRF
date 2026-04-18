from django.contrib import admin
from .models import Category, Product

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    model = Category
    list_display = ("name", "parent")

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    model = Product
    list_display = ("title", "category", "description", "stock_units", "price", "seller")


