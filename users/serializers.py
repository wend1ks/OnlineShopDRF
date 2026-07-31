from rest_framework import serializers
from .models import CustomUser, Seller, ActivationCode
from rest_framework import serializers
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from .models import CustomUser, Seller, ActivationCode

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(choices=CustomUser.USER_ROLES)

    class Meta:
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", 
                 "phone_number", "user_image", "role", "password", "password2")

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop("password")
        

        user = CustomUser.objects.create(**validated_data)
        user.set_password(password)
        user.is_active = False
        user.save()

        
        if user.role == "seller":
            Seller.objects.get_or_create(user=user)

        return user



class UserProfileUpdateSerializer(serializers.ModelSerializer):
    permission_classes = [IsAuthenticated]
    class Meta:
        model = CustomUser
        fields = (
            'username',
            'first_name',
            'last_name',
            'phone_number',
            'user_image',
        )
        read_only_fields = ('email', 'role')

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False, min_length=8)
    
    class Meta:
        model = CustomUser
        fields = (
            "username",
            "first_name",
            "last_name",
            "phone_number",
            "user_image",
            "current_password",
            "new_password"
        )
    
    def validate(self, data):
        new_password = data.get('new_password')
        current_password = data.get('current_password')
        
        if new_password and not current_password:
            raise serializers.ValidationError({
                "current_password": "Enter your current password to change it."
            })
        
        return data
    
    def update(self, instance, validated_data):
        current_password = validated_data.pop('current_password', None)
        new_password = validated_data.pop('new_password', None)
        
        if new_password and current_password:
            if not instance.check_password(current_password):
                raise serializers.ValidationError({
                    "current_password": "Incorrect current password."
                })
            instance.set_password(new_password)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class ActivationCodeCheckSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=4, max_length=4)


class SignInSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class SimpleUserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = (
            "username",
            "first_name",
            "last_name",
            "phone_number",
            "user_image",
        )   

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def validate(self, data):
        if data.get('new_password') or data.get('current_password'):
            if not data.get('current_password'):
                raise serializers.ValidationError({
                    "current_password": "Current password is required to change your password."
                })
            
            if not data.get('new_password'):
                raise serializers.ValidationError({
                    "new_password": "New password is required."
                })
            
            if data.get('new_password') != data.get('confirm_password'):
                raise serializers.ValidationError({
                    "confirm_password": "Passwords do not match."
                })
        
        return data

    def update(self, instance, validated_data):
        current_password = validated_data.pop('current_password', None)
        new_password = validated_data.pop('new_password', None)
        validated_data.pop('confirm_password', None)
        
        if current_password and new_password:
            if not instance.check_password(current_password):
                raise serializers.ValidationError({
                    "current_password": "Incorrect current password."
                })
            
            instance.set_password(new_password)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance
