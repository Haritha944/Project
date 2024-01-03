from django.urls import path
from . import views

app_name='category'

urlpatterns = [
    #admin side
    #subcategory
    path('viewsubcategory/', views.viewsubcategory, name='viewsubcategory'),
    path('subunlist/<int:subcat_id>/', views.subunlist, name="subunlist"),
    path('addsubcategory/', views.addsubcategory, name='addsubcategory'),
    path('editsubcategory/<int:subcat_id>/', views.editsubcategory, name="editsubcategory"),
    #category
    path('viewcategory/', views.viewcategory, name='viewcategory'),
    path('catunlist/<int:cat_id>/', views.catunlist, name="catunlist"),
    path('addcategory/', views.addcategory, name='addcategory'),
    path('editcategory/<int:category_id>/', views.editcategory, name="editcategory"),


    # user side
    path('showcategoryproduct/<int:cat_id>/', views.showcategoryproduct, name="showcategoryproduct"),
    
]