from django.shortcuts import render,redirect,get_object_or_404
from cart.models import Cart,CartItem,Address,Coupon,UserCoupons
from products.models import Product,ProductVariant
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from user.models import User
from django.http import HttpResponse,JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from order.models import Order,OrderItem,Payment
import random
# Create your views here.

#<!- Cart section --->
def _cart_id(request):
    cart=request.session.session_key
    if not cart:
        cart=request.session.create()
    return cart

def addcart(request,product_id):
    variant = ProductVariant.objects.get(id=product_id)
    product = Product.objects.get(id=variant.product.id) #Get the product
    try:
        cart=Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id= _cart_id(request)
        )
    cart.save()
    try:
        cart_item = CartItem.objects.get(product=product,cart=cart)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(
            product=product,
            quantity = 1,
            cart=cart,
            variant=variant,

        )
        cart_item.save()
    #return HttpResponse(cart_item.product)
    return redirect('cart:cart')
        


       
def cart(request,total=0,quantity=0,cart_items=None):
    url = request.META.get('HTTP_REFERER')
    cart_id = _cart_id(request)
    tax=0
    discount=0
    grand_total=0
    current_date = timezone.now()
    try:
        cart=Cart.objects.get(cart_id = cart_id)
        cart_items = CartItem.objects.filter(cart=cart,is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.discount_price * cart_item.quantity)
            quantity += cart_item.quantity
        if 'coupon_code' in request.session:
            coupon_code = request.session['coupon_code']
            try:
                coupon = Coupon.objects.get(coupon_code=coupon_code)
                # Check if the coupon is valid and not expired
                if coupon.start_date <= current_date <= coupon.end_date:
                    # Check if the coupon is applicable to the current cart total
                    if total >= coupon.min_purchase:
                        
                        # Apply the coupon discount
                        discount=float(coupon.coupon_discount)
                        total -= discount

                        # Save the coupon details for the user
                        used_coupons = UserCoupons(user=request.user, coupon=coupon, is_used=True)
                        used_coupons.save()

                        #messages.success(request, 'Coupon applied successfully!')
                        
                    else:
                        messages.warning(request, 'Coupon is not applicable for the current cart total.')
                else:
                    messages.warning(request, 'Coupon has expired.')
            except Coupon.DoesNotExist:
                messages.warning(request, 'Invalid coupon code.')

            # Remove the coupon code from the session
            del request.session['coupon_code']
        tax = (2*total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass  #just ignore
    context = {
        'total':total,
        'quantity':quantity,
        'cart_items':cart_items,
        'tax':tax,
        'grand_total':grand_total,
        'discount':discount,

    }

    return render(request,'cart/cart.html',context)

def removecartitem(request,product_id):
    cart_id = _cart_id(request)
    productvariant = get_object_or_404(ProductVariant,id = product_id)
    try:
        email = request.session['user-email']
        user = User.objects.get(email=email)
        cart_item = CartItem.objects.get(variant=productvariant,cart=cart)
    except:
        cart = Cart.objects.get(cart_id=cart_id)
        cart_item = CartItem.objects.get(variant=productvariant,cart=cart)
    cart_item.delete()
    return redirect('cart:cart')


#<!- Cart section End--->

#<!- User Profile section --->
@login_required
def profile(request):
    url = request.META.get('HTTP_REFERER')
    if request.method == "POST":
        email = request.POST.get('email')
        user = User.objects.get(email=email)
        name = request.POST.get('name')
        if name != user.name:
            if User.objects.filter(name=name).exists():
                messages.error(request, "username already exist..!")
                return redirect(url)
            else:
                user.name = request.POST.get('name')
                user.email = request.POST.get('email')
                user.mobile = request.POST.get('mobile')
                user.first_name = request.POST.get('firstname')
                user.last_name = request.POST.get('lastname')
                user.save()
        else:
            user.email = request.POST.get('email')
            user.mobile = request.POST.get('mobile')
            user.first_name = request.POST.get('firstname')
            user.last_name = request.POST.get('lastname')
            user.save()
    if request.user.is_authenticated:
        user = request.user
        context = {
            'user': user
        }
        return render(request, 'userprofile/profile.html',context)
   

    return redirect('user:handlelogin')

@login_required
def address(request):
    user = request.user
    addresses = Address.objects.filter(user_id=user)
    context = {
        'addresses': addresses
    }
    return render(request,'userprofile/address.html',context)
        

    
@login_required
def editaddress(request,address_id):
    if request.method=="POST":
        address = Address.objects.get(id=address_id)
        print(address)
        address.recipient_name = request.POST.get('RecipientName')
        address.email = request.POST.get('email')
        address.house_no = request.POST.get('house_no')
        address.mobile = request.POST.get('mobile')
        address.street_name = request.POST.get('street_name')
        address.village_name = request.POST.get('village_name')
        address.postal_code = request.POST.get('postal_code')
        address.district = request.POST.get('district')
        address.state = request.POST.get('state')
        address.country = request.POST.get('country')
        default_address = request.POST.get('default_address')
        if default_address == 'on':
            try:
                email=request.user
                user=User.objects.get(email=email)
                addrss = Address.objects.get(user_id=user,is_default=True)
                print(addrss)
                addrss.is_default = False
                addrss.save()
            except Address.DoesNotExist:
                pass
        address.is_default= True
        address.save()
        addresses = Address.objects.filter(user_id=address.user_id)
        context = {
            "addresses":addresses
        }


    return render(request,'userprofile/address.html',context)
@login_required
def addaddress(request):
    email = request.POST.get('email')
    user=User.objects.get(email=email)
    default_address = request.POST.get('default_address')
    if default_address == 'on':
        try:
            adrss = Address.objects.get(user_id=user, is_default=True)
            print(adrss)
            adrss.is_default = False
            print(adrss.is_default)
            adrss.save()
        except Address.DoesNotExist:
            pass
    address = Address()
    address.user_id = user
    address.recipient_name = request.POST.get('RecipientName')
    address.email = request.POST.get('email')
    address.house_no = request.POST.get('house_no')
    address.mobile = request.POST.get('mobile')
    address.is_default=True
    address.email = request.POST.get('email')
    address.street_name = request.POST.get('street_name')
    address.village_name = request.POST.get('village_name')
    address.postal_code = request.POST.get('postal_code')
    address.district= request.POST.get('district')
    address.state = request.POST.get('state')
    address.country = request.POST.get('country')
    address.save()
    addresses = Address.objects.filter(user_id=user)
    context = {
            "addresses":addresses
        }
    return render(request,'userprofile/address.html',context)


def deleteaddress(request,address_id):
    address = Address.objects.get(id=address_id)
    if address is not None:
        address.delete()
        return redirect('cart:address')
    
@login_required
def checkout(request,total=0,quantity=0,cart_items=None):
    user=request.user
    url = request.META.get('HTTP_REFERER')
    discount=0
    try:
        try:
            email = request.POST.get('email')
            user=User.objects.get(user=request.user,email=email)
            print(user)
            if user is not None:
               cart_items = CartItem.objects.filter(user_id=user.id, is_active=True).order_by('id')
        except:
            cart_id = _cart_id(request)
            cart = Cart.objects.get(cart_id=cart_id)
            cart_items = CartItem.objects.filter(cart=cart, is_active=True).order_by('id')
            print(cart_items)
           
            for cart_item in cart_items:
                total += (cart_item.variant.discount_price * cart_item.quantity)
                quantity += cart_item.quantity
            if 'coupon_code' in request.session:
                coupon_code = request.session['coupon_code']
                try:
                    coupon = Coupon.objects.get(coupon_code=coupon_code)
                    if coupon.start_date <= timezone.now() <= coupon.end_date:
                        if total >= coupon.min_purchase:
                    # Apply the coupon discount
                            discount = float(coupon.coupon_discount)
                            total -= discount
                            used_coupons = UserCoupons(user=request.user, coupon=coupon, is_used=True)
                            used_coupons.save()
                            messages.success(request, 'Coupon applied successfully!')
                        else:
                            messages.warning(request, 'Coupon is not applicable for the current cart total.')
                    else:
                        messages.warning(request, 'Coupon has expired.')
                except Coupon.DoesNotExist:
                    messages.warning(request, 'Invalid coupon code.')

        # Remove the coupon code from the session
                del request.session['coupon_code']

           
        tax = (2 * total) / 100
        grand_total = total + tax
  
    except Cart.DoesNotExist:
        print("Cart does not exist")
        pass
    except CartItem.DoesNotExist:
        print("CartIT does not exist")
        pass  
       
    address_list = Address.objects.filter(user_id=request.user)
    default_address = address_list.filter(user_id=request.user).first()
    if not default_address:
        return redirect('cart:address')

    context = {
        'total':total,
        'quantity':quantity,
        'grand_total':grand_total,
        'cart_items': cart_items,
        'tax': tax,
        'discount':discount,
        #'selected_address': selected_address,
        'address_list':address_list,
        'default_address': default_address,
    }

    return render(request,'cart/checkout.html',context)

def addaddresscheck(request):
    email = request.POST.get('email')
    user=User.objects.get(email=request.user.email)
    try:
        uname = request.POST.get('RecipientName')
        print(uname)
        if Address.objects.filter(user_id=user, recipient_name=uname).exists():
            print("error")
            messages.error("This user address already exist..!")
            return redirect('cart:checkout')
        else:
            print("yes")
            address = Address()
            address.user_id = user
            address.recipient_name = request.POST.get('RecipientName')
            address.email = request.POST.get('email')
            address.house_no = request.POST.get('house_no')
            address.street_name = request.POST.get('street_name')
            address.village_name = request.POST.get('village_name')
            address.postal_code = request.POST.get('postal_code')
            address.district = request.POST.get('district')
            address.state = request.POST.get('state')
            address.mobile = request.POST.get('mobile')
            address.country = request.POST.get('country')
            address.save()
            return redirect('cart:checkout')
    except:
        messages.error(request, "This user address already exist..!")
        return redirect('cart:checkout',new_address_id=address.id)

def removecart(request, product_id):  
    cart_id = _cart_id(request)  # Get or generate the cart_id
    productvariant = get_object_or_404(ProductVariant, id=product_id)
    print(productvariant)
    try:
        email = request.user
        user=User.objects.get(email=request.user.email)
        cart_item = CartItem.objects.get(variant=productvariant, user_id=user.id)
    except:
        cart = Cart.objects.get(cart_id=cart_id)
        cart_item = CartItem.objects.get(variant=productvariant, cart=cart)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
        sub_total = 0
        try:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        except:
            cart = Cart.objects.get(cart_id=cart_id)
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for item in cart_items:
            sub_total += (item.variant.discount_price * item.quantity)
        total = cart_item.quantity * cart_item.variant.discount_price
        return JsonResponse({'quantity': cart_item.quantity, 'total': total,'sub_total': sub_total})
        
    else:
        cart_item.delete()
        return JsonResponse({'status': 'empty'})
    


    
def checkoutorder(request):
    url = request.META.get('HTTP_REFERER')
    global item,address,cart_items
    discount=0
    #<!------------------checking stock------------------------------->
    try:
        email = request.user
        user = User.objects.get(email=email)
        if user is not None:
            cart_items = CartItem.objects.filter(user_id=user.id,is_active=True).order_by('id')
    except:
        cart_id = _cart_id(request)
        cart = Cart.objects.get(cart_id=cart_id)
        cart_items = CartItem.objects.filter(cart=cart,is_active=True).order_by('id')
    for item in cart_items:
        variant = item.variant
        print(variant.product.product_name,variant.stock,item.quantity)
        if item.quantity >= variant.stock+1:
            print("no" , variant.stock,variant.product.product_name)
            messages.error(request,f"only {variant.stock} stock left on product {variant.product.product_name} size {variant.size}")
            return redirect("cart:cart")
        else:
            print("yes" , variant.stock,variant.product.product_name)
        #<!------------------checking stock------------------------------->
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.get(email=email)
        recipient_name = request.POST.get('username')
        selected_address_id= request.POST.get('selectedAddress')
        if recipient_name is None:
            try:
                address= Address.objects.get(id=selected_address_id)
            except:
                messages.error(request,"Create a address...!")
        else:
            address = Address.objects.get(recipient_name=recipient_name)
        order = Order()
        order.user=user
        order.address=address
        cart = CartItem.objects.filter(user_id=user.id,is_active=True)
        cart_total_price=0
        for item in cart:
            cart_total_price = (cart_total_price + item.variant.discount_price * item.quantity)

        trackno = 'pvkewt' + str(random.randint(1111111, 9999999))
        while Order.objects.filter(tracking_no=trackno) is None:
            trackno = 'pvkewt' + str(random.randint(1111111, 9999999))
        order.tracking_no = trackno
        #<!--coupn-->
        payment_method = request.POST.get(payment_method)
        if payment_method == "Paid by Razorpay":
            order.payment.payment_method = request.POST.get('payment_method')
            order.total_price = cart_total_price
        order.save()
        neworderitems = CartItem.objects.filter(user=user, is_active=True)
        for item in neworderitems:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                price=item.variant.selling_price,
                quantity=item.quantity,
                user=user
            )
            # reduce the product quantity from available stock
            orderproduct = ProductVariant.objects.get(
                id=item.variant.id
            )
            print(orderproduct.stock)
            orderproduct.stock = orderproduct.stock - item.quantity
            print(orderproduct.stock)
            orderproduct.save()

            # delete cart
            try:
               Cart.objects.get(cart_id= item.cart.cart_id).delete()
            except:
                pass
            return render(request, 'order/placeorder.html')
        
    if request.user.is_authenticated:
        cart_id = _cart_id(request)  # Get or generate the cart_id
        tax = 0
        total=0
        grand_total = 0
        subtotal = 0
        quantity = 0
        cart_items = ''
        try:

            try:
                email = request.POST.get('email')
                user = User.objects.get(email=email)
                cart_items = CartItem.objects.filter(user_id=user.id, is_active=True)
            except:
                cart = Cart.objects.get(cart_id=cart_id)
                cart_items = CartItem.objects.filter(cart=cart, is_active=True)
            for cart_item in cart_items:
                subtotal += (cart_item.variant.discount_price * cart_item.quantity)
                quantity += cart_item.quantity
            total = subtotal
            tax = (2 * subtotal) / 100
            grand_total = subtotal + tax

        except ObjectDoesNotExist:
            pass
        try:
            user = request.user
           
            addresses = Address.objects.filter(user_id=user, is_default=False)
        except:
            pass
        try:
            default_address = Address.objects.get(user_id=user, is_default=True)
        except:
            default_address = Address.objects.filter(user_id=user).first()
        
        context = {
            'subtotal': subtotal,
            'quantity': quantity,
            'cart_items': cart_items,
            'addresses': addresses,
            'grand_total': grand_total,
            'default_address': default_address,
            'total': total,
            'discount': discount

        }
        return render(request, 'cart/checkout.html', context)
    return redirect('/login/')

