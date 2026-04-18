from django import forms
from .models import *
from django.core.exceptions import ValidationError

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('title','category','description','image','stock_units','price')
        exclude = ('seller',)
        widgets = {
            'image': forms.FileInput(attrs={'class': 'product_image'}),
        }
    def clean_image(self):
        image = self.cleaned_data.get('image')
        max_size = 10 * 1024 * 1024
        if image.size >= max_size:
            raise ValidationError('Картинка не может весить больше 10 МБ')
        return image
        
    def clean_price(self):  
        price = self.cleaned_data.get('price')
        if price < 100:
            raise ValidationError('Слишком маленькая стоимость')
        return price
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        special = ['!', '@', '$', "#", '%', '^', '&', '*', '(', ')', '_', '+']
        for char in title:
            if char in special:
                raise forms.ValidationError('Название не может содержать специальные символы (!@#%*)')
        return title
    
