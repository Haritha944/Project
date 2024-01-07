from django.contrib import admin
from products.models import Product,ProductVariant,ProductImage
# Register your models here.
admin.site.register(Product)
admin.site.register(ProductVariant)
admin.site.register(ProductImage)