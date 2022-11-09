from django.db import models
from django.contrib.auth.models import User
import psycopg2
from django.utils import timezone
from datetime import datetime
import pytz
#from django.db.models.manager import Manager as GeoManager

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
    Productimg = models.ImageField(upload_to='media/Productimg',blank = True, null = True)
    def __str__(self):
        return str(self.productname) +" "+ str(self.Size)
      



class punchedprod (models.Model):
    user=models.IntegerField(blank = True, null = True, default='2')
    productname = models.CharField(max_length = 50, blank = True, null = True, default='')
    Category = models.CharField(max_length = 50, blank = True, null = True, default='')
    Subcategory = models.CharField(max_length = 50, default='',blank = True, null = True)
    Size = models.CharField(max_length = 50, default = '',blank = True, null = True)
    PSize = models.CharField(max_length = 50, default = '',blank = True, null = True)
    Price = models.IntegerField(blank = True, null = True, default='')
    Subtotal = models.IntegerField(blank = True, null = True, default='')
    Cost = models.DecimalField(decimal_places=2,max_digits = 7,blank = True, null = True, default='0.00')
    Qty = models.IntegerField(blank = True, null = True, default='')
    DateTime= models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.productname) +" "+ str(self.Size) +" "+ str(self.PSize)

class punchedprodso (models.Model):
    user=models.IntegerField(blank = True, null = True, default='2')
    productname = models.CharField(max_length = 50, blank = True, null = True, default='')
    Category = models.CharField(max_length = 50, blank = True, null = True, default='')
    Subcategory = models.CharField(max_length = 50, default='',blank = True, null = True)
    Size = models.CharField(max_length = 50, default = '',blank = True, null = True)
    PSize = models.CharField(max_length = 50, default = '',blank = True, null = True)
    Price = models.IntegerField(blank = True, null = True, default='')
    Subtotal = models.IntegerField(blank = True, null = True, default='')
    Cost = models.DecimalField(decimal_places=2,max_digits = 7,blank = True, null = True, default='0.00')
    Qty = models.IntegerField(blank = True, null = True, default='')
    DateTime= models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.productname) +" "+ str(self.Size) +" "+ str(self.PSize)

class queue1 (models.Model):
    user=models.IntegerField(blank = True, null = True, default='2')
    productname = models.CharField(max_length = 50, blank = True, null = True, default='')
    Category = models.CharField(max_length = 50, blank = True, null = True, default='')
    Subcategory = models.CharField(max_length = 50, default='',blank = True, null = True)
    Size = models.CharField(max_length = 50, default = '',blank = True, null = True)
    PSize = models.CharField(max_length = 50, default = '',blank = True, null = True)
    Price = models.IntegerField(blank = True, null = True, default='')
    Subtotal = models.IntegerField(blank = True, null = True, default='')
    Cost = models.DecimalField(decimal_places=2,max_digits = 7,blank = True, null = True, default='0.00')
    Qty = models.IntegerField(blank = True, null = True, default='')
    Bill= models.IntegerField(blank = True, null = True, default='0')
    Change= models.IntegerField(blank = True, null = True, default='0')
    CusName=models.CharField(max_length = 50, blank = True, null = True, default='')
    DateTime= models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.productname) +" "+ str(self.Size) +" "+ str(self.PSize)+" "+ str(self.CusName)


class queue2 (models.Model):
    user=models.IntegerField(blank = True, null = True, default='2')
    productname = models.CharField(max_length = 50, blank = True, null = True, default='')
    Category = models.CharField(max_length = 50, blank = True, null = True, default='')
    Subcategory = models.CharField(max_length = 50, default='',blank = True, null = True)
    Size = models.CharField(max_length = 50, default = '',blank = True, null = True)
    PSize = models.CharField(max_length = 50, default = '',blank = True, null = True)
    Price = models.IntegerField(blank = True, null = True, default='')
    Subtotal = models.IntegerField(blank = True, null = True, default='')
    Cost = models.DecimalField(decimal_places=2,max_digits = 7,blank = True, null = True, default='0.00')
    Qty = models.IntegerField(blank = True, null = True, default='')
    Bill= models.IntegerField(blank = True, null = True, default='0')
    Change= models.IntegerField(blank = True, null = True, default='0')
    CusName=models.CharField(max_length = 50, blank = True, null = True, default='')
    DateTime= models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.productname) +" "+ str(self.Size) +" "+ str(self.PSize)+" "+ str(self.CusName)


