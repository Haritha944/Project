from django.contrib import admin
from dashboard.models import Referral,UserReferral,ReferralAmount

admin.site.register(Referral)
admin.site.register(UserReferral)
admin.site.register(ReferralAmount)