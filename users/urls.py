from django.urls import path,include
from .views import *

app_name = 'users'


app_name = 'users'

urlpatterns = [

    path('signup/', signup_page, name='signup_page'),
    path('signin/', signin_page, name='signin_page'),
    path('verify-code/' , verify_code_page, name='verify_code_page'),
    path('profile/update', profile_page, name='profile_page'),

    path('api/signup/', SignUpAPIView.as_view(), name='api_signup'),
    path('api/verify-code/', VerifyCodeAPIView.as_view(), name='api_verify_code'),
    path('api/signin/', SignInAPIView.as_view(), name='api_signin'),
    path('api/signout/', SignOutAPIView.as_view(), name='api_signout'),
    path('api/resend-code/', ResendCodeAPIView.as_view(), name='api_resend_code'),
    path('api/profile/update/', UserProfileUpdateAPIView.as_view(), name='profile_update')
]