from django.db import models
from django.contrib.auth.models import User
import psycopg2
from django.utils import timezone
from datetime import datetime
import pytz
# Create your models here.

class Subcategories(models.Model):
    Subcategorychoices = models.CharField(max_length = 50, blank = False, null = False, default='')
    def __str__(self):
        return str(self.Subcategorychoices)

class Categories(models.Model):
    Categorychoices = models.CharField(max_length = 50, blank = False, null = False, default='')
    def __str__(self):
        return str(self.Categorychoices)

class Sizes(models.Model):
    Sizechoices = models.CharField(max_length=50, blank = False, null = False, default='')
    def __str__(self):
        return str(self.Sizechoices)

class PSizes(models.Model):
    PSizechoices = models.CharField(max_length=50, blank = False, null = False, default='')
    def __str__(self):
        return str(self.PSizechoices)


class user1 (models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE,blank = False, null = False)
    productname = models.CharField(max_length = 50, blank = False, null = False, default='')
    Category = models.ForeignKey(Categories, on_delete=models.CASCADE, default='',blank = True, null = True)
    Subcategory = models.ForeignKey(Subcategories, on_delete=models.CASCADE, default='',blank = True, null = True)
    Size = models.ForeignKey(Sizes, on_delete = models.CASCADE, default = '',blank = True, null = True)
    PSize = models.ForeignKey(PSizes, on_delete = models.CASCADE, default = '',blank = True, null = True)
    Price = models.IntegerField(blank = False, null = False, default='')
    Cost = models.DecimalField(decimal_places=2,max_digits = 7,blank = False, null = False, default='0.00')
    Qty = models.IntegerField(blank = False, null = False, default='1')
    Promo = models.CharField(max_length = 50, blank = False, null = False, default='')
    Productimg = models.ImageField(upload_to='Productimg',blank = True, null = True)
    def __str__(self):
        return str(self.productname) +" "+ str(self.Size)