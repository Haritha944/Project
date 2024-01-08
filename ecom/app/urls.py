from django.urls import path
from . import views
from .forms import LoginForm
from django.contrib.auth import views as auth_views

app_name='user'

urlpatterns = [
    path('',views.index,name='index'),
    path('about/',views.about,name='about'),
    path('contact/',views.contact,name='contact'),
    path('signup/',views.handlesignup,name='handlesignup'),
    path('signup_otp/', views.signup_otp, name='signup_otp'),
    path('resend_otp_signup', views.ResentOtpSignup, name='resend_otp_signup'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('password_verify/<uidb64>/<token>/', views.password_verify, name='password_verify'),
    path('confirm_password/', views.confirm_password, name='confirm_password'),
    #path('login/',auth_views.LoginView.as_view(template_name='user/login.html',authentication_form=LoginForm),name='handlelogin'),
    path('login/',views.handlelogin,name='handlelogin'),
    path('logout/',views.logout,name='logout'),
    path('search/',views.search,name='search'),



]