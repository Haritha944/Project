from django.db import models
from user.models import User
from django.utils import timezone



class Referral(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    referral_code = models.CharField(max_length=10,unique=True)
    referred_by = models.ForeignKey(User,related_name='referrals',null=True,blank=True,on_delete=models.SET_NULL)
    created_date = models.DateTimeField(default=timezone.now) 


    def __str__(self):
        return f"{self.user.name}'s Referral: {self.referral_code} Referred: {self.referred_by}"
    

