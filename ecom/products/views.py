from django.shortcuts import render,redirect
from django.core.paginator import Paginator
from .models import Product,ProductVariant,ProductImage
from category.models import Sub_Category,Category
import re
import os
from ecom import settings
from decimal import Decimal
from django.contrib import messages
from django.urls import reverse
from cart.views import _cart_id
from cart.models import CartItem


def home(request):
    products = Product.objects.filter(is_visible=True).order_by('id')
    sub_cat = Sub_Category.objects.filter(is_visible=True).order_by('id')
    cat = Category.objects.filter(is_visible=True)
    products_with_default_variants = Product.objects.prefetch_related('variants').filter(
        variants__is_available=True)
    product_queryset = ProductVariant.objects.none()
    for products in products_with_default_variants:
        default_variant = products.variants.filter(is_available=True).first()
        if default_variant:
            product_queryset |= ProductVariant.objects.filter(pk=default_variant.pk)
            
    context = {
        'products': product_queryset,
        'sub_cat': sub_cat,
        'category': cat,

    }

    return render(request, 'user/index.html', context)



def remove_currency_symbols(input_string):
    # Define a regular expression pattern to match dollar ($) and rupee (₹) symbols
    currency_symbols = r'[$₹]'
    # Use the sub() function from the re module to replace the currency symbols with an empty string
    output_string = re.sub(currency_symbols, '', input_string)
    return output_string

from django.db.models import QuerySet
def viewshop(request):
    if request.method == 'POST':
        minamount = int(remove_currency_symbols(request.POST.get('minamount')))
        maxamount = int(remove_currency_symbols(request.POST.get('maxamount')))
        filter_size=request.POST.get('filter_size')

        if minamount and maxamount and filter_size is not None:
            print("hooo", minamount, maxamount)
            products_within_price_range = ProductVariant.objects.filter(discount_price__gte=minamount,
                                                                        discount_price__lte=maxamount,
                                                                        size=filter_size)
        else:
            products_within_price_range = ProductVariant.objects.filter(discount_price__gte=minamount,
                                                                        discount_price__lte=maxamount)
            if filter_size is None:
                filter_size = 0
        paginator = Paginator(products_within_price_range, 16)
        page_number = request.GET.get('page', 1)
        products_within_price_range = paginator.get_page(page_number)
        sub_cat = Category.objects.filter(is_visible=True)
        context = {
            'products': products_within_price_range,
            'all_products': products_within_price_range,
            'sale_off': products_within_price_range,
            'sub_category': sub_cat,
            'min': minamount,
            'max': maxamount,
            'size': str(filter_size)
        }
        return render(request, 'products/shop.html', context)
    else:
        products_with_default_variants = Product.objects.prefetch_related('variants').filter(
           variants__is_available=True)
        product_queryset = ProductVariant.objects.none()
        for product in products_with_default_variants:
            default_variant = product.variants.filter(is_available=True).first()
            if default_variant:
                product_queryset |= ProductVariant.objects.filter(pk=default_variant.pk)
                

        sub_cat = Category.objects.filter(is_visible=True)
        paginator = Paginator(product_queryset, 16)
        page_number = request.GET.get('page', 1)
        product_queryset = paginator.get_page(page_number)
        context = {
            'products': product_queryset,
            'all_products': product_queryset,
            'sale_off': product_queryset,
            'sorted_product': product_queryset,
            'sub_category': sub_cat,

        }
        return render(request, 'products/shop.html', context)

def singleproductview(request,product_id):
    selected_product = ProductVariant.objects.get(id=product_id)
    product = Product.objects.get(id=selected_product.product.id)
    product_variant = ProductVariant.objects.filter(product=product)
    print(selected_product,product,product_variant)
    cart_id = _cart_id(request)
    in_cart = CartItem.objects.filter(cart__cart_id=cart_id, product=product).exists()
    images = ProductImage.objects.filter(product=product)
    imagesa = ProductImage.objects.filter(product=product).first()
    similar_product = ProductVariant.objects.filter(product__category=product.category)[:4]
    
    like_product=ProductVariant.objects.filter(product__category=product.category,discount_price__lt=4000)[:4]

    # try:
    #     orderproduct = OrderItem.objects.filter(user=request.user,product = product).exists()
    # except OrderItem.DoesNotExist:
    #     orderproduct = None

    # get the review
    
    context = {
        'product': selected_product,
        'variants': product_variant,
        'in_cart': in_cart,
        'images': images,
        # 'orderproduct': orderproduct,
        #'reviews': reviews,
        'similar_product': similar_product,
        'like_product': like_product,
    }
    return render(request, 'products/singleproduct.html', context)


#<!--Admin view product--->
def viewproduct(request):
    products = Product.objects.filter(is_visible=True).order_by('id')
    sub_cat = Sub_Category.objects.filter(is_visible=True).order_by('id')
    paginator = Paginator(products, 3)
    page_number = request.GET.get('page', 1)
    products = paginator.get_page(page_number)
    context = {
        'products': products,
        'sub_cat': sub_cat,

    }
    return render(request,"admin/viewproduct.html",context)
#<!--Admin view product--->


#<!--Admin softdelete product--->

def softdeleteproduct(request, product_id):
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return redirect('/viewproduct/')
    product.soft_deleted = True
    product.is_available = False
    product.save()
    return redirect('/viewproduct/')

def undosoftdeleteproduct(request, product_id):
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return redirect('/viewproduct/')
    product.soft_deleted = False
    product.is_available = True
    product.save()
    return redirect('/viewproduct/')

#<!--Admin add product--->
def addproduct(request):
    url = request.META.get('HTTP_REFERER')
    product = Product()
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        if Product.objects.filter(product_name=product_name).exists():
            messages.warning(request,"Product name already exist..!")
            return redirect(url)
        else:
            product.product_name = request.POST.get('product_name')
       
        product.description = request.POST.get('description')
        subcategory = request.POST.get('category_name')
        sub_cat = Sub_Category.objects.get(id=subcategory)
        product.subcategory = sub_cat
        product.category = sub_cat.category
        product.original_price = request.POST.get('original_price')
        product.discount_price = request.POST.get('discount_price')
        images = request.FILES.getlist('images')
        if images:
            product.images = images[len(images) - 1]

        product.save()   
        return redirect('/viewproduct/')
        

    return render(request, 'admin/viewproduct.html')

#<!--admin edit  ---------------------------------->
def editproduct(request, product_id):
    product = Product.objects.get(id=product_id)
    if request.method == 'POST':
        product.product_name = request.POST.get('product_name')
        product.description = request.POST.get('description')
        subcategory = request.POST.get('category_name')
        sub_cat = Sub_Category.objects.get(id=subcategory)
        product.subcategory = sub_cat
        product.category = sub_cat.category
        img1 = request.FILES.get('img')
        if img1 is None:
            product.images = product.images
        else:
            product.images = request.FILES.get('img')
        # product.stock = request.POST.get('stock')
        product.save()
        variant_size = request.POST.getlist("variant_size[]")
        original_price = request.POST.getlist("variant_original_price[]")
        discount_price = request.POST.getlist("variant_discount_price[]")
        stocks = request.POST.getlist('variant_stock[]')
        for size, original_price, discount_price, stock in zip(variant_size, original_price, discount_price,
                                                                stocks):
            if size and original_price and discount_price and stock:
                variant = ProductVariant()
                variant.product = product
                variant.size = Decimal(size)
                variant.original_price = Decimal(original_price)
                variant.discount_price = Decimal(discount_price)
                variant.stock = stocks
                variant.save()

        return redirect('/viewproduct/')
    return redirect('/viewproduct/')

