from django.contrib import admin
from .models import *
from django.apps import AppConfig


# Register your models here.
class AuthorAdmin(admin.ModelAdmin):
    pass

admin.site.register([Fingerprint,Employee,messengerbag,timesheet, Acceptorder, Rejectorder,Customer,acknowledgedstockorder,submitstockorder,punchedprodso,user1, Categories, Sizes, Subcategories, PSizes, punchedprod, queue1, queue2, queue3, Sales,Dailysales, saecat,saesubcate,saesubcats, couponlist,CategoriesCoupon])