@login_required
def order(request, id=None):
    try:
        if request.session['coupon']:
            offer = request.session['coupon']
    except:
        offer = None
    total = 0
    sub_total = 0
    if id:
        order = Order.objects.get(payment_id=id)
        print(order.payment.payment_method)
        neworderitems = OrderItem.objects.filter(order=order.id)
        print(neworderitems)
        for item in neworderitems:
            total = total + item.variant.discount_price
        if offer is not None:
            total = total - offer
            del request.session['coupon']
        else:
            offer = 0
        sub_total = offer + total
        context = {
            'order': order,
            'cart_items': neworderitems,
            'total': total,
            'offer': offer,
            'sub_total': sub_total
        }
        return render(request, 'order/placeorder.html', context)
    email=request.user
    print(email)
    user=User.objects.get(email=email)
    order = Order.objects.filter(user=user).latest('id')
    neworderitems = OrderItem.objects.filter(order=order)

    for item in neworderitems:
        total = total + item.variant.discount_price
    if offer is not None:
        offer = request.session['coupon']
        total = total - offer
        del request.session['coupon']
    else:
        offer = 0
    sub_total = offer + total
    context = {
        'order': order,
        'cart_items': neworderitems,
        'total': total,
        'offer': offer,
        'sub_total': sub_total
    }
    return  render(request, 'order/placeorder.html', context)


