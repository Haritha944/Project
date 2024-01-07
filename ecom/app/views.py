from django.shortcuts import render,redirect
from django.views.decorators.cache import never_cache
from math import ceil
from .forms import SignupForm,LoginForm
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.hashers import make_password
import re
#from app.models import Profile
from user.models import User
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate,login
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from .utils import send_otp,send_forget_password_mail
from datetime import datetime
import pyotp
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from products.models import Product,ProductVariant
from category.models import Category,Sub_Category




# Create your views here.
@cache_control(no_cache=True, must_revalidate=True,no_store=True)  
def index(request):
    cat = Category.objects.filter(is_visible=True)
    sub_cat = Sub_Category.objects.filter(is_visible=True)
    products =Product.objects.filter(is_visible=True)
    products_with_default_variants = Product.objects.prefetch_related('variants').filter(
        variants__is_available=True)
    product_queryset = ProductVariant.objects.none()
    for products in products_with_default_variants:
        default_variant = products.variants.filter(is_available=True).first()
        if default_variant:
            product_queryset |= ProductVariant.objects.filter(pk=default_variant.pk)
            

    context = {
        'category': cat,
        'sub_category': sub_cat,
        'products':  product_queryset,
        
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
        if len(password) >= 8:
            return True
        else:
            return False
    
    except ValidationError:
        return False

def validate_name(value):
    if not re.match(r'^[a-zA-Z\s]*$', value):
        return 'Name should only contain alphabets and spaces'
    elif len(value) < 5:
        return 'Username must be atleast 5 characters long'
    elif value.strip() == '':
        return 'Name field cannot be empty or contain only spaces'
    elif User.objects.filter(name=value).exists():
        return('Username already exist')
        
    else:
        return None

def handlesignup(request):
    if request.method =='POST':
       name=request.POST["name"]
       email=request.POST["email"]
       mobile = request.POST.get("mobile")
       password1=request.POST["password1"]
       password2=request.POST["password2"]

       check=[name,email,password1,password2,mobile]
       for value in check:
            if not value:
                context = {
                    'pre_name': name,
                    'pre_email': email,
                    'pre_mobile': mobile,
                }
                messages.info(request, 'Some fields are empty')
                return render(request, 'user/signup.html', context)
       # validate username   
       result = validate_name(name)
       if result is not None:
           context = {
                'pre_name': name,
                'pre_mobile': mobile,
                'pre_email': email,
                 }
           messages.warning(request, result) 
           return render(request, 'user/signup.html', context)
         # validate email   
     
       if not validateEmail(email) :
           context = {
                'pre_name': name,
                'pre_mobile': mobile,
                'pre_email': email,
                 }
           messages.info(request,'Enter valid email')
           return render(request, 'user/signup.html', context)
         # validate password
     
       if not ValidatePassword(password1) :
            context = {
                'pre_name': name,
                'pre_email': email,
                'pre_mobile': mobile,
            }
            messages.warning(request, 'Passwords must be at least 8 characters long.')
            return render(request, 'user/signup.html', context)
           
           
        # Check if the email already exists in the User model
       if User.objects.filter(email=email).exists():
            context = {
                'pre_name': name,
                'pre_email': email,
                'pre_mobile': mobile,
            }
            messages.error(request, 'Email already exists')
            return render(request, 'user/signup.html', context)
       if password1!=password2 :
           context = {
                'pre_name': name,
                'pre_email': email,
                'pre_mobile': mobile,
                 }
           messages.error(request, 'Passwords do not match')
           return render(request, 'user/signup.html', context)

       my_user = User(email=email, password=password1,name=name,mobile=mobile)
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
    if request.method =="POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        #hashed_password = make_password(password)
        #print(hashed_password)
        user = authenticate(request, email=email, password=password)
        print(user)
        if user is not None:
            if not user.is_superuser and user.is_active:
                print(email)
                login(request, user)
                return redirect('user:index')
        else:
            try:
                user = User.objects.get(email=email)
                if user.is_active is False:
                    messages.error(request, 'User is Blocked..!')
                else:
                    messages.error(request, 'Email or password is incorrect')

            except User.DoesNotExist:
                messages.error(request, 'Email or password is incorrect')
            print("Login failed")
            return redirect('user:handlelogin')
            
    return render(request, 'user/login.html')     
 

   


        
       


        
@cache_control(no_cache=True, must_revalidate=True,no_store=True)      
@never_cache
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
            email= request.POST.get('email')
            if not User.objects.filter(email=email).first():
                messages.error(request,'No user with this email')
                return redirect('/forgot_password/')
            user_obj=User.objects.get(email=email)
            token=str(uuid.uuid4())
           # profile_obj=Profile.objects.get(pk=1)
           # profile_obj.forget_password_token = token
            print(token)
           # profile_obj.save()
            send_forget_password_mail(user_obj,token)
            messages.success(request,'An email sended')
            return redirect('/forgot_password/')        
            
    except Exception as e:
        print(e)
    return render(request, "user/forgot_password.html")


def confirm_password(request, token):
    context = {'user_id': None}
    try:
        #profile_obj = Profile.objects.filter(forget_password_token = token).first()
        print(token)
        
        
        #context= {'user_id' : profile_obj.user.id} 
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            reconfirm_password = request.POST.get('reconfirm_password')
            user_id= request.POST.get('user_id')
            print(user_id)
            
            if user_id is None:
                messages.warning(request,'No user found')
                return redirect(f'/confirm_password/{token}/')     
            if new_password != reconfirm_password:
                messages.warning(request, 'Passwords do not match')
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