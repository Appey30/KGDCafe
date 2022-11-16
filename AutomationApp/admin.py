from django.contrib import admin
from .models import *
from django.apps import AppConfig


class SomeAppConfig(AppConfig):
    # ...

    def ready(self):
        from django.contrib import admin
        from django.contrib.sites.models import Site
        admin.site.unregister(Site)

# Register your models here.
class AuthorAdmin(admin.ModelAdmin):
    pass

admin.site.register([timesheet, Acceptorder, Rejectorder,Customer,acknowledgedstockorder,submitstockorder,punchedprodso,user1, Categories, Sizes, Subcategories, PSizes, punchedprod, queue1, queue2, queue3, Sales,Dailysales, saecat,saesubcate,saesubcats, couponlist,CategoriesCoupon])