@login_required
def placeorder(request, total=0, quantity=0):
    
    if request.method == 'POST':
        email = request.user
        user = User.objects.get(email=email)
        print(user)
        cart_id = _cart_id(request)
        cart = Cart.objects.get(cart_id=cart_id)
        cart_items = CartItem.objects.filter(cart=cart,is_active=True).order_by('id')
        print(cart_items)
        total = 0
        grand_total=0
        tax=0
        quantity = 0
        for cart_item in cart_items:
            total += (cart_item.variant.discount_price * cart_item.quantity)
            quantity += cart_item.quantity
        
            tax = (2 * total) / 100
            grand_total = total + tax 
            print(grand_total)
        
        if user is not None:
            try:
                address=Address.objects.filter(user_id=user.id).last()
            except:
                messages.error(request,"Create a address...!")
        else:
            address=Address.objects.filter(email=user.email).last()
        
        
        order = Order()
        order.user = user
        order.total_price=grand_total
        order.address = address
        trackno = 'pvkewt' + str(random.randint(1111111, 9999999))
        while Order.objects.filter(tracking_no=trackno) is None:
            trackno = 'pvkewt' + str(random.randint(1111111, 9999999))
        order.tracking_no = trackno
       
        order.save()
        neworderitems = CartItem.objects.filter(user=user, is_active=True)
        for item in neworderitems:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                price=item.variant.discount_price,
                quantity=item.quantity,
                user=user
            )
            # reduce the product quantity from available stock
            orderproduct = ProductVariant.objects.get(
                id=item.variant.id
                )
            print(orderproduct.stock)
            orderproduct.stock = orderproduct.stock - item.quantity
            print(orderproduct.stock)
            orderproduct.save()

            # delete cart
            try:
                Cart.objects.get(cart_id= item.cart.cart_id).delete()
            except:
                pass
        order = Order.objects.get(user=user,tracking_no=trackno,total_price=grand_total)

        context = {
            'order': order,
            'address':address,
            'cart_items': cart_items,
            'total_price': grand_total,
            'tracking_no':trackno,
            'tax': tax,
            'discount': 0,
            'total': total ,
            'quantity': quantity,
        }

        return render(request, 'order/placeorder.html', context)
    else:
        return redirect('cart:checkout')
    

