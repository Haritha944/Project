from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from cart.models import Cart,CartItem,Address
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from user.models import User
from order.models import Order,OrderItem,Payment,ReturnOrder,UserWallet
from products.models import Product,ProductVariant
from django.db import transaction

# Create your views here.

def _cart_id(request):
    cart=request.session.session_key
    if not cart:
        cart=request.session.create()
    return cart
@transaction.atomic      
def confirmrazorpayment(request,tracking_no):
    user = request.user
    try:
        order = Order.objects.get(tracking_no=tracking_no, user=user)
    except Order.DoesNotExist:
        return redirect('cart:cart')
    
    total_amount = order.total_price 

    payment = Payment(
        user=user,
        payment_method="Razorpay",
        status="Paid",
        amount_paid=total_amount,
    )
    payment.save()

    order.tracking_no = tracking_no
    order.payment = payment
    order.save()



    cart_items = CartItem.objects.filter(user=user)
    for cart_item in cart_items:
        product=cart_item.product
        stock=product.stock-cart_item.quantity
        product.stock=stock
        product.save()
        order_product = OrderItem(
            order=order,
            payment=payment,
            user=user,
            product=cart_item.product,
            quantity=cart_item.quantity,
            product_price=cart_item.variant.discount_price,
           
        )
        order_product.save()

    cart_items.delete()

    context = {'order': order}

    return render(request, 'order/orderconfirm.html', context)
    
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

@login_required
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

def myorder(request):
    orders = Order.objects.filter(user=request.user,payment__isnull=False).order_by('-id')
    order_items = OrderItem.objects.filter(user=request.user).order_by('-id')
    context = {
        'orders': orders,
        "order_items": order_items,
    }
    return render(request, 'userprofile/myorder.html',context)
@login_required        
def myorderdetail(request,order_id):
    user=request.user  
    print(user)
    email = request.user
    user = User.objects.get(email=email)
    order = Order.objects.get(id=order_id)
    if request.method == "POST":
        status=request.POST.get('status')
        order = Order.objects.filter(user=user)
        if status == 'status' or status == 'all':
            order_items = OrderItem.objects.filter(user=user).order_by('-id')
        else:
            print(status)
            order_items = OrderItem.objects.filter(user=user,status=status).order_by('-id')
            order_items1 = OrderItem.objects.filter(user=user, status='Cancelled',).values()
            print(order_items1)
        context = {
            "order": order,
            "order_items": order_items
        }
    else:
        order_items = OrderItem.objects.filter(user=user,order=order).order_by('-id')
        context = {
            "order": order,
            "order_items": order_items
        }
    
    
    return render(request, 'userprofile/order.html', context)
@login_required
def cancelorder(request,order_item_id):
    order_item = OrderItem.objects.get(id=order_item_id)
    order = Order.objects.get(id=order_item.order.id)
    if order is not None:
        order.status = 'Cancelled'
        order.save()
        order_items = OrderItem.objects.filter(order=order)
        print(order.payment.payment_method)
        if order.payment.payment_method == 'Paid by Razorpay' or order.payment.payment_method == 'Wallet':
            email = request.user
            user = User.objects.get(email=email)
            userwallet = UserWallet()
            userwallet.user = request.user
            userwallet.amount = order.total_price
            userwallet.transaction = 'Credited'
            userwallet.save()
            user.save()
        for item in order_items:
            reason = request.POST.get('cancel')
            item.status = 'Cancelled'
            item.save()
        return redirect('order:myorder')    
    else:
        pass    

#<!---------admin---------->  
def vieworder(request):
    if request.method=="POST":
        status=request.POST.get('status')
        print(status)
        if status == 'status' or status == 'all':
            orders = Order.objects.filter(payment__isnull=False).order_by('-id')
        else:
            orders = Order.objects.filter(status=status,payment__isnull=False).order_by('-id')
        context = {
            'orders': orders
        }
        return render(request, 'admin/vieworder.html', context)
    else:
        orders = Order.objects.filter(payment__isnull=False).order_by('-id')
        context = {
            "orders": orders,
            
        }
        return render(request, 'admin/vieworder.html', context)
