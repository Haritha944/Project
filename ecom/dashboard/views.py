from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from user.models import User
from cart.models import Wishlist
from products.models import ProductVariant,Product
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control, never_cache

# Create your views here.

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def adminlogin(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        if email is not None and password is not None and email.strip() == '' and password.strip() == '':
            messages.warning(request, "Fields can't be blank")
            return redirect('/adminlogin/')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            if user.is_superuser:
                login(request, user)
                return redirect('/admindash/')
    return render(request,'admin/adminlogin.html')

@never_cache
def admindashboard(request):
    if request.user.is_superuser:
       return render(request, 'admin/dashboard.html')
    else:
        return redirect('/adminlogin/')
       
@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def adminlogout(request):
    if request.user.is_authenticated:
        print("User is authenticated. Logging out...")
        logout(request)
        print("User logged out.")
    return redirect('/adminlogin/')


def usersdetails(request):
    if request.method == 'POST':
        search = request.POST.get('search')
        users = User.objects.filter(
             Q(name__icontains=search) |
            Q(email__icontains=search) 
        ).filter(is_superuser=False).order_by('id')
        user_count = User.objects.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) 
            
        ).filter(is_superuser=False).order_by('id').count()
    else:
        users = User.objects.filter(is_superuser=False).order_by('id')
        user_count = User.objects.filter(is_superuser=False).order_by('id').count()

    paginator = Paginator(users, 6)
    page_number = request.GET.get('page', 1)
    users = paginator.get_page(page_number)
    context = {
        'users': users,
        'user_count': user_count

    }
    return render(request,'admin/userdetail.html',context)

   
def userblock(request, user_id):
    user = User.objects.get(id=user_id)
    if user.is_active:
        user.is_active = False
        user.save()
        users = User.objects.filter(is_superuser=False).order_by('id')
        context = {
            'users': users
        }
        return render(request, 'admin/userdetail.html', context)
    else:
        user.is_active = True
        user.save()
        users = User.objects.filter(is_superuser=False).order_by('id')
        context = {
            'users': users
        }
        return render(request, 'admin/userdetail.html', context)
    
@login_required
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def wishlist(request):
    wishlist = Wishlist.objects.filter(user=request.user)
    context = {
        'wishlist':wishlist,
    }
    return render(request,'userprofile/wishlist.html',context)

def addwishlist(request,variant_id):
    variant=ProductVariant.objects.get(id=variant_id)
    product = Product.objects.get(id=variant.product.id)
    try:
        is_exist = Wishlist.objects.filter(user=request.user,variant=variant).exists()
        if is_exist:
            messages.warning(request,'This product is already in your wishlist.')
        else:
            wishlist = Wishlist.objects.create(user=request.user,variant=variant)
            wishlist.save()
            messages.success(request,'Product is added to your wishlist.')
        return redirect('user:index')
    except Exception as e:
        print(e)
        messages.error(request,'Failed to add the product to the wishlist.')
        return redirect('user:index')
    

def removewish(request,wish_id):
    try:
        wishlist_item = Wishlist.objects.get(id=wish_id, user=request.user)
        wishlist_item.delete()  # Remove the wishlist item
    except Wishlist.DoesNotExist:
        pass
    wishlist = Wishlist.objects.filter(user=request.user)
    context = {
        'wishlist': wishlist,
    }
    return render(request, 'userprofile/wishlist.html', context)


