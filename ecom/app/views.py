from django.shortcuts import render,redirect
from django.views.decorators.cache import never_cache
from math import ceil
from django.db.models import Q
from .forms import SignupForm,LoginForm
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.hashers import make_password
import re
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
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
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from dashboard.models import Referral,UserReferral,ReferralAmount
from order.models import UserWallet
import string
import random




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
    

def generate_referral_code():
    code_length=6
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters,k=code_length))


def handlesignup(request):
    if request.method =='POST':
        name=request.POST["name"]
        email=request.POST["email"]
        mobile = request.POST.get("mobile")
        password1=request.POST["password1"]
        password2=request.POST["password2"]
        referral_code=request.POST.get('referral_code')

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
        referrer = None
        if referral_code:
            try:
                referral_instance = Referral.objects.get(referral_code=referral_code)
                referrer = UserReferral.objects.get(referral__referral_code=referral_instance)
                if referrer.is_used:
                    messages.error(request, 'Referral code has already been used.')
                    return render(request, 'user/signup.html')
            except UserReferral.DoesNotExist:
                messages.error(request, 'Referral code is incorrect.')
                return render(request, 'user/signup.html')

        my_user = User(email=email,name=name,mobile=mobile)
        my_user.set_password(password1)
        my_user.is_active = True
        refer_code = generate_referral_code()
        my_user.save()
        
        referral_instance = Referral.objects.create(user=my_user,referral_code=refer_code)
        user_refer = UserReferral.objects.create(user=my_user,referral=referral_instance,is_used=False)
        user_refer.save()
        referred_amount = ReferralAmount.objects.first()
        if  UserReferral.objects.filter(referral__referral_code=referral_code).exists():
            user_referral = UserReferral.objects.get(referral__referral_code=referral_code)
            referred_user = user_referral.user
            referobj = Referral.objects.get(referral_code=referral_code)
            referobj.user=my_user
            referobj.referred_by=referred_user
            referobj.new_user_amount = referred_amount.new_user_amount
            referobj.referred_user_amount = referred_amount.referred_user_amount
            referobj.save()
            referred_user_wallet = UserWallet.objects.get(user=referred_user)
            referred_user_wallet.amount += referred_amount.referred_user_amount
            referred_user_wallet.save()
            user_wallet = UserWallet.objects.create(user=request.user)
            user_wallet.amount += referred_amount.new_user_amount
            user_wallet.save()
            referred_user.is_used = True
            referred_user.save()
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
@never_cache
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


def forgot_password(request):
    try:
        if request.method == 'POST':
            email= request.POST.get('email')
            if User.objects.filter(email=email).exists():
                user = User.objects.get(email__exact=email)

                current_site = get_current_site(request)
                mail_subject = "Reset Your Password"
                message = render_to_string('user/password_verify.html',{
                    'user': user,
                    'domain': current_site,
                    'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                })
                to_email = email
                send_email  = EmailMessage(mail_subject, message, to=[to_email])
                send_email.send()

                messages.success(request,"Password reset email has been sent to your email address ")
                return redirect('user:handlelogin')

            else:
                messages.warning(request, 'Account does not exist!')
                return redirect('/forgot_password/')        
            
    except Exception as e:
        print(e)
    return render(request, "user/forgot_password.html")

def password_verify(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please Reset your Password!!')
        return redirect('user:confirm_password')
    else:
        messages.warning(request, 'Link has been expired')
        return redirect('user:handlelogin')



def confirm_password(request):
    if request.method == "POST":
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        if not (password and confirm_password):
                raise ValueError("Password fields are empty")


        if password == confirm_password:
            uid = request.session.get('uid')
            user = User.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset Successfull')
            return redirect('user:handlelogin')

        else:
            messages.warning(request, 'Passwords do not match')
            return redirect("user:confirm_password")
    else:
        return render(request, 'user/confirm_password.html')

def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = ProductVariant.objects.filter(Q(is_available=True) &
                                                     Q(Q(product__description__icontains=keyword) |
                                                       Q(product__product_name__icontains=keyword)))
   
    sub_cat = Category.objects.all()

    context = {
        'products': products,
        'sub_category': sub_cat,

    }
    return render(request,'user/index.html',context)

