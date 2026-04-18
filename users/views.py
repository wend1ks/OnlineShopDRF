from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from django.db import transaction
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView 
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.conf import settings

from .serializers import *
from .models import *
from .forms import *
from .signals import *
from .activation import get_activation, bump_attempts, consume_activation


class SignUpAPIView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(is_active=False)
            if request.data.get('is_seller', False):
                Seller.objects.create(user=user)
            
            request.session['active_email'] = user.email
            request.session.save()
            
            return Response({
                'status': 'success',
                'message': 'Пользователь создан. Код активации отправлен на email.',
                'user_id': user.id,
                'email': user.email
            })
        return Response({'errors': serializer.errors}, status=400)
    

class VerifyCodeAPIView(APIView):
    def post(self, request):
        serializer = ActivationCodeCheckSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
            
        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]
        
        user = CustomUser.objects.filter(email=email).order_by('-date_joined').first()
        
        if not user:
            return Response({'detail': 'Пользователь с таким email не найден'}, status=400)

        payload = get_activation(user)
        if not payload:
            return Response({'detail': 'Код активации не найден или срок действия истек'}, status=400)

        max_attempts = int(getattr(settings, 'ACTIVATION_CODE_MAX_ATTEMPTS', 5))
        if payload.attempts >= max_attempts:
            consume_activation(user)
            return Response({'detail': 'Слишком много попыток'}, status=400)

        if payload.code != code:
            payload = bump_attempts(user)
            attempts_left = max(0, max_attempts - (payload.attempts if payload else max_attempts))
            return Response({'detail': f'Неверный код. Осталось попыток: {attempts_left}'}, status=400)

        consume_activation(user)
        
        with transaction.atomic():
            user.is_active = True
            user.save()
            
            if user.role == "seller" or user.is_seller():
                Seller.objects.get_or_create(user=user)
        
        login(request, user)
        
        if 'active_email' in request.session:
            request.session.pop('active_email')
        
        return Response({
            'username': user.username,
            'email': user.email
        }, status=200)


class ResendCodeAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        
        if not email:
            return Response({'detail': 'Email обязателен'}, status=400)
        
        user = CustomUser.objects.filter(email=email).order_by('-date_joined').first()
        
        if not user:
            return Response({'detail': 'Пользователь не найден'}, status=400)
        
        send_activation_code(user)
        
        return Response({'status': 'sent'}, status=200)


class UserProfileUpdateAPIView(APIView):    
    def put(self, request):
        user = request.user
        serializer = UserProfileUpdateSerializer(user, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({'user': serializer.data}, status=200)
        
        return Response(serializer.errors, status=400)
    
    def patch(self, request):
        user = request.user
        serializer = UserProfileUpdateSerializer(user, data=request.data,partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({'user': serializer.data}, status=200)
        
        return Response(serializer.errors, status=400)    


class SignInAPIView(APIView):
    def post(self, request):
        serializer = SignInSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data["username"]
            password = serializer.validated_data["password"]

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return Response({'user_id': user.id, 'username': user.username})
            return Response({'detail': 'Неверные учетные данные'}, status=401)
        return Response(serializer.errors, status=400)

class SignOutAPIView(APIView):
    def post(self, request):
        logout(request)
        return Response({'status': 'logged_out'})

    
def signup_page(request):
    return render(request, 'signup.html')

def signin_page(request):
    return render(request, 'signin.html')

def verify_code_page(request):
    return render(request, 'verify_code.html')

def profile_page(request):
    if not request.user.is_authenticated:
        return redirect('users:signin_page')
    return render(request, 'profile.html', {'user': request.user})