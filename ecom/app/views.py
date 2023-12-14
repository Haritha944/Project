from django.shortcuts import render,redirect
from math import ceil
from .forms import SignupForm,LoginForm
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.models import User
import re
from app.models import Profile
from django.contrib.auth import login,authenticate
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from .utils import send_otp,send_forget_password_mail
from datetime import datetime
import pyotp
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from products.models import Product
from category.models import Category,Sub_Category



# Create your views here.
def index(request):
    #cat = Category.objects.filter(is_visible=True)
    #sub_cat = Sub_Category.objects.filter(is_visible=True)
    products =Product.objects.filter(is_visible=True)
    context = {
        #'category': cat,
        #'sub_category': sub_cat,
        'products': products,
        
          }
  
    return render(request,'user/index.html',context)
def about(request):
    return render(request,'user/about.html')
def contact(request):
    return render(request,'user/contact.html')

def validateEmail(email):
    
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False
def ValidatePassword(password):
    from django.contrib.auth.password_validation import validate_password
    try:
        validate_password(password)
        return True
    except ValidationError:
        return False

def validate_name(value):
    if not re.match(r'^[a-zA-Z\s]*$', value):
        return 'Name should only contain alphabets and spaces'

    elif value.strip() == '':
        return 'Name field cannot be empty or contain only spaces'
    elif User.objects.filter(username=value).exists():
        return 'Username already exist'
    else:
        return False

def handlesignup(request):
    if request.method =='POST':
       username=request.POST["username"]
       email=request.POST["email"]
       password1=request.POST["password1"]
       password2=request.POST["password2"]

       check=[username,email,password1,password2]
       for value in check:
            if not value:
                context = {
                    'pre_username': username,
                    'pre_email': email,
                }
                messages.info(request, 'Some fields are empty')
                return render(request, 'user/signup.html', context)
       # validate username   
       result = validate_name(username)
       if result is not False:
           context = {
                'pre_username': username,
              
                'pre_email': email,
                 }
           messages.info(request, result)
           return render(request, 'user/user_register.html', context)
         # validate email   
     
       if not validateEmail(email) :
           context = {
                'pre_username': username,
              
                'pre_email': email,
                 }
           messages.info(request,'Enter valid email')
           return render(request, 'user/user_register.html', context)
         # validate password
     
       if not ValidatePassword(password1) :
            context = {
                'pre_username': username,
                'pre_email': email,
            }
            messages.warning(request, 'Enter a strong password')
            return render(request, 'user/user_register.html', context)
           
           
        # Check if the email already exists in the User model
       if User.objects.filter(email=email).exists():
            context = {
                'pre_username': username,
                'pre_email': email,
            }
            messages.error(request, 'Email already exists')
            return render(request, 'user/signup.html', context)
       if password1!=password2 :
           context = {
                'pre_username': username,
                'pre_email': email,
                 }
           messages.error(request, 'Passwords do not match')
           return render(request, 'user/signup.html', context)

       my_user = User(email=email, password=password1,username=username)
       my_user.save()
       send_otp(request, email)
       return redirect('/signup_otp/')

    return render(request, 'user/signup.html')

def signup_otp(request):
    email = request.session.get('email')

    if request.method =='POST':
        otp = ''
        otp += request.POST.get('otp1')
        otp += request.POST.get('otp2')
        otp += request.POST.get('otp3')
        otp += request.POST.get('otp4')
        otp += request.POST.get('otp5')
        otp += request.POST.get('otp6')
        otp_secret_key = request.session['otp_secret_key']
        otp_valid_date = request.session['otp_valid_date']
        if otp_secret_key and otp_valid_date is not None:
            validate_until = datetime.fromisoformat(otp_valid_date)
            if validate_until > datetime.now():
                totp = pyotp.TOTP(otp_secret_key, interval=120)
                user = User.objects.get(email=email)
                if int(otp) == int(totp.now()):
                    user.authenticated = True
                    user.otp = 0
                    user.save()
                    del request.session['otp_secret_key']
                    del request.session['otp_valid_date']
                    del request.session['email']
                    messages.success(request, 'Created a new account. Please login !')
                    return render(request, 'user/login.html')
                else:
                    messages.error(request, 'Please enter proper OTP .')
            else:
                messages.error(request, 'OTP expired.')
                del request.session['otp_secret_key']
                del request.session['otp_valid_date']
                del request.session['email']
        else:
            del request.session['otp_secret_key']
            del request.session['otp_valid_date']
            del request.session['email']
            return redirect('handlelogin')
       
       
    return render(request,'user/otp_signup.html')   
       
    
@cache_control(no_cache=True, must_revalidate=True,no_store=True)
def handlelogin(request):
    if request.method =='POST':
        uname=request.POST.get('username')
        pass1=request.POST.get('password')
        user=authenticate(request,username=uname,password=pass1)
        if user is not None:
            if user.is_active is True and user.is_superuser is False:
                if user.is_authenticated == True:
                   login(request,user)
                   messages.success(request,'Login sucessfully')
                   return redirect('/index/')
        else:
            messages.error(request,'Invalid Credientials')
            return redirect('/login/')
    return render(request,'user/login.html')



def logout(request):
    request.session.flush()
    request.session['logged_out'] = True
    messages.info(request,'Logout Success')
    return redirect('/login/')

def ResentOtpSignup(request):
    try:
        if 'otp_secret_key' in request.session:
            del request.session['otp_secret_key']
        if 'otp_valid_date' in request.session:
            del request.session['otp_valid_date']

            email = request.session['email']
            send_otp(request, email)
        return redirect('/signup_otp/')
    except Exception as e:
        print(e)

import uuid
def forgot_password(request):
    try:
        if request.method == 'POST':
            username= request.POST.get('username')
            if not User.objects.filter(username=username).first():
                messages.error(request,'No user with this username')
                return redirect('/forgot_password/')
            user_obj=User.objects.get(username=username)
            token=str(uuid.uuid4())
            profile_obj=Profile.objects.get(pk=1)
            profile_obj.forget_password_token = token
            profile_obj.save()
            send_forget_password_mail(user_obj.email,token)
            messages.success(request,'An email sended')
            return redirect('/forgot_password/')        
            
    except Exception as e:
        print(e)
    return render(request, "user/forgot_password.html")


def confirm_password(request, token):
    context = {'user_id': None}
    try:
        profile_obj = Profile.objects.filter(forget_password_token = token).first()
        
        
        context= {'user_id' : profile_obj.user.id} 
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            reconfirm_password = request.POST.get('reconfirm_password')
            user_id = request.POST.get('user_id')
            if user_id is None:
                messages.error(request,'No user found')
                return redirect(f'/confirm_password/{token}/')     
            if new_password != reconfirm_password:
                messages.error(request, 'Passwords do not match')
                return redirect(f'/confirm_password/{token}/') 
            
            
            user_obj=User.objects.get(id=user_id)
            user_obj.set_password(new_password)
            user_obj.save()
            messages.success(request, 'Password updated successfully')
            return redirect('/login/')
   
    except Exception as e:
        print(e)

    return render(request, 'user/confirm_password.html', context)

   
def search(request):
    product_objects=Product.objects.all()
    keyword= request.GET.get('item_name')
    if keyword !='' and keyword is not None:
         product_objects = product_objects.filter(title__icontains=keyword)
    return render(request,'user/index.html',{'product_objects':product_objects})