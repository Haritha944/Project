from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from cart.models import Cart,CartItem,Address,Coupon,UserCoupons
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from user.models import User
from order.models import Order,OrderItem,Payment,ReturnOrder,UserWallet
from products.models import Product,ProductVariant
from django.db import transaction
from django.views.decorators.cache import cache_control
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist  
from datetime import datetime
import razorpay
import json
from django.template.loader import get_template
from io import BytesIO
from django.views import View
from django.db.models import Sum
import os
from xhtml2pdf import pisa
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt


# Create your views here.

def _cart_id(request):
    cart=request.session.session_key
    if not cart:
        cart=request.session.create()
    return cart

       
def razorpaid(request,tracking_no):
    user=request.user
    print("hii",user)
    try:
        order = Order.objects.get(tracking_no=tracking_no, user=user)
        order_id = order.id
    except Order.DoesNotExist:
        return redirect('cart:cart')
    payment= Payment.objects.filter(user=user).order_by('-created_at').first()
    payment.save()
    order.payment=payment
    order.save()
    cart_id = _cart_id(request)
    cart = Cart.objects.get(cart_id=cart_id)
    cart_items = CartItem.objects.filter(cart=cart,is_active=True).order_by('id')
    
    
    for cart_item in cart_items:
        variant=cart_item.variant
        stock=variant.stock-cart_item.quantity
        variant.stock=stock
        variant.product.stock = stock      
        variant.product.save()
        if 'coupon_code' in request.session:
            coupon_code = request.session['coupon_code']
            coupon = Coupon.objects.get(coupon_code=coupon_code)
            discount = float(coupon.coupon_discount)
            pricevalue=cart_item.variant.discount_price-discount
        else:
            pricevalue=cart_item.variant.discount_price

        order_product = OrderItem.objects.create(
            order=order,
            user=user,
            product=cart_item.product,
            variant=cart_item.variant,
            quantity=cart_item.quantity,
            price=pricevalue,
            
        )
        order_product.save()
    
    cart_items.delete()
    if 'coupon_code' in request.session:
        del request.session['coupon_code']
   
    return redirect('order:orderinvoice', order_id=order_id)

    
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
        variant.stock=stock
        variant.product.stock = stock
        variant.save()
        variant.product.save()
        if 'coupon_code' in request.session:
            coupon_code = request.session['coupon_code']
            coupon = Coupon.objects.get(coupon_code=coupon_code)
            discount = float(coupon.coupon_discount)
            pricevalue=cart_item.variant.discount_price-discount
        else:
            pricevalue=cart_item.variant.discount_price

        order_product = OrderItem.objects.create(
            order=order,
            user=user,
            product=cart_item.product,
            variant=cart_item.variant,
            quantity=cart_item.quantity,
            price=pricevalue,
            
        )
        order_product.save()
    
    cart_items.delete()
    if 'coupon_code' in request.session:
        del request.session['coupon_code']
    
    context = {'order': order}

    return render(request, 'order/cashdelivery.html', context)

