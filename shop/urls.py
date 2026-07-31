from django.urls import path
from .views import *

app_name = 'shop'

urlpatterns = [
    # магазин апи
    path('api/products/', ProductListAPIView.as_view(), name='api_products_list'),
    path('api/products/<int:product_id>/', ProductDetailAPIView.as_view(), name='api_product_detail'),
    path('api/products/create/', ProductCreateAPIView.as_view(), name='api_product_create'),
    path('api/cart/update/<int:product_id>/<str:action>/', UpdateQuantityAPIView.as_view(), name='api_cart_update'),   
    path('api/cart/', CartAPIView.as_view(), name='api_cart'),
    path('api/cart/toggle/<int:product_id>/', CartToggleAPIView.as_view(), name='api_cart_toggle'),

    # магазин странички
    path('products/',products_list_page, name='products_list'),
    path('add_product_page', add_product_page, name='add_product'),
    path('product/<int:product_id>/', product_detail, name='add_product'),
    path('cart_page', cart_page, name='cart'),
    
    # оплата    
    path('api/create-order/', CreateOrderView.as_view(), name='api_create_order'),
    path('api/create-checkout-session/<int:order_id>/', CreateCheckoutSessionView.as_view(), name='api_create_checkout_session'),
    path('stripe/success/<int:order_id>/', stripe_success, name='stripe_success'),
    path('stripe/cancel/<int:order_id>/', stripe_cancel, name='stripe_cancel'),

]