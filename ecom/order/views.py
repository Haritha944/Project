from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from cart.models import Cart,CartItem,Address
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from user.models import User
from order.models import Order,OrderItem,Payment
from products.models import Product,ProductVariant
from django.db import transaction
# Create your views here.

def _cart_id(request):
    cart=request.session.session_key
    if not cart:
        cart=request.session.create()
    return cart
       
def razorpaycheck(request):
    email = request.user
    user = User.objects.get(email=email)
    cart = CartItem.objects.filter(user_id=user.id)
    total_price = 0
    for item in cart:
        total_price = total_price + item.variant.discount_price * item.quantity
    try:
        if request.session['coupon']:
            offer = request.session['coupon']
            total_price = total_price - offer
    except:
        pass
    return JsonResponse({
        'total_price': total_price
    })
@transaction.atomic
def cashdelivery(request,tracking_no):
    user=request.user
    try:
        order=Order.objects.get(user=user,tracking_no=tracking_no)
    except Order.DoesNotExist:
        return redirect('order:orderconfirm')
    total_amount= order.total_price
    payment=Payment.objects.create(user=user,payment_method="Cash On Delivery",amount_paid=total_amount,status="Not Paid")
    payment.save()
    order.payment=payment
    order.save()
    
    cart_id = _cart_id(request)
    cart = Cart.objects.get(cart_id=cart_id)
    cart_items = CartItem.objects.filter(cart=cart,is_active=True).order_by('id')
    
    
    for cart_item in cart_items:
        variant=cart_item.variant
        stock=variant.stock-cart_item.quantity
        variant.product.quantity = stock
        variant.product.save()
        order_product = OrderItem.objects.create(
            order=order,
            user=user,
            product=cart_item.product,
            variant=cart_item.variant,
            quantity=cart_item.quantity,
            price=cart_item.variant.discount_price,
            
        )
        order_product.save()
    
    cart_items.delete()
    
    context = {'order': order}

    return render(request, 'order/orderconfirm.html', context)

        
  
    

   