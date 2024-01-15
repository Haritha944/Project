from django.contrib import admin
from cart.models import Cart,CartItem,Address,Wishlist,Coupon,UserCoupons
# Register your models here.
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Address)
admin.site.register(Wishlist)
admin.site.register(Coupon)
admin.site.register(UserCoupons)