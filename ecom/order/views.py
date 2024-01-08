from django.shortcuts import render,redirect, get_object_or_404
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

    return render(request, 'order/cashdelivery.html', context)


def orderinvoice(request,order_id):
    user = request.user
    order = Order.objects.get(id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    payment = Payment.objects.get(order=order)
    #cart_id = _cart_id(request)
    #cart = Cart.objects.get(cart_id=cart_id)
   #cart_items = CartItem.objects.filter(cart=cart,is_active=True).order_by('id')
    cart_items = CartItem.objects.filter(user=user)
    total = 0
    tax = 0
    shipping = 0
    grand_total = 0
    subtotal = 0 
    for order_item in order_items:
        order_item_total = order_item.variant.discount_price * order_item.quantity
        total = order_item_total  
        subtotal += order_item_total
        tax = (2 * subtotal) / 100
        

        grand_total = subtotal + tax 

        context = {
            'order': order,
            'order_items': order_items,
            'payment': payment,
            'grand_total': grand_total,
            'cart_items': cart_items,
            'total': total,
            'tax':tax,
            'subtotal': subtotal,
        }
    return render(request, 'order/orderconfirm.html', context)
        
def myorders(request):
    user=request.user  
    print(user)
    email = request.user
    user = User.objects.get(email=email)
    if request.method == "POST":
        status=request.POST.get('status')
        order = Order.objects.filter(user=user)
        if status == 'status' or status == 'all':
            order_items = OrderItem.objects.filter(user=user).order_by('-id')
        else:
            print(status)
            order_items = OrderItem.objects.filter(user=user,status=status).order_by('-id')
            order_items1 = OrderItem.objects.filter(user=user, status='Cancelled').values()
            print(order_items1)
        context = {
            "order": order,
            "order_items": order_items
        }
    else:
        order = Order.objects.filter(user=user)
        order_items = OrderItem.objects.filter(user=user).order_by('-id')
        context = {
            "order": order,
            "order_items": order_items
        }
    
    
    return render(request, 'userprofile/order.html', context)

def cancelorder(request,order_item_id):
    order_item = OrderItem.objects.get(id=order_item_id)
    order = Order.objects.get(id=order_item.order.id)
    if order is not None:
        order.status = 'Cancelled'
        order.save()
        order_items = OrderItem.objects.filter(order=order)
        print(order.payment.payment_method)
        for item in order_items:
            reason = request.POST.get('cancel')
            item.status = 'Cancelled'
            item.save()
        return redirect('order:myorders')    
    else:
        pass    

#<!---------admin---------->  
def vieworder(request):
    if request.method=="POST":
        status=request.POST.get('status')
        print(status)
        if status == 'status' or status == 'all':
            orders = Order.objects.all().order_by('-id')
        else:
            orders = Order.objects.filter(status=status).order_by('-id')
        context = {
            'orders': orders
        }
        return render(request, 'admin/vieworder.html', context)
    else:
        orders = Order.objects.all().order_by('-id')
        context = {
            "orders": orders,
            
        }
        return render(request, 'admin/vieworder.html', context)
def viewsingleadmin(request, order_id):
    order = Order.objects.get(id=order_id)
    order_item = OrderItem.objects.filter(order=order)
    user=User.objects.get(id=order.user.id)
    payments = Payment.objects.filter(order__id=order_id)
    # user.wallet = user.wallet+order.total_price
    user.save()
    context = {
        'order': order,
        'order_item': order_item,
        'payments': payments,
        # 'order_return_message': order_return_message
    }
    return render(request, 'admin/viewdetailorder.html', context)

def updatestatus(request, order_id, new_status):
    
    order = get_object_or_404(Order, pk=order_id)
    
    if new_status == 'Order Confirmed':
        order.status = 'Order Confirmed'
    elif new_status == 'Shipped':
        order.status = 'Shipped'
    elif new_status == 'Out for Delivery':
        order.status = 'Out for Delivery'
    elif new_status == 'Delivered':
        order.status = 'Delivered'
    elif new_status == 'Cancelled':
        order.status = 'Cancelled'
    
    order.save()
    
    messages.success(request, f"Order #{order.tracking_no} has been updated to '{new_status}' status.")
    
    return redirect('order:vieworder')
   
        
        

          
 
        

        

    
    



        
  
    

   