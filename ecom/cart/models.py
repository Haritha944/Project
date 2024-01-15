from django.db import models
from user.models import User
from products.models import Product,ProductVariant

# Create your models here.
class Cart(models.Model):
    cart_id=models.CharField(max_length=250,blank=True)
    date=models.DateField(auto_now_add=True)

    def __str__(self):
        return self.cart_id
    
class CartItem(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,null=True)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    variant=models.ForeignKey(ProductVariant,on_delete=models.CASCADE,blank=True)
    cart=models.ForeignKey(Cart,on_delete=models.CASCADE,null=True)
    quantity=models.IntegerField()
    is_active=models.BooleanField(default=True)

    def sub_total(self):
        return self.variant.discount_price * self.quantity
    def __str__(self):
        return self.product.product_name
    
class Address(models.Model):
    user_id = models.ForeignKey(User,on_delete=models.CASCADE)
    house_no = models.IntegerField()
    mobile = models.CharField(max_length=15,null=False)
    email= models.EmailField()
    recipient_name=models.CharField(max_length=100)
    street_name=models.CharField(max_length=50)
    village_name=models.CharField(max_length=50)
    postal_code = models.IntegerField()
    district=models.CharField(max_length=50)
    state=models.CharField(max_length=50)
    country=models.CharField(max_length=50)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return "{}-{}".format(self.recipient_name, self.user_id.name)

class Wishlist(models.Model):
    user = models.ForeignKey(User,  on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class Coupon(models.Model):
    coupon_name=models.CharField(max_length=20)
    coupon_code=models.CharField(max_length=20)
    min_purchase=models.FloatField()
    coupon_discount=models.FloatField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.coupon_name
class UserCoupons(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    is_used = models.BooleanField(default=True)

    def __str__(self):
        return self.coupon.coupon_code