def increment(request, product_id):
    cart_id = _cart_id(request)  # Get or generate the cart_id
    productvariant = get_object_or_404(ProductVariant, id=product_id)

    try:
        email = request.user
        user = User.objects.get(email=email)
        cart_item = CartItem.objects.get(variant=productvariant, user=user)
    except:
        cart = Cart.objects.get(cart_id=cart_id)
        cart_item = CartItem.objects.get(variant=productvariant, cart=cart)

    if productvariant.stock <= cart_item.quantity:

        sub_total = 0
        try:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        except:
            cart = Cart.objects.get(cart_id=cart_id)
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for item in cart_items:
            sub_total += (item.variant.discount_price * item.quantity)
        total = cart_item.quantity * cart_item.variant.discount_price
        return JsonResponse(
            {'quantity': cart_item.quantity, 'total': total, 'sub_total': sub_total, 'messages': "error"})
    # if cart_item.quantity > 1:
    else:
        cart_item.quantity += 1
        cart_item.save()
        # calculating subtotal
        sub_total = 0
        try:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        except:
            cart = Cart.objects.get(cart_id=cart_id)
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for item in cart_items:
            sub_total += (item.variant.discount_price * item.quantity)
        total = cart_item.quantity * cart_item.variant.discount_price
        return JsonResponse(
            {'quantity': cart_item.quantity, 'total': total, 'sub_total': sub_total, "messages": "success"})