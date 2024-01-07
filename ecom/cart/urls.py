from django.urls import path
from . import views

app_name='cart'

urlpatterns = [
    # user side
    path('cart/', views.cart, name='cart'),
    path('addcart/<int:product_id>/', views.addcart, name='addcart'),
    path('removecartitem/<int:product_id>/', views.removecartitem,
         name='removecartitem'),
    path('profile/', views.profile, name='profile'),
    path('address/', views.address, name='address'),
    path('addaddress/', views.addaddress, name='addaddress'),
    path('editaddress/<int:address_id>', views.editaddress, name='editaddress'),
    path('deleteaddress/<int:address_id>', views.deleteaddress, name='deleteaddress'),
    path('checkout/', views.checkout, name='checkout'),
    path('addaddresscheck/', views.addaddresscheck,
         name='addaddresscheck'),
    path('selectedaddress/', views.selectedAddress, name='selectedaddress'),
    path('removecart/<int:product_id>/', views.removecart, name='removecart'),
<<<<<<< HEAD
    path('checkoutorder/', views.checkoutorder, name='checkoutorder'),
    #path('my-order/<str:id>/', views.order, name='my_order'),
    #path('my-order/', views.order, name='my_order'),
    path('placeorder/', views.placeorder, name='placeorder'),
=======
>>>>>>> 8b56765e6bed435d8dfc3a6abdb477c47957515e
    
    

]