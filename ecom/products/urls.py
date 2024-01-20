from django.urls import path
from . import views

app_name='products'

urlpatterns = [
     # user side
    path('home/', views.home, name='home'),
    path('viewshop/', views.viewshop, name='viewshop'),
    path('singleproduct/<int:product_id>/', views.singleproductview, name="singleproductview"),
     #admin side
    path('viewproduct/', views.viewproduct, name='viewproduct'),
    path('addproduct/', views.addproduct, name='addproduct'),
    path('softdeleteproduct/<int:product_id>/', views.softdeleteproduct, name='softdeleteproduct'),
    path('undosoftdeleteproduct/<int:product_id>/', views.undosoftdeleteproduct, name='undosoftdeleteproduct'),
    path('editproduct/<int:product_id>', views.editproduct, name='editproduct'),
    path('viewvariant/<int:variant_id>', views.viewvariant, name="viewvariant"),
    path('addvariant/', views.addvariant, name='addvariant'),
    path('editvariant/<int:variant_id>', views.editvariant, name="editvariant"),
    path('softdeletevariant/<int:variant_id>/', views.softdeletevariant, name='softdeletevariant'),
    path('undosoftdeletevariant/<int:variant_id>/', views.undosoftdeletevariant, name='undosoftdeletevariant'),
    path('viewimage/<int:product_id>', views.viewimage, name='viewimage'),
    path('addimage/<int:product_id>', views.addimage, name='addimage'),
    path('deleteimage/<int:image_id>', views.deleteimage, name='deleteimage'),
     path('searchadmin/', views.searchadmin, name='searchadmin'),
]