from django.db import models
from category.models import Category, Sub_Category

# Create your models here.

class Product(models.Model):
    product_name = models.CharField(max_length=200, unique=True)
    images = models.ImageField(upload_to="images/products/",default=None)
    is_available = models.BooleanField(default=True)
    description = models.TextField(max_length=225, blank=True)
    original_price = models.FloatField(default=0)
    discount_price = models.FloatField(default=0)
    stock = models.IntegerField(default=0)
    category= models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory= models.ForeignKey(Sub_Category, on_delete=models.CASCADE)
    is_visible = models.BooleanField(default=True)

    def __str__(self):
        return self.product_name
    
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size=models.CharField(max_length=10)
    color = models.CharField(max_length=50)
    material = models.CharField(max_length=50)
    original_price = models.FloatField(default=0)
    discount_price = models.FloatField(default=0)
    stock = models.IntegerField()
    is_available = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.product.product_name}"
    
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Change related_name
    image = models.ImageField(upload_to='images/product_images/')

    