class queue3 (models.Model):
    user=models.IntegerField(blank = True, null = True, default='2')
    productname = models.CharField(max_length = 50, blank = True, null = True, default='')
    Category = models.CharField(max_length = 50, blank = True, null = True, default='')
    Subcategory = models.CharField(max_length = 50, default='',blank = True, null = True)
    Size = models.CharField(max_length = 50, default = '',blank = True, null = True)
    PSize = models.CharField(max_length = 50, default = '',blank = True, null = True)
    Price = models.IntegerField(blank = True, null = True, default='')
    Subtotal = models.IntegerField(blank = True, null = True, default='')
    Cost = models.DecimalField(decimal_places=2,max_digits = 7,blank = True, null = True, default='0.00')
    Qty = models.IntegerField(blank = True, null = True, default='')
    Bill= models.IntegerField(blank = True, null = True, default='0')
    Change= models.IntegerField(blank = True, null = True, default='0')
    CusName=models.CharField(max_length = 50, blank = True, null = True, default='')
    DateTime= models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.productname) +" "+ str(self.Size) +" "+ str(self.PSize)+" "+ str(self.CusName)
class saesubcate(models.Model):
    saesubcatchoices = models.CharField(max_length=50, blank = False, null = False, default='')
    def __str__(self):
        return str(self.saesubcatchoices)
class saesubcats(models.Model):
    saesubcatchoices = models.CharField(max_length=50, blank = False, null = False, default='')
    def __str__(self):
        return str(self.saesubcatchoices)
        
class saecat(models.Model):
    saecatchoices = models.CharField(max_length=50, blank = False, null = False, default='')
    def __str__(self):
        return str(self.saecatchoices)
        
class Sales (models.Model):
    user=models.IntegerField(blank = True, null = True, default='2')
    productname = models.CharField(max_length = 50, blank = True, null = True, default='')
    Category = models.CharField(max_length = 50, blank = True, null = True, default='')
    Subcategory = models.CharField(max_length = 50, default='',blank = True, null = True)
    Size = models.CharField(max_length = 50, default = '',blank = True, null = True)
    PSize = models.CharField(max_length = 50, default = '',blank = True, null = True)
    Price = models.IntegerField(blank = True, null = True, default='0')
    Subtotal = models.IntegerField(blank = True, null = True, default='0')
    GSubtotal = models.IntegerField(blank = True, null = True, default='0')
    Cost = models.DecimalField(decimal_places=2,max_digits = 7,blank = True, null = True, default='0.00')
    Qty = models.IntegerField(blank = True, null = True, default='0')
    Addons = models.CharField(max_length = 50, default = '',blank = True, null = True)
    QtyAddons = models.IntegerField(blank = True, null = True, default='0')
    Bill= models.IntegerField(blank = True, null = True, default='0')
    Change= models.IntegerField(blank = True, null = True, default='0')
    MOP = models.CharField(max_length = 50, default = '',blank = True, null = True)
    ordertype=models.CharField(max_length = 50, blank = True, null = True, default='Offline')
    gpslat = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00')
    gpslng = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00')
    gpsaccuracy = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00')
    pinnedlat = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00')
    pinnedlng = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00') 
    Province = models.CharField(max_length = 50, blank = True, null = True, default='')
    MunicipalityCity = models.CharField(max_length = 50, blank = True, null = True, default='')
    Barangay = models.CharField(max_length = 50, blank = True, null = True, default='')
    StreetPurok = models.CharField(max_length = 50, blank = True, null = True, default='')
    Housenumber=models.CharField(max_length = 50, blank = True, null = True, default='')
    LandmarksnNotes=models.CharField(max_length = 50, blank = True, null = True, default='')
    ScheduleTime = models.CharField(max_length = 50, blank = True, null = True, default='')
    Timetodeliver = models.CharField(max_length = 50, blank = True, null = True, default='')
    DeliveryFee=models.IntegerField(blank = True, null = True, default='0')
    contactnumber=models.BigIntegerField(blank = True, null = True, default='09000000000')
    CusName=models.CharField(max_length = 50, blank = True, null = True, default='')
    Categoryaes = models.ForeignKey(saecat, on_delete = models.CASCADE, default = '',blank = True, null = True)
    Subcategorys = models.ForeignKey(saesubcats, on_delete = models.CASCADE, default = '',blank = True, null = True)
    Subcategorye = models.ForeignKey(saesubcate, on_delete = models.CASCADE, default = '',blank = True, null = True)
    Amount = models.DecimalField(decimal_places=2,max_digits = 7,blank = True, null = True, default='0.00')
    Description = models.CharField(max_length = 50, blank = True, null = True, default='')
    Receipt = models.ImageField(upload_to='Receipt/%Y/%m/%d',blank = True, null = True)
    tokens= models.CharField(max_length = 300, blank = True, null = True, default='')
    DateTime= models.DateTimeField(default=timezone.now)
    def __str__(self):
        monthconvert=['January','February','March','April','May','June','July','August','September','October','November','December',]
        Monthidentifier=monthconvert[int(self.DateTime.strftime('%m'))-1]
        return Monthidentifier +" "+str(self.DateTime.strftime('%d')) +", "+str(self.DateTime.strftime('%Y'))+"   // "+str(self.user) +" "+ str(self.productname) +" "+ str(self.Size) +" "+ str(self.PSize)+" "+ str(self.CusName)+" "+str(self.Categoryaes)
        
