from django.contrib import admin
from .models import *


# Register your models here.
class AuthorAdmin(admin.ModelAdmin):
    pass

admin.site.register([timesheet, Acceptorder, Rejectorder,Customer,acknowledgedstockorder,submitstockorder,punchedprodso,user1, Categories, Sizes, Subcategories, PSizes, punchedprod, queue1, queue2, queue3, Sales,Dailysales, saecat,saesubcate,saesubcats])
