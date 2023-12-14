from django.urls import path
from . import views

app_name='products'

urlpatterns = [
     # admin side
    path('shop/', views.ViewProducts, name='ViewProducts'),
]