class Dailysales (models.Model):
    user=models.IntegerField(blank = True, null = True, default='2')
    DateTime= models.DateTimeField(default=timezone.now)
    Sales= models.IntegerField(blank = True, null = True, default='0')
    Expenses= models.DecimalField(decimal_places=2,max_digits = 7,blank = True, null = True, default='0.00')
    Startstocks=models.DecimalField(decimal_places=2,max_digits = 7,blank = True, null = True, default='0.00')
    Endstocks=models.DecimalField(decimal_places=2,max_digits = 7,blank = True, null = True, default='0.00')
    Valuestocks=models.DecimalField(decimal_places=2,max_digits = 7,blank = True, null = True, default='0.00')
    Net= models.DecimalField(decimal_places=2,max_digits = 7,blank = True, null = True, default='0.00')

    def __str__(self):
        return str(self.Net)

class submitstockorder (models.Model):
    user=models.IntegerField(blank = True, null = True, default='2')
    productname = models.CharField(max_length = 50, blank = True, null = True, default='')
    Category = models.CharField(max_length = 50, blank = True, null = True, default='')
    Price = models.IntegerField(blank = True, null = True, default='0')
    Subtotal = models.IntegerField(blank = True, null = True, default='0')
    Cost = models.DecimalField(decimal_places=2,max_digits = 7,blank = True, null = True, default='0.00')
    Qty = models.IntegerField(blank = True, null = True, default='0')
    CusName=models.CharField(max_length = 50, blank = True, null = True, default='')
    DeliveryAddress=models.CharField(max_length = 100, blank = True, null = True, default='')
    ShippingFee=models.IntegerField(blank = True, null = True, default='0')
    contactnumber=models.BigIntegerField(blank = True, null = True, default='09000000000')
    DateTime= models.DateTimeField(default=timezone.now)
    def __str__(self):
        return str(self.productname) +" "+ str(self.CusName)
        

class acknowledgedstockorder (models.Model):
    user=models.IntegerField(blank = True, null = True, default='2')
    productname = models.CharField(max_length = 50, blank = True, null = True, default='')
    Category = models.CharField(max_length = 50, blank = True, null = True, default='')
    Price = models.IntegerField(blank = True, null = True, default='0')
    Subtotal = models.IntegerField(blank = True, null = True, default='0')
    Cost = models.DecimalField(decimal_places=2,max_digits = 7,blank = True, null = True, default='0.00')
    Qty = models.IntegerField(blank = True, null = True, default='0')
    CusName=models.CharField(max_length = 50, blank = True, null = True, default='')
    DeliveryAddress=models.CharField(max_length = 100, blank = True, null = True, default='')
    ShippingFee=models.IntegerField(blank = True, null = True, default='0')
    contactnumber=models.BigIntegerField(blank = True, null = True, default='09000000000')
    DateTime= models.DateTimeField(default=timezone.now)
    def __str__(self):
        return str(self.productname) +" "+ str(self.CusName)