#<!--admin view variant ---------------------------------->        
def viewvariant(request, variant_id):
    product = Product.objects.get(id=variant_id)
    variants = ProductVariant.objects.filter(product=product).order_by('id')
    context = {
        'variants': variants,
    }

    return render(request, 'admin/viewvariant.html', context)

#<!--admin viewvariant  ---------------------------------->
def addvariant(request):
    variant=ProductVariant()
    if request.method == 'POST':
       #product_id= request.POST.get('variant_product')
       product = request.POST.get('variant_product')
       #product = Product.objects.get(id=product_id)
       
       
       variant.product = product
       print(variant.product)
       variant.size = request.POST.get('variant_size')
       variant.color = request.POST.get('variant_color')
       variant.material = request.POST.get('variant_material')
       variant.original_price = request.POST.get('variant_original_price')
       variant.discount_price = request.POST.get('variant_discount_price')
       variant.stock = request.POST.get('variant_stock')
       variant.save()
       messages.success(request, "Variant added successfully!")
       return redirect('/viewvariant/')
    return render(request, 'admin/viewvariant.html',{'variant': variant})

#<!--admin editvariant  ---------------------------------->
def editvariant(request,variant_id):
    variant=ProductVariant.objects.get(id=variant_id)
    if request.method == "POST":
        variant.size=request.POST.get('variant_size')
        variant.color = request.POST.get('variant_color')
        variant.material = request.POST.get('variant_material')
        variant.original_price = request.POST.get('variant_original_price')
        variant.discount_price = request.POST.get('variant_discount_price')
        variant.stock = request.POST.get('variant_stock')
        variant.save()
        variants=ProductVariant.objects.filter(product=variant.product).order_by('id')
        context={
            'variants': variants,
        }
        return render(request, 'admin/viewvariant.html', context)
    return render(request, 'admin/viewvariant.html')

#<!--admin delvariant  ---------------------------------->
def softdeletevariant(request, variant_id):
    try:
        variant = ProductVariant.objects.get(pk=variant_id)
    except ProductVariant.DoesNotExist:
        return redirect('/viewvariant/')
    variant.soft_deleted = True
    variant.is_available = False
    variant.save()
    return redirect('/viewvariant/')

def undosoftdeletevariant(request, variant_id):
    try:
        variant= ProductVariant.objects.get(pk=variant_id)
    except ProductVariant.DoesNotExist:
        return redirect('/viewvariant/')
    variant.soft_deleted = False
    variant.is_available = True
    variant.save()
    return redirect('/viewvariant/')

#<!--admin viewimage  ---------------------------------->
def viewimage(request,product_id):
    #retrieve all images related to specified product id
    images=ProductImage.objects.filter(product=product_id)
    #retrieve product related to specified product id
    product=Product.objects.filter(id=product_id)
    context={
        'images':images,  #pass the retrieved images,product to the template
        'product':product
    }
    return render(request,'admin/viewimage.html',context)
#<!--admin viewimage  ---------------------------------->


#<!--admin addimage  ---------------------------------->
def addimage(request,product_id):
    product=Product.objects.get(id=product_id)
    if request.method == 'POST':
        images = request.FILES.getlist('img')
        print(product.product_name,images)
        if images:
            for image in images:
                #Create a ProductImage instance for each image
                new_image=ProductImage(product=product,image=image)
                #save the instance
                new_image.save()
    images = ProductImage.objects.filter(product=product_id)
    context={
        'images':images,
        'product':product,
    }
    return render(request,'admin/viewimage.html',context)


#<!--admin deleteimage  ---------------------------------->   
def deleteimage(request,image_id):
    image=ProductImage.objects.get(id=image_id)
    product=Product.objects.get(id=image.product_id)
    try:
        file_path=os.path.join(settings.MEDIA_ROOT,str(image.image))
        image.delete()
        if os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass
    images=ProductImage.objects.filter(product=product)
    context={
        'images':images,
        'product':product
    }
    return render(request,'admin/viewimage.html',context)


