from django.db import models
from users.models import *

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name
    
class Product(models.Model):
    title = models.CharField(max_length=150)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    description = models.TextField()
    image = models.ImageField(upload_to='Shop/product_image/')
    stock_units = models.PositiveBigIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    

    def __str__(self):
        return self.title
    
class CartItem(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product')
    quantity = models.PositiveBigIntegerField(default=1)
    
    def line_total(self):
        return self.product.price * self.quantity
    
    def __str__(self):
        return f"{self.user} - {self.product} x {self.quantity}"
    
class Order(models.Model):
    user = models.ForeignKey(CustomUser,related_name='orders', on_delete=models.CASCADE, verbose_name='Пользователь')
    address = models.CharField(max_length=150, null=True)
    city = models.CharField(max_length=100, null=True)

    created_At = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    #Работа с оплатой
    STATUS_CHOICES = [
        ('PENDING', 'Ожидает оплату'),
        ('PAID', 'Оплачен'),
        ('FAILED', 'Ошибка оплаты'),
        ('DELIVERED', 'Доставлен'),
        ('CANCELED', 'Отменён'),
    ]

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('shop:order_detail', args=[self.id])

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    stripe_session_id = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f'Заказ №{self.id} Статус: {self.status}'
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveBigIntegerField(default=1)

    def __str__(self):
        return f'{self.id}'

    def get_cost(self):
        return self.price * self.quantity