class Customer(models.Model):
    Admin=models.IntegerField(blank = True, null = True, default='2')
    Customername = models.CharField(max_length = 50, blank = True, null = True, default='')
    Province = models.CharField(max_length = 50, blank = True, null = True, default='')
    MunicipalityCity = models.CharField(max_length = 50, blank = True, null = True, default='')
    Barangay = models.CharField(max_length = 50, blank = True, null = True, default='')
    StreetPurok = models.CharField(max_length = 50, blank = True, null = True, default='')
    Housenumber=models.CharField(max_length = 50, blank = True, null = True, default='')
    LandmarksnNotes=models.CharField(max_length = 50, blank = True, null = True, default='')
    DeliveryFee=models.IntegerField(blank = True, null = True, default='0')
    contactnumber=models.BigIntegerField(blank = True, null = True, default='09000000000')
    Bill=models.IntegerField(blank = True, null = True, default='0')
    Change= models.IntegerField(blank = True, null = True, default='0')
    productname = models.CharField(max_length = 50, blank = True, null = True, default='')
    Category = models.CharField(max_length = 50, blank = True, null = True, default='')
    Subcategory = models.CharField(max_length = 50, blank = True, null = True, default='')
    Size = models.CharField(max_length = 50, default = '',blank = True, null = True)
    Addons = models.CharField(max_length = 50, default = '',blank = True, null = True)
    QtyAddons = models.IntegerField(blank = True, null = True, default='0')
    PSize = models.CharField(max_length = 50, default = '',blank = True, null = True)
    Price = models.IntegerField(blank = True, null = True, default='0')
    Subtotal = models.IntegerField(blank = True, null = True, default='0')
    GSubtotal = models.IntegerField(blank = True, null = True, default='0')
    Cost = models.DecimalField(decimal_places=2,max_digits = 7,blank = True, null = True, default='0.00')
    Qty = models.IntegerField(blank = True, null = True, default='0')
    MOP = models.CharField(max_length = 50, default = '',blank = True, null = True)
    ordertype = models.CharField(max_length = 50, default = '',blank = True, null = True)
    Timetodeliver = models.CharField(max_length = 50, default = '',blank = True, null = True)
    ScheduleTime = models.CharField(max_length = 50, default = '',blank = True, null = True)
    gpslat = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00')
    gpslng = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00')
    gpsaccuracy = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00')
    pinnedlat = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00')
    pinnedlng = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00')
    tokens= models.CharField(max_length = 300, blank = True, null = True, default='')
    DateTime= models.DateTimeField(default=timezone.now)
    def __str__(self):

        return str(self.productname) +" / "+ str(self.Customername)+" / "+ str(self.Admin)+" / "+ str(self.Barangay)

class Acceptorder(models.Model):
    Admin=models.IntegerField(blank = True, null = True, default='2')
    Customername = models.CharField(max_length = 50, blank = True, null = True, default='')
    Province = models.CharField(max_length = 50, blank = True, null = True, default='')
    MunicipalityCity = models.CharField(max_length = 50, blank = True, null = True, default='')
    Barangay = models.CharField(max_length = 50, blank = True, null = True, default='')
    StreetPurok = models.CharField(max_length = 50, blank = True, null = True, default='')
    Housenumber=models.CharField(max_length = 50, blank = True, null = True, default='')
    LandmarksnNotes=models.CharField(max_length = 50, blank = True, null = True, default='')
    DeliveryFee=models.IntegerField(blank = True, null = True, default='0')
    Rider = models.CharField(max_length = 50, blank = True, null = True, default='')
    contactnumber=models.BigIntegerField(blank = True, null = True, default='09000000000')
    Bill=models.IntegerField(blank = True, null = True, default='0')
    Change= models.IntegerField(blank = True, null = True, default='0')
    ETA = models.CharField(max_length = 50, blank = True, null = True, default='')
    productname = models.CharField(max_length = 50, blank = True, null = True, default='')
    Category = models.CharField(max_length = 50, blank = True, null = True, default='')
    Subcategory = models.CharField(max_length = 50, blank = True, null = True, default='')
    Size = models.CharField(max_length = 50, default = '',blank = True, null = True)
    Addons = models.CharField(max_length = 50, default = '',blank = True, null = True)
    QtyAddons = models.IntegerField(blank = True, null = True, default='0')
    PSize = models.CharField(max_length = 50, default = '',blank = True, null = True)
    Price = models.IntegerField(blank = True, null = True, default='0')
    Subtotal = models.IntegerField(blank = True, null = True, default='0')
    GSubtotal = models.IntegerField(blank = True, null = True, default='0')
    Cost = models.DecimalField(decimal_places=2,max_digits = 7,blank = True, null = True, default='0.00')
    Qty = models.IntegerField(blank = True, null = True, default='0')
    MOP = models.CharField(max_length = 50, default = '',blank = True, null = True)
    ordertype = models.CharField(max_length = 50, default = '',blank = True, null = True)
    Timetodeliver = models.CharField(max_length = 50, default = '',blank = True, null = True)
    ScheduleTime = models.CharField(max_length = 50, default = '',blank = True, null = True)
    gpslat = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00')
    gpslng = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00')
    gpsaccuracy = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00')
    pinnedlat = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00')
    pinnedlng = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00')
    tokens= models.CharField(max_length = 300, blank = True, null = True, default='')
    DateTime= models.DateTimeField(default=timezone.now)
    def __str__(self):

        return str(self.productname) +" / "+ str(self.Customername)+" / "+ str(self.Admin)+" / "+ str(self.Barangay)
        
