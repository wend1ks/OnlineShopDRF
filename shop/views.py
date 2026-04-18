from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import *
from .serializers import *
import stripe
from django.shortcuts import render,redirect
from django.urls import reverse
from users.models import CustomUser

stripe.api_key = settings.STRIPE_SECRET_KEY

class ProductListAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
        
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductListSerializer(products, many=True)

        data = serializer.data
        if request.user.is_authenticated:
            cart_ids = set(request.user.cart_items.values_list('product_id', flat=True))
            for item in data:
                item['in_cart'] = item['id'] in cart_ids
        
        return Response(data)


class ProductDetailAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        serializer = ProductSerializer(product)
        
        data = serializer.data
        if request.user.is_authenticated:
            from .models import CartItem
            data['in_cart'] = CartItem.objects.filter(user=request.user, product=product).exists()
        
        return Response(data)


class ProductCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        if not request.user.is_seller():
            return Response({'error': 'Только продавцы могут добавлять товары'},status=403)

        seller, created = Seller.objects.get_or_create(user=request.user)
        
        data = request.data.copy()
        data['seller'] = seller.id
        
        serializer = ProductCreateUpdateSerializer(data=data,context={'request': request})
        
        if serializer.is_valid():
            product = serializer.save()
            return Response(ProductSerializer(product).data,status=201)
        
        return Response(serializer.errors, status=400)


class CartAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        cart_items = CartItem.objects.filter(user=request.user)
        serializer = CartItemSerializer(cart_items, many=True)
        
        total_price = sum(item.line_total() for item in cart_items)
        total_items = cart_items.count()
        
        return Response({
            'items': serializer.data,
            'total_price': total_price,
            'total_items': total_items
        })




class CartToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product
        )
        if not created:
            cart_item.delete()
            return Response(None)
        return Response({'in_cart': True}, status=201)
    
class UpdateQuantityAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, product_id, action):
        product = get_object_or_404(Product, id=product_id)
        
        
        cart_item = get_object_or_404(CartItem, user=request.user, product=product)
        
        if action == 'plus':
            if cart_item.quantity >= product.stock_units:
                return Response(
                    {'error': f'В наличии только {product.stock_units} ед.'},status=400)
            cart_item.quantity += 1
            cart_item.save()
            
        elif action == 'minus':
            if cart_item.quantity == 1:
                cart_item.delete()
                return Response({'deleted': True})
            else:
                cart_item.quantity -= 1
                cart_item.save()
        else:
            return Response(
                status=400
            )
        
        return Response({'quantity': cart_item.quantity,'line_total': cart_item.line_total(),'product_id': product.id,'product_title': product.title})


class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        cart_items = CartItem.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response({'error': 'Корзина пуста'}, status=status.HTTP_400_BAD_REQUEST)
        
        total_price = sum(item.line_total() for item in cart_items)

        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            address='', 
            city=''      
        )
        
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                price=cart_item.product.price,
                quantity=cart_item.quantity
            )
        
        
        return Response({
            'order_id': order.id,
            'total_price': str(order.total_price)
        })

class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user, status='PENDING')
        line_item = {
            'price_data': {
                'currency': 'rub',
                'unit_amount': int(order.total_price * 100),
                'product_data': {
                    'name': f"Заказ №{order.id}",
                }
            },
            'quantity': 1
        }
        
        success_url = request.build_absolute_uri(reverse('shop:stripe_success', args=[order.id]))
        cancel_url = request.build_absolute_uri(reverse('shop:stripe_cancel', args=[order.id]))
        
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[line_item],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={'order_id': order.id}
            )
            
            order.stripe_session_id = checkout_session.id
            order.save()
            
            return Response({
                'session_url': checkout_session.url,
                'session_id': checkout_session.id
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StripeSuccessView(APIView):
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        
        try:
            session = stripe.checkout.Session.retrieve(order.stripe_session_id)
            
            if session.payment_status == 'paid':
                order.status = 'PAID'
                order.save()
                
                if order.user:
                    CartItem.objects.filter(user=order.user).delete()
                
                return Response({
                    'success': True,
                    'order_id': order.id,
                    'status': 'PAID'
                })
            else:
                return Response({
                    'success': False,
                    'order_id': order.id,
                    'status': order.status
                })
                
        except Exception as e:
            return Response({'error': str(e)}, status=404)

class StripeCancelView(APIView):
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        return Response({
            'success': False,
            'order_id': order.id,
            'status': order.status,
            'message': 'Платеж отменен'
        })

class OrderStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        return Response({
            'order_id': order.id,
            'status': order.status,
            'total_price': str(order.total_price)
        })
 

def stripe_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    session_id = order.stripe_session_id

    if not session_id:
        return redirect('shop:cart') 

    try:    
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == 'paid':
            order.status = "PAID"
            order.save(update_fields=['status'])
            CartItem.objects.filter(user=order.user).delete()
        else:
            return redirect('shop:cart')
    
    except Exception as e:
        print(f"Ошибка: {e}")
        return redirect('shop:cart')

def stripe_cancel(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return redirect('https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygUJcmljayByb2xs')

def products_list_page(request):
    if not request.user.is_authenticated:
        return redirect('users:signin_page')
    return render(request, 'products_list.html')

def add_product_page(request):
    if not request.user.is_authenticated:
        return redirect('users:signin_page')
    return render(request, 'add_product.html')

def cart_page(request):
    if not request.user.is_authenticated:
        return redirect('users:signin_page')
    return render(request, 'cart.html')

def product_detail(request, product_id):
    product = Product.objects.get(id=product_id)
    return render(request, 'product_detail.html', {'product': product})