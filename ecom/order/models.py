from django.db import models
from user.models import User
from cart.models import Address
from products.models import Product,ProductVariant
# Create your models here.

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=100)
    amount_paid = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    discount = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_method
    
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    total_price = models.FloatField(null=False)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    message = models.TextField(null=True)
    tracking_no = models.CharField(max_length=150, null=True)
    orderstatuses = (
        ('Order confirmed', 'Order confirmed'),
        ('Shipped', 'Shipped'),
        ('Out for delivery', 'Out for delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Return requested', 'Return requested'),
        ('Return processing', 'Return processing'),
        ('Returned', 'Returned'),
    )
    status = models.CharField(max_length=150, choices=orderstatuses, default='Order confirmed')
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.tracking_no)
    
class OrderItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    price = models.FloatField(null=False)
    quantity = models.IntegerField(null=False)
    STATUS = (
        ('Order confirmed', 'Order confirmed'),
        ('Shipped', 'Shipped'),
        ('Out for delivery', 'Out for delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Return requested', 'Return requested'),
        ('Return processing', 'Return processing'),
        ('Returned', 'Returned'),
    )
    status = models.CharField(max_length=150, choices=STATUS, default='Order Confirmed')

    def _str_(self):
        return f"{self.order.id, self.order.tracking_no}"
