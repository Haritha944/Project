from django.urls import path
from . import views

app_name='order'

urlpatterns = [

    
    path('proceed-to-pay/', views.razorpaycheck, name='proceed-to-pay'),
    path('cashdelivery/<str:tracking_no>/', views.cashdelivery, name='cashdelivery'),
    path('orderinvoice/<int:order_id>/', views.orderinvoice, name='orderinvoice'),
    path('myorders', views.myorders, name='myorders'),
    path('cancelorder/<int:order_item_id>/', views.cancelorder, name='cancelorder'),
   
]