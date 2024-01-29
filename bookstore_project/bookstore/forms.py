# bookstore/forms.py

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from .models import User, BookRating, Author, Category

class CatalogueFilterForm(forms.Form):
    search_query = forms.CharField(label='Search', required=False)
    author = forms.ModelChoiceField(queryset=Author.objects.all(), empty_label='All Authors', required=False)
    category = forms.ModelChoiceField(queryset=Category.objects.all(), empty_label='All Categories', required=False)

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')

class LoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ('username', 'password')

class RatingForm(forms.ModelForm):
    class Meta:
        model = BookRating
        fields = ['rating']

class OrderForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    phone_number = forms.CharField(max_length=15)
    email = forms.EmailField()
    address = forms.CharField(widget=forms.Textarea)
    zip_code = forms.CharField(max_length=10)