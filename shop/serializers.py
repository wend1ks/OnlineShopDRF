from rest_framework import serializers
from .models import Category, Product, CartItem, Order, OrderItem
from users.models import Seller, CustomUser



class SellerInfoSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
    
    class Meta:
        model = Seller
        fields = ['id', 'username', 'email', 'rating', 'balance']
        read_only_fields = ['id', 'username', 'email', 'rating', 'balance']

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    seller_info = SellerInfoSerializer(source='seller', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'category', 'category_name',
            'description', 'image', 'stock_units', 'price',
            'seller', 'seller_info'
        ]
        read_only_fields = ['id', 'seller_info', 'created_at']
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value
    
    def validate_stock_units(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value


class ProductCreateUpdateSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'category', 'description',
            'image', 'stock_units', 'price', 'seller'
        ]
        read_only_fields = ['id']
    
    def validate(self, data):
        request = self.context.get('request')
        if request and request.method == 'POST':
            if 'seller' not in data:
                raise serializers.ValidationError({
                    "seller": "Seller is required."
                })
        return data


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    seller_username = serializers.CharField(source='seller.user.username', read_only=True)
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'category_name', 'image',
            'price', 'stock_units', 'seller_username'
        ]


class CartItemSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title')
    product_image = serializers.ImageField(source='product.image')
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'user', 'product', 'product_title', 'product_image',
            'product_price', 'quantity', 'line_total'
        ]
        read_only_fields = ['id', 'user', 'line_total', 'product_title', 'product_image', 'product_price']


class CartSerializer(serializers.Serializer):
    items = CartItemSerializer(many=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    
    class Meta:
        fields = ['items', 'total_price', 'total_items']


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_image', 'price', 'quantity', 'get_cost']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_email', 'user_username', 'address', 'city',
            'created_At', 'total_price', 'status', 'stripe_session_id', 'items'
        ]
        read_only_fields = ['user', 'stripe_session_id', 'created_At']

class OrderCreateSerializer(serializers.ModelSerializer):
    address = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    
    class Meta:
        model = Order
        fields = ['address', 'city']
    
    def validate(self, data):
        user = self.context['request'].user
        
        cart_items = CartItem.objects.filter(user=user)
        if not cart_items.exists():
            raise serializers.ValidationError("Your cart is empty.")
        
        total_price = sum(item.line_total() for item in cart_items)
        if total_price > 999999.99:
            raise serializers.ValidationError(
                f"Сумма заказа ({total_price} руб.) превышает максимально допустимый лимит в 999,999.99 руб."
            )
        
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        cart_items = CartItem.objects.filter(user=user)
        
        total_price = sum(item.line_total() for item in cart_items)
        
        order = Order.objects.create(
            user=user,
            total_price=total_price,
            address=validated_data['address'],
            city=validated_data['city'],
            status='PENDING'
        )
        
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                price=cart_item.product.price,
                quantity=cart_item.quantity
            )
        return order

class StripeSessionSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    success_url = serializers.URLField(required=False)
    cancel_url = serializers.URLField(required=False)
    
    

class PaymentStatusSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    
    
    

    
        
    
