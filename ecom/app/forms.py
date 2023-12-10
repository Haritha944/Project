from django import forms
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django.contrib.auth.models import User


class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username','email','password1','password2')

    username = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder':'Enter your username',
        'class':'w-full py-2 px-5 rounded-xl'
    }),required=True)
    email = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder':'Enter your email',
        'class':'w-full py-2 px-5 rounded-xl'
    }),required=True)
    password1 = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder':'Enter your password',
        'class':'w-full py-2 px-5 rounded-xl'
    }),required=True)
    password2 = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder':'Confirm your password',
        'class':'w-full py-2 px-5 rounded-xl'
    }))
    def clean_password(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long.')
        return password1
    
    def clean_username(self):
       username = self.cleaned_data['username']
       if len(username) < 5:
            raise forms.ValidationError('Username must be at least 5 characters long.')
       if not username.isalnum():
            raise forms.ValidationError('Username must contain only alphanumeric characters.')
       return username
   
class LoginForm(AuthenticationForm):
    
    username = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder':'Enter your username',
        'class':'w-full py-2 px-5 rounded-xl'
    }),required=True)
   
    password = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder':'Enter your password',
        'class':'w-full py-2 px-5 rounded-xl' 
    }))
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long.')
        return password
    def clean_username(self):
       username = self.cleaned_data['username']
       if len(username) < 5:
            raise forms.ValidationError('Username must be at least 5 characters long.')
       if not username.isalnum():
            raise forms.ValidationError('Username must contain only alphanumeric characters.')
       return username
