from django.urls import path
from . import views

app_name='order'

urlpatterns = [

    
    path('confirmrazorpayment/<str:tracking_no>/', views.confirmrazorpayment, name='confirmrazorpayment'),
    path('cashdelivery/<str:tracking_no>/', views.cashdelivery, name='cashdelivery'),
    path('orderinvoice/<int:order_id>/', views.orderinvoice, name='orderinvoice'),
     path('myorder', views.myorder, name='myorder'),
    path('myorderdetail/<int:order_id>/', views.myorderdetail, name='myorderdetail'),
    path('returnorder/<int:order_item_id>/', views.returnorder, name='returnorder'),
    path('cancelorder/<int:order_item_id>/', views.cancelorder, name='cancelorder'),
   #admin
    path('vieworder/', views.vieworder, name='vieworder'),
    path('viewsingleadmin/<int:order_id>', views.viewsingleadmin, name='viewsingleadmin'),
    path('updatestatus/<int:order_id>/<str:new_status>/', views.updatestatus, name='updatestatus'),
]