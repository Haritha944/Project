from django.urls import path
from . import views

app_name = 'dashboard' 

urlpatterns = [
    path('adminlogin/', views.adminlogin, name="adminlogin"),
    path('admindash/', views.admindashboard, name="admindashboard"),
    path('adminlogout/', views.adminlogout, name='adminlogout'),
    path('usersdetails/', views.usersdetails, name="usersdetails"),
    path('userblock/<int:user_id>/', views.userblock, name="userblock"),
    path('wishlist/', views.wishlist, name="wishlist"),
]