@login_required
def orderinvoice(request,order_id):
    user = request.user
    order = Order.objects.get(id=order_id)
    order_items = OrderItem.objects.filter(order=order,user=user)
    payment = Payment.objects.filter(order=order,user=user)
    #cart_id = _cart_id(request)
    #cart = Cart.objects.get(cart_id=cart_id)
   #cart_items = CartItem.objects.filter(cart=cart,is_active=True).order_by('id')
    cart_items = CartItem.objects.filter(user=user)
    total = 0
    tax = 0
    discount = 0
    grand_total = 0
    subtotal = 0 
    for order_item in order_items:
        order_item_total = order_item.variant.discount_price * order_item.quantity
        subtotal += order_item_total
        total=subtotal  
    discount=order_item.variant.discount_price-order_item.price
    if discount != 0:
        total -= discount
    else:
        total=subtotal
    tax = (2 * total) / 100  
    grand_total = total + tax 

    context = {
        'order': order,
        'order_items': order_items,
        'payment': payment,
        'grand_total': grand_total,
        'cart_items': cart_items,
        'total': total,
        'tax':tax,
        'discount':discount,
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
        if order.payment.payment_method == 'Razorpay' or order.payment.payment_method == 'Wallet':
            email = request.user
            user = User.objects.get(email=email)
            userwallet = UserWallet()
            userwallet.user = request.user
            if userwallet is not None:
                userwallet.amount=UserWallet.objects.filter(user=user, transaction='Credited').aggregate(Sum('amount'))['amount__sum'] or 0
                userwallet.amount = (userwallet.amount or 0) + order.total_price
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
    discount=0
    total=0

    for item in order_item:
        item_total = item.variant.discount_price * item.quantity
        #total = item_total  
        subtotal += item_total
        total=subtotal
    discount=item.variant.discount_price-item.price  
    if discount != 0:
        total -= discount 
    else:
        total=subtotal
    tax = (2 * total) / 100
    grand_total = total + tax 
    # user.wallet = user.wallet+order.total_price
    user.save()
    context = {
        'order': order,
        'order_item': order_item,
        'payments': payments,
        'subtotal':subtotal,
        'discount':discount,
        'tax': tax,
        'total':total,
        'grand_total': grand_total,
        
        # 'order_return_message': order_return_message
    }
    return render(request, 'admin/viewdetailorder.html', context)

def updatestatus(request, order_id, new_status):
    
    order = get_object_or_404(Order, pk=order_id)
    order_item = OrderItem.objects.filter(order=order)
    try:
        if new_status == 'Order Confirmed':
            order.status = 'Order Confirmed'
        elif new_status == 'Shipped':
            order.status = 'Shipped'
        elif new_status == 'Pending':
            order.status = 'Pending'
        elif new_status == 'Delivered':
            order.status = 'Delivered'
        elif new_status == 'Cancelled':
            order.status = 'Cancelled'
            context = {
                    'order': order,
                    'order_item': order_item
                }
            return render(request, 'admin/viewdetailorder.html', context)
        order = Order.objects.get(id=order_id)
        order_item = OrderItem.objects.filter(order=order)
        for item in order_item:
            item.status = new_status
            item.save()
        order.status = new_status
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
    
        return render(request, 'admin/viewdetailorder.html',context)
    except:
        pass
    order_item = OrderItem.objects.filter(order=order)
    context = {
        'order': order,
        'order_item': order_item
    }
    return render(request, 'admin/order/viewdetailorder.html', context)

   

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
@login_required
def mywallet(request):
    user = request.user 
    wallet_transaction = UserWallet.objects.filter(user=request.user)
    
    try:
        wallets = UserWallet.objects.filter(user=user).order_by('-created_at')
        wallet_amount = sum(wallet.amount for wallet in wallets)
    except UserWallet.DoesNotExist:
        wallet_amount=0
        
   
     
    context = {
        'wallet_amount': wallet_amount,
        'wallet_transaction': wallet_transaction,
        
    }

    return render(request, 'userprofile/wallet.html', context)

@login_required   
@never_cache
def walletpay(request,order_id):
    user=request.user
    order = Order.objects.get(id=order_id)
    wallet = None
    try:
        wallet = UserWallet.objects.filter(user=user).order_by('-created_at').first()
    except:
        #wallet = UserWallet.objects.create(user=request.user,amount=0)
        #wallet.save()
        pass
    if wallet.amount >= order.total_price:
        payment = Payment.objects.create(user=request.user,payment_method='Wallet',amount_paid=order.total_price,status='Paid')
        payment.save()
        order.payment=payment
        order.save()
        wallet.amount -= order.total_price
        wallet.save()
        cart_id = _cart_id(request)
        cart = Cart.objects.get(cart_id=cart_id)
        cart_items = CartItem.objects.filter(cart=cart,is_active=True).order_by('id')
        print(cart_items)
        for cart_item in cart_items:
            variant=cart_item.variant
            stock=variant.stock-cart_item.quantity
            variant.stock=stock
            variant.product.stock = stock
            variant.save()
            variant.product.save()
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

@login_required          
def viewcoupon(request):
    coupons = Coupon.objects.all().order_by('-id')
    context = {
        'coupons': coupons
    }
    return render(request,'admin/viewcoupon.html',context)

def addcoupon(request):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        coupon = Coupon()
        coupon_name = request.POST.get('coupon_name')
        if Coupon.objects.filter(coupon_name=coupon_name).exists():
            messages.warning(request,'Coupon name already exists')
            return redirect(url)
        else:
            coupon.coupon_name = request.POST.get('coupon_name')
        coupon_code = request.POST.get('coupon_code')
        if Coupon.objects.filter(coupon_code=coupon_code).exists():
            messages.warning(request,'Coupon code already exists')
            return redirect(url)
        else:
            coupon.coupon_code = request.POST.get('coupon_code')
        coupon.min_purchase=request.POST.get('min_price')
        coupon.coupon_discount = request.POST.get('discount_amount')
        coupon.start_date=datetime.strptime(request.POST.get('start_date'), '%d/%m/%Y').strftime('%Y-%m-%d')
        coupon.end_date=datetime.strptime(request.POST.get('end_date'), '%d/%m/%Y').strftime('%Y-%m-%d')
        coupon.save()
        return redirect('order:viewcoupon')

def editcoupon(request,id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        coupon = Coupon.objects.get(id=id)
        coupon_name = request.POST.get('coupon_name')
        if coupon_name != coupon.coupon_name:
            if Coupon.objects.filter(coupon_name=coupon_name).exists():
                messages.error(request, "coupon name already exist ")
                return redirect(url)
            else:
                coupon.coupon_name = request.POST.get('coupon_name')

        coupon_code = request.POST.get('coupon_code')
        if coupon_code !=coupon.coupon_code:
            if Coupon.objects.filter(coupon_code=coupon_code).exists():
                messages.error(request, "coupon code already exist ")
                return redirect(url)
            else:
                coupon.coupon_code = request.POST.get('coupon_code')        
        coupon.min_purchase = request.POST.get('min_price')
        coupon.coupon_discount = request.POST.get('discount_amount')
        coupon.start_date = datetime.strptime(request.POST.get('start_date'), '%d/%m/%Y').strftime('%Y-%m-%d')
        coupon.end_date = datetime.strptime(request.POST.get('end_date'), '%d/%m/%Y').strftime('%Y-%m-%d')
        coupon.save()
        return redirect('order:viewcoupon')
    
def deletecoupon(request,id):
    coupons = Coupon.objects.get(id=id)
    coupons.delete()
    return redirect('order:viewcoupon')

@login_required
def mycoupons(request):
    if request.user.is_authenticated:
        coupons = Coupon.objects.all()
        user = request.user

        coupon_statuses = []

        for coupon in coupons:
            is_used = UserCoupons.objects.filter(coupon=coupon, user=user, is_used=True).exists()
            coupon_statuses.append("Used" if is_used else "Active")

        coupon_data = zip(coupons, coupon_statuses)

        context = {'coupon_data': coupon_data}
        return render(request, 'userprofile/mycoupons.html', context)
    else:
        return redirect('user:handlelogin')
    
def _cart_id(request):
    cart=request.session.session_key
    if not cart:
        cart=request.session.create()
    return cart
    
def applycoupon(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        cart_id = _cart_id(request)
        cart = Cart.objects.get(cart_id=cart_id)
        cart_items = CartItem.objects.filter(cart=cart, is_active=True).order_by('id')
        if 'cancel' in request.POST:
            return handlecancel(request)
        request.session['coupon_code'] = coupon_code
        try:
            coupon = Coupon.objects.get(coupon_code=coupon_code)
            cart = Cart.objects.get(cart_id=cart_id)
            cart_items = CartItem.objects.filter(cart=cart, is_active=True).order_by('id')
            if coupon.start_date <= timezone.now() <= coupon.end_date:
                cart_total = sum(cart_item.variant.discount_price * cart_item.quantity for cart_item in cart_items)
                if cart_total >= coupon.min_purchase:
                    if UserCoupons.objects.filter(user=request.user, coupon=coupon, is_used=True).exists():
                        coupon_code=None
                        messages.warning(request, 'Coupon has already been Used')
                    else:
                        for cart_item in cart_items:
                            updated_total = cart_item.variant.discount_price - float(coupon.coupon_discount)
                            cart_item.variant.discount_price = updated_total
                            cart_item.save()

                        #used_coupons = UserCoupons(user=request.user, coupon=coupon, is_used=True)
                        #used_coupons.save()
                        messages.success(request, 'Coupon applied successfully!')

                        return redirect('cart:cart')
                else:
                    messages.warning(request, 'Coupon is not Applicable for Order Total')
            else:
                messages.warning(request, 'Coupon is not Applicable for the current date')
        except ObjectDoesNotExist:
            messages.warning(request, 'Coupon code is Invalid')
            #return redirect('cart:cart')
           

    return redirect('cart:cart')

def handlecancel(request):
    if 'coupon_code' in request.session:
        del request.session['coupon_code']
    return redirect('cart:cart')

from typing import Dict,Any
def pdf_download(request,id):
    order=Order.objects.get(id=id)
    neworderitems=OrderItem.objects.filter(order=order)
    subtotal=0
    for order_item in neworderitems:
        order_item_total = order_item.variant.discount_price * order_item.quantity
        subtotal += order_item_total
        total=subtotal  
    discount=order_item.variant.discount_price-order_item.price
    if discount != 0:
        total -= discount
    else:
        total=subtotal
    tax = (2 * total) / 100  
    grand_total = total + tax 

    cont = {
        'order': order,
        'cart_items': neworderitems,
        'tax':tax,
        'discount':discount,
        'subtotal':subtotal,
        'total':total,
        'grand_total':grand_total
    }
    pdf = render_to_pdf('order/invoicedownload.html', cont)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = "Invoice_%s.pdf" % (cont['order'])
        content = "inline; filename='%s'" % (filename)
        # download = request.GET.get("download")
        # if download:
        content = "attachment; filename=%s" % (filename)
        response['Content-Disposition'] = content
        return response
def render_to_pdf(template_src, context_dict=None):
    if context_dict is None:
        context_dict = {}
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)#, link_callback=fetch_resources)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

def fetch_resources(uri, rel):
    path = os.path.join(uri.replace(settings.STATIC_URL, ""))
    return path

class GenerateInvoice(View):
    def get(self, request, pk, *args, **kwargs):
        try:
            order = Order.objects.get(payment_id=id)
            neworderitems = OrderItem.objects.filter(order=order.id)
        except:
            return HttpResponse("505 Not Found")
        data = {
            'order': order,
            'cart_items': neworderitems
        }
        pdf = render_to_pdf('order/orderconfirm.html', data)
        # return HttpResponse(pdf, content_type='application/pdf')

        # force download
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = "Invoice_%s.pdf" % (order.id)
            content = "inline; filename='%s'" % (filename)
            # download = request.GET.get("download")
            # if download:
            content = "attachment; filename=%s" % (filename)
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Not found")
    
@never_cache
def salesreport(request):
    total_sales=0
    total_order=0
    if request.method=="POST":
        start_date=request.POST.get('start_date')
        end_date=request.POST.get('end_date')
        if start_date==end_date:
            print(start_date)
            orders = Order.objects.filter(created_at__date=start_date)
        else:
            orders = Order.objects.filter(created_at__range=(start_date, end_date))
            Pending = Order.objects.filter(created_at__range=(start_date, end_date),status='Order confirmed').count()
            Shipped = Order.objects.filter(created_at__range=(start_date,end_date),status='Shipped').count()
            Delivered = Order.objects.filter(created_at__range=(start_date,end_date),status='Delivered').count()
            Cancelled = Order.objects.filter(created_at__range=(start_date,end_date),status='Cancelled').count()
            Returned = Order.objects.filter(created_at__range=(start_date,end_date),status='Returned').count()
            for order in orders:
                total_sales+=order.total_price
    else:
        orders=Order.objects.filter(total_price__gt=0)
        total_order=Order.objects.all().count()
        Pending = Order.objects.filter(status='Order confirmed').count()
        Shipped = Order.objects.filter(status='Shipped').count()
        Delivered = Order.objects.filter(status='Delivered').count()
        Cancelled = Order.objects.filter(status='Cancelled').count()
        Returned = Order.objects.filter(status='Returned').count()
       
        for order in orders:
            total_sales = total_sales + order.total_price
    context={
        'orders':orders,
        'total_sales':total_sales,
        'total_order':total_order,
        'Pending':Pending,
        'Shipped':Shipped,
        'Delivered':Delivered,
        'Cancelled':Cancelled,
        'Returned':Returned,
    }

        
    return render(request,'admin/viewsalesreport.html',context)

def render_to_pdf(template_path, context_dict):
    template = get_template(template_path)
    html = template.render(context_dict)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Sales_report.pdf"'

    # Create a PDF with xhtml2pdf
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

def sales_report_pdf_download(request):
    if request.method == "POST":
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        print(f"Start Date: {start_date}, End Date: {end_date}")
        if start_date and end_date:
            order = Order.objects.filter(created_at__range=(start_date, end_date), total_price__gt=0)
        else:
            order=Order.objects.filter(total_price__gt=0)
        cont = {
            'orders': order,
        }
        pdf = render_to_pdf('admin/salesreportdownload.html', cont)
        return pdf
    
    else:
        order=Order.objects.filter(total_price__gt=0)
    cont = {
            'orders': order,
        }
    pdf = render_to_pdf('admin/salesreportdownload.html', cont)
    return pdf
    
    

@csrf_exempt
def callback(request):
    order_id = request.GET.get('order_id')
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return redirect('cart:cart')
    r_tot=order.total_price*100
    request.user=order.user
    client = razorpay.Client(auth=("rzp_test_zLLrBmHDjYzLTa","RZzrXnbKkKZyFzvIGk57In95"))
    paymentt=client.order.create({'amount':r_tot,'currency':'INR','payment_capture':'1'})
    print(paymentt,request.user)
    razorpay_payment_id = request.POST.get("razorpay_payment_id")
    signature_id = request.POST.get("razorpay_signature")

    print(razorpay_payment_id,signature_id)
    #payment.razor_pay_id=razorpay_payment_id
    #order.payment.payment_method="Razorpay"
    #order.payment.save()
    payment_object = Payment.objects.create(
        user = order.user,
        razor_pay_id = razorpay_payment_id,
        signature_id = signature_id,
        payment_method="Razorpay",
        status="Paid",
        amount_paid=order.total_price,
    )
    payment_object.save()
    

    def verify_signature(response_data):
        client = razorpay.Client(auth=("rzp_test_zLLrBmHDjYzLTa","RZzrXnbKkKZyFzvIGk57In95"))
        return client.utility.verify_payment_signature(response_data)
    if "razorpay_signature" in request.POST:
        order_id = request.GET.get('order_id')
        order = Order.objects.get(id=order_id)
        payment = Payment.objects.get(order=order) 
        payment_id = request.POST.get("razorpay_payment_id")
        print('hiii')
        order_id = request.POST.get("razorpay_order_id")
        signature_id = request.POST.get("razorpay_signature")
        payment.razor_pay_id=payment_id
        payment.payment_method="Razorpay"
        payment.signature_id = signature_id
        print(payment.razor_pay_id)
        print(payment.signature_id)
        payment.save()
        if verify_signature(request.POST):
            order.payment.status = "SUCCESS"
            order.save()
            return render(request, 'order/sucessorder.html',{'order':order})
        else:
            order.payment.status = "FAILURE"
            order.save()
            return render(request, "order/paymentfailure.html", context={"status": order.payment.status})
    
    return render(request, 'order/sucessorder.html',{'order':order})
        
    
       

    
    



        
  
    

   