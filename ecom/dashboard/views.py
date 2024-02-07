from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from django.http import JsonResponse
from user.models import User
from cart.views import addcart
from cart.models import Wishlist
from products.models import ProductVariant,Product
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control, never_cache
from order.models import Order, OrderItem
from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from django.utils import timezone
from django.db.models import Q
from dashboard.models import ReferralAmount,UserReferral



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
@login_required(login_url='/adminlogin/')
def admindashboard(request):
    if request.user.is_superuser:
       orders=Order.objects.filter(status='Delivered')
       order_count = orders.count()
       total_amount=0
       customers=User.objects.filter(is_superuser=False).count()
       for item in orders:
            total_amount=total_amount+item.total_price

       no_deliverd = OrderItem.objects.filter(status='Delivered').count()
       no_cancel =  OrderItem.objects.filter(status='Cancelled').count()
       no_return =  OrderItem.objects.filter(status='Returned').count()

       current_year = timezone.now().year

        # Calculate monthly sales for the current year
       monthly_sales = Order.objects.filter(
            created_at__year=current_year
        ).annotate(month=ExtractMonth('created_at')).values('month').annotate(total_sales=Sum('total_price')).order_by(
            'month')

        # Create a dictionary to hold the monthly sales data
       monthly_sales_data = {month: 0 for month in range(1, 13)}

       for entry in monthly_sales:
            month = entry['month']
            total_sales = entry['total_sales']
            monthly_sales_data[month] = total_sales

       context = {
            'total_amount': total_amount,
            'order_count': order_count,
            'customers': customers,
            'no_deliverd': no_deliverd,
            'no_cancel': no_cancel,
            'no_return': no_return,
            'monthly_sales_data': monthly_sales_data
        }
       return render(request, 'admin/dashboard.html',context)
    else:
        return redirect('/adminlogin/')
       
@cache_control(no_cache=True, must_revalidate=True,no_store=True) 
@never_cache
def adminlogout(request):
    if request.user.is_authenticated:
        print("User is authenticated. Logging out...")
        logout(request)
        print("User logged out.")
    return redirect('/adminlogin/')

@login_required(login_url='/adminlogin/')
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
            return redirect('dashboard:wishlist')
        else:
            wishlist = Wishlist.objects.create(user=request.user,variant=variant)
            wishlist.save()
           # messages.success(request,'Product is added to your wishlist.')
        return redirect('user:index')
    except Exception as e:
        print(e)
        messages.error(request,'Failed to add the product to the wishlist.')
        return redirect('dashboard:wishlist')
    

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

def addwishcart(request,wish_id):
    try:
        wishlist_item = Wishlist.objects.get(id=wish_id,user=request.user)
        addcart(request,product_id=wishlist_item.variant.id)
        wishlist_item.delete()
    except Wishlist.DoesNotExist:
        pass
    wishlist = Wishlist.objects.filter(user=request.user)
    context = {
        'wishlist': wishlist,
    }
    return render(request,'userprofile/wishlist.html',context)

@login_required(login_url='/adminlogin/')
def get_sales_revenue(request):
    # Replace this with your actual data retrieval logic
    # Example mock data
    orders=Order.objects.filter(status='Delivered')
    order_count = orders.count()
    total_amount=0
    current_year = timezone.now().year
    for item in orders:
        total_amount=total_amount+item.total_price
    revenue=total_amount*12
   
    monthly_sales = Order.objects.filter(
            created_at__year=current_year
        ).annotate(month=ExtractMonth('created_at')).values('month').annotate(total_sales=Sum('total_price')).order_by(
            'month')
    
        # Create a dictionary to hold the monthly sales data
    monthly_sales_data = {month: 0 for month in range(1, 13)}

    for entry in monthly_sales:
        month = entry['month']
        total_sales = entry['total_sales']
        monthly_sales_data[month] = total_sales
    data = {
        
        'sales': monthly_sales_data,
        'revenue':revenue,
    }

    return JsonResponse(data)


def add_referral_program(request):
    referral_programs = ReferralAmount.objects.all()
    no_referral_programs = False
    if not referral_programs:
        no_referral_programs = True
    if request.method == 'POST':
        description = request.POST.get('description', '')
        new_user_amount = float(request.POST.get('new_user_amount'))
        referred_user_amount = float(request.POST.get('referred_user_amount'))
        # Create the referral program with the provided data
        ReferralAmount.objects.create(
            description=description,
            new_user_amount=new_user_amount,
             referred_user_amount = referred_user_amount 
        )
        # Redirect to a success page or perform other actions
        return redirect('dashboard:add_referral_program')
    context = {
        'referral_programs': referral_programs,
        'no_referral_programs': no_referral_programs,
    }
    return render(request, 'admin/adminreferral.html', context)

def edit_referral_program(request, program_id):
    program = ReferralAmount.objects.get(id=program_id)
    if request.method == 'POST':
        description = request.POST.get('description')
        new_user_amount = float(request.POST.get('new_user_amount'))
        referred_user_amount  = float(request.POST.get('referred_user_amount'))
        program.description = description
        program.new_user_amount = new_user_amount
        program.referred_user_amount  = referred_user_amount 
        program.save()
        return redirect('dashboard:add_referral_program')
    context = {'program': program}
    return render(request, 'admin/editreferral.html', context)
def deletereferral(request,program_id):
    refers = ReferralAmount.objects.get(id=program_id)
    refers.delete()
    return redirect('dashboard:add_referral_program')

def myrefer(request):
    if request.user.is_authenticated:
        user=request.user
        try:
            refer=UserReferral.objects.filter(user=user).first()
            if refer:
                refer_code=refer.referral.referral_code
                context={
                'refer_code':refer_code,
                'user':user,
                }

                return render(request, 'userprofile/referral.html',context)
            else:
                messages.error(request,'No referral code for you now')
                return render(request, 'userprofile/referral.html')
        except UserReferral.DoesNotExist:
           
            context = {
                'error_message': 'No referral code found for the current user.'
            }
            return render(request, 'userprofile/referral.html', context)
    else:
        return render(request, 'userprofile/referral.html')