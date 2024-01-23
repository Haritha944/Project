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
    path('addwishlist/<int:variant_id>/', views.addwishlist, name='addwishlist'),
    path('removewish/<int:wish_id>', views.removewish, name='removewish'),
    path('addwishcart/<int:wish_id>', views.addwishcart, name='addwishcart'),
    path('get-sales-revenue/', views.get_sales_revenue,
         name='get_sales_revenue'),
]

