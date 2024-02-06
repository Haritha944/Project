from django.db import models
from user.models import User
from django.utils import timezone



class Referral(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    referral_code = models.CharField(max_length=10,unique=True)
    referred_by = models.ForeignKey(User,related_name='referrals',null=True,blank=True,on_delete=models.SET_NULL)
    created_date = models.DateTimeField(default=timezone.now) 
    new_user_amount = models.FloatField(default=0)
    referred_user_amount = models.FloatField(default=0)
    description = models.TextField(null=True, blank=True)


    def __str__(self):
        return f"{self.user.name}'s Referral: {self.referral_code} Referred: {self.referred_by}"
    

class UserReferral(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.name}'s UserReferral: {self.referral.referral_code} Is Used: {self.is_used}"
    
class ReferralAmount(models.Model):
    new_user_amount = models.DecimalField(max_digits=10, decimal_places=2)
    referred_user_amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
       return str(self.new_user_amount)