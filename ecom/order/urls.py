from django.urls import path
from . import views

app_name='order'

urlpatterns = [

    
    path('proceed-to-pay/', views.razorpaycheck, name='proceed-to-pay'),
    path('cashdelivery/<str:tracking_no>/', views.cashdelivery, name='cashdelivery'),
   
]