def viewsingleadmin(request, order_id):
    order = Order.objects.get(id=order_id)
    order_item = OrderItem.objects.filter(order=order)
    user=User.objects.get(id=order.user.id)
    payments = Payment.objects.filter(order__id=order_id)
    subtotal=0
    for item in order_item:
        item_total = item.variant.discount_price * item.quantity
        total = item_total  
        subtotal += item_total
        tax = (2 *subtotal) / 100
        

        grand_total = subtotal + tax 

    # user.wallet = user.wallet+order.total_price
    user.save()
    context = {
        'order': order,
        'order_item': order_item,
        'payments': payments,
        'tax': tax,
        'grand_total': grand_total,
        
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
    if order.status == 'Returned':
        email = order.user.email
        user = User.objects.get(email=email)
        userwallet = UserWallet()
        userwallet.user = user
        userwallet.amount += order.total_price
        userwallet.transaction = 'Credited'
        userwallet.save()
        user.save()
        order_item = OrderItem.objects.filter(order=order)
        context = {
                'order': order,
                'order_item': order_item
            }
    
    #messages.success(request, f"Order #{order.tracking_no} has been updated to '{new_status}' status.")
    
    return render(request, 'admin/viewdetailorder.html', context)
   

def returnorder(request,order_item_id):
    order_item = OrderItem.objects.get(id=order_item_id)
    order = Order.objects.get(id=order_item.order.id)
    if request.method == 'POST':
        reason = request.POST.get('reason')
        returnorder = ReturnOrder()
        returnorder.order_item = order_item
        returnorder.order = order
        returnorder.return_comment = reason
        returnorder.save()
        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            reason = request.POST.get('return')
            item.status = 'Return requested'
            item.save()
            order.status = "Return requested"
            order.save()
    return redirect('order:myorder')   


def returnapprove(request,order_id):
    order = Order.objects.get(id=order_id)
    order.status = "Returned"
    order.save()
    order_item = OrderItem.objects.filter(order=order)
    for item in order_item:
        item.status = "Returned"
        item.save()
    context = {
        'order' : order,
        'order_item' : order_item,
    }
    return render(request,"admin/viewdetailorder.html",context)

def mywallet(request):
    user = request.user 
    try:
        wallet = UserWallet.objects.get(user=user)
    except UserWallet.DoesNotExist:
        wallet = UserWallet.objects.create(user=user,amount=0)
    wallet_amount=wallet.amount
     
    context = {'wallet_amount': wallet_amount}

    return render(request, 'userprofile/wallet.html', context)

def walletpay(request,order_id):
    user=request.user
    order = Order.objects.get(id=order_id)
    try:
        wallet = UserWallet.objects.get(user=request.user)
    except:
        wallet = UserWallet.objects.create(user=request.user,amount=0)
        wallet.save()
    if wallet.amount > order.total_price:
        payment = Payment.objects.create(user=request.user,payment_method='Wallet',amount_paid=order.total_price,status='Paid')
        payment.save()
        order.payment=payment
        order.save()
        wallet.amount -= order.total_price
        wallet.save()
        cart_items = CartItem.objects.filter(user=user)
        for cart_item in cart_items:
            product=cart_item.product
            stock=product.stock-cart_item.quantity
            product.stock=stock
            product.save()
            order_product = OrderItem(
                order=order,
                user=user,
                product=cart_item.product,
                variant=cart_item.variant,
                quantity=cart_item.quantity,
                price=cart_item.product.discount_price
                
            )
            order_product.save()
        
        cart_items.delete()
    else:
        messages.warning(request, 'Not Enough Balance in Wallet')
        return render(request, 'userprofile/wallet.html')
    context = {
        'order': order,
        'tracking_no': order.tracking_no,
        }
    return render(request, 'order/cashdelivery.html', context)
          
 
        

        

    
    



        
  
    

   