import pyotp
from datetime import datetime, timedelta
from django.db.models.signals import Signal
from ecom import settings  # Importing settings.py from a package
from django.conf import settings
# Access variables or configurations defined in settings.py
# piExample usage: accessing a variable from settings.py
from django.dispatch import receiver
from django.core.mail import send_mail
import threading
from threading import local
from app.middleware import request_local
from user.models import User
otp_generated = Signal()

# @receiver(otp_generated)

def send_otp(request,email):
# def send_otp(sender, **kwargs):

    # request = request_local.request
    # email = kwargs.get('email')
    totp = pyotp.TOTP(pyotp.random_base32(), interval=120)
    otp = totp.now()
    request.session['otp_secret_key'] = totp.secret
    valid_date = datetime.now() + timedelta(minutes=2)
    request.session['otp_valid_date'] = str(valid_date)
    subject = f"Hello, {email}!"
    message = "OTP verification"
    from_email = "trendyfoot.official@gmail.com"
    htmlgen = f"""
    <div style="font-family: Helvetica,Arial,sans-serif;min-width:1000px;overflow:auto;line-height:2">
    <div style="margin:50px auto;width:70%;padding:20px 0">
    <div style="border-bottom:1px solid #eee">
      <a href="" style="font-size:1.4em;color: #00466a;text-decoration:none;font-weight:600">TrendyFoot</a>
    </div>
    <p style="font-size:1.1em">Hi,</p>
    <p>Thank you for choosing TrendyFoot. Use the following OTP to complete your Sign In procedures. OTP is valid for 1 minutes</p>
    <h2 style="background: #00466a;margin: 0 auto;width: max-content;padding: 0 10px;color: #fff;border-radius: 4px;">{otp}</h2>
    <p style="font-size:0.9em;">Regards,<br />TrendyFoot</p>
    <hr style="border:none;border-top:1px solid #eee" />
    <div style="float:right;padding:8px 0;color:#aaa;font-size:0.8em;line-height:1;font-weight:300">
      <p>TrendyFoot</p>
      <p>contact : 0000000000</p>
      <p>Email : trendyfoot.official@gmail.com</p>
    </div>
    </div>
    </div>
    """
    
    send_mail(subject, message, from_email, [email], fail_silently=False, html_message=htmlgen)
    request.session['email'] = email
    user = User.objects.get(email=email)
    user.otp = otp
    user.save()


def send_forget_password_mail(email,token):
    
    subject="Your forget password link"
    message=f'Hi,click on the link to reset your password http://127.0.0.1:8000/confirm_password/{token}/'
    from_email = "trendyfoot.official@gmail.com"
    recipient_list=[email]
    send_mail(subject,message,from_email,recipient_list,fail_silently=False)
    return True