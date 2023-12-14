# from django.shortcuts import render
# from django.db.models import QuerySet
# from .models import Product
# from category.models import Sub_Category,Category
# import re

# def ViewProducts(request):
#     products = Product.objects.filter(is_visible=True).order_by('id')
#     #sub_cat = Sub_Category.objects.filter(is_visible=True).order_by('id')
#     context = {
#         'products': products,
#        #'sub_cat': sub_cat,

#     }

#     return render(request, 'product/shop.html', context)



# def remove_currency_symbols(input_string):
#     # Define a regular expression pattern to match dollar ($) and rupee (₹) symbols
#     currency_symbols = r'[$₹]'
#     # Use the sub() function from the re module to replace the currency symbols with an empty string
#     output_string = re.sub(currency_symbols, '', input_string)
#     return output_string







