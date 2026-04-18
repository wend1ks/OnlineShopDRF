from django import forms
from .models import *
from django.core.exceptions import ValidationError


class SignUpForm(forms.ModelForm):
    password1 = forms.CharField(
        required=True, 
        label='Пароль', 
        widget=forms.PasswordInput(attrs={'class': 'input-field'})
    )

    password2 = forms.CharField(
        required=True, 
        label='Повторите пароль',
        widget=forms.PasswordInput(attrs={'class': 'input-field'})
    )

    class Meta:
        model = CustomUser
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'user_image', 'phone_number', 'password1',
            'password2', 'role'
        )
        
        widgets = {
            'username': forms.TextInput(attrs={'class': 'input-field'}),
            'first_name': forms.TextInput(attrs={'class': 'input-field'}),
            'last_name': forms.TextInput(attrs={'class': 'input-field'}),
            'email': forms.EmailInput(attrs={'class': 'input-field'}),
            'phone_number': forms.TextInput(attrs={'class': 'input-field'}),
            'role': forms.Select(attrs={'class': 'input-field'}),
            'user_image': forms.ClearableFileInput(attrs={'class': 'file-input'}),
        }


    def clean(self):
        cleaned = super().clean()
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 != password2:
            return ValidationError("Пароли не совпадают")
        return cleaned
    
    # def clean_username(self):
    #     username = self.cleaned_data.get('username')
    #     if username ...:
    #         ...
    #     return username

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password1")
        if password:
            user.set_password(password)
        if commit:
            user.save()
            if user.role == "seller":
                Seller.objects.create(user=user)
        return user

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args,**kwargs)
    #     for name, field in self.fields.items():
    #         field.widget.attrs['class'] = 'НАЗВАНИЕ ВАШЕГО КЛАССА'

class SignInForm(forms.Form):
    username = forms.CharField(
        max_length=15,
        required=True,
        label='Имя пользоветля'
    )
    password = forms.CharField(max_length=150, required=True, label='Пароль')

class ChangeUserForm(forms.ModelForm):
    password1 = forms.CharField(
        required=False,
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={'class': 'input-field'})
    )
    password2 = forms.CharField(
        required=False,
        label='Повторите пароль',
        widget=forms.PasswordInput(attrs={'class': 'input-field'})
    )

    class Meta:
        model = CustomUser
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'user_image', 'phone_number', 'password1', 'password2', 'role'
        )
        widgets = {
            'username': forms.TextInput(attrs={'class': 'input-field'}),
            'first_name': forms.TextInput(attrs={'class': 'input-field'}),
            'last_name': forms.TextInput(attrs={'class': 'input-field'}),
            'email': forms.EmailInput(attrs={'class': 'input-field'}),
            'phone_number': forms.TextInput(attrs={'class': 'input-field'}),
            'role': forms.Select(attrs={'class': 'input-field'}),
            'user_image': forms.FileInput(attrs={'class': 'file-input'}),
        }

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')

        if p1 or p2:
            if p1 != p2:
                raise ValidationError("Пароли не совпадают")

        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password1")

        if password:
            user.set_password(password)

        if commit:
            user.save()

        return user

    
class ActivationCodeForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'readonly': 'readonly'}))
    code = forms.CharField(max_length=4, min_length=4, label='Код (4 цифры)')