class Rejectorder(models.Model):
    Admin=models.IntegerField(blank = True, null = True, default='2')
    Customername = models.CharField(max_length = 50, blank = True, null = True, default='')
    Province = models.CharField(max_length = 50, blank = True, null = True, default='')
    MunicipalityCity = models.CharField(max_length = 50, blank = True, null = True, default='')
    Barangay = models.CharField(max_length = 50, blank = True, null = True, default='')
    StreetPurok = models.CharField(max_length = 50, blank = True, null = True, default='')
    Housenumber=models.CharField(max_length = 50, blank = True, null = True, default='')
    LandmarksnNotes=models.CharField(max_length = 50, blank = True, null = True, default='')
    DeliveryFee=models.IntegerField(blank = True, null = True, default='0')
    contactnumber=models.BigIntegerField(blank = True, null = True, default='09000000000')
    Bill=models.IntegerField(blank = True, null = True, default='0')
    Change= models.IntegerField(blank = True, null = True, default='0')
    productname = models.CharField(max_length = 50, blank = True, null = True, default='')
    Category = models.CharField(max_length = 50, blank = True, null = True, default='')
    Subcategory = models.CharField(max_length = 50, blank = True, null = True, default='')
    Size = models.CharField(max_length = 50, default = '',blank = True, null = True)
    Addons = models.CharField(max_length = 50, default = '',blank = True, null = True)
    QtyAddons = models.IntegerField(blank = True, null = True, default='0')
    PSize = models.CharField(max_length = 50, default = '',blank = True, null = True)
    Price = models.IntegerField(blank = True, null = True, default='0')
    Subtotal = models.IntegerField(blank = True, null = True, default='0')
    GSubtotal = models.IntegerField(blank = True, null = True, default='0')
    Cost = models.DecimalField(decimal_places=2,max_digits = 7,blank = True, null = True, default='0.00')
    Qty = models.IntegerField(blank = True, null = True, default='0')
    MOP = models.CharField(max_length = 50, default = '',blank = True, null = True)
    ordertype = models.CharField(max_length = 50, default = '',blank = True, null = True)
    Timetodeliver = models.CharField(max_length = 50, default = '',blank = True, null = True)
    ScheduleTime = models.CharField(max_length = 50, default = '',blank = True, null = True)
    gpslat = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00')
    gpslng = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00')
    gpsaccuracy = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00')
    pinnedlat = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00')
    pinnedlng = models.DecimalField(decimal_places=20,max_digits = 50,blank = True, null = True, default='0.00')
    tokens= models.CharField(max_length = 300, blank = True, null = True, default='')
    DateTime= models.DateTimeField(default=timezone.now)
    def __str__(self):

        return str(self.productname) +" / "+ str(self.Customername)+" / "+ str(self.Admin)+" / "+ str(self.Barangay)


class timesheet(models.Model):
    Admin=models.IntegerField(blank = True, null = True, default='2')
    Employeename = models.CharField(max_length = 50, blank = True, null = True, default='')
    Day = models.CharField(max_length = 50, blank = True, null = True, default='')
    Timein = models.CharField(max_length = 50, blank = True, null = True, default='')
    Timeout = models.CharField(max_length = 50, blank = True, null = True, default='')
    Totalmins = models.IntegerField(blank = True, null = True, default='0')
    Productimg = models.ImageField(upload_to='Employeeattendance',blank = True, null = True)
    Sales = models.IntegerField(blank = True, null = True, default='0')
    Identifybonus = models.CharField(max_length = 50, blank = True, null = True, default='No Bonus')
    ASLbalance = models.IntegerField(blank = True, null = True, default='0')
    ISalary=models.IntegerField(blank = True, null = True, default='0')
    FSalary=models.IntegerField(blank = True, null = True, default='0')
    DateTime= models.DateTimeField(default=timezone.now)
    def __str__(self): 
        monthconvert=['January','February','March','April','May','June','July','August','September','October','November','December',]
        Monthidentifier=monthconvert[int(self.DateTime.strftime('%m'))-1]
        return Monthidentifier +" "+str(self.DateTime.strftime('%d')) +", "+str(self.DateTime.strftime('%Y'))+"   // "+ str(self.Admin)+" "+ str(self.Employeename)

