from django import forms
from django.forms import ModelForm
from .models import user1, punchedprod, queue1, Sales,punchedprodso,submitstockorder


class editform(ModelForm):
	class Meta:
		model = user1
		fields = ['user','productname','Category','Subcategory','Size','PSize' ,'Price','Cost','Productimg']
		labels = {
				'user':'user',
				'productname' : 'Prouct Name',
				'Category' : 'Category',
				'Subcategory' : 'Subcategory',
				'Size' : 'Size',
				'PSize' : 'PSize',
				'Price' : 'Price',
				'Cost' : 'Cost',
				'Productimg':'Productimg',
		}
		widgets = {
				'user' : forms.NumberInput(attrs={'class':'form-control clear','type':'hidden','placeholder':'Enter Product Name here...','id':'user1id'}),
				'productname' : forms.TextInput(attrs={'class':'form-control clear','placeholder':'Enter Product Name here...','id':'lagyu'}),
				'Category' : forms.Select(attrs={'class':'form-control clear','placeholder':'Enter Category here...','onchange':'myFunctioncat()','id':'Categ'}),
				'Subcategory' : forms.Select(attrs={'class':'form-control clear','placeholder':'Enter Subcategory here...','onchange':'myFunctionsubcat()','id':'subcateg'}),
				'Size' : forms.Select(attrs={'class':'form-control clear','placeholder':'Enter Size here...'}),
				'PSize' : forms.Select(attrs={'class':'form-control clear','placeholder':'Enter Size here...'}),
				'Price' : forms.NumberInput(attrs={'class':'form-control clear','placeholder':'Enter Price here...'}),
				'Cost' : forms.NumberInput(attrs={'class':'form-control clear','placeholder':'Enter Cost here...'}),
				
		}

class punched(ModelForm):
	class Meta:
		model = punchedprod
		fields = ['user','productname','Category','Subcategory','Size','PSize' ,'Price','Cost','Subtotal','Qty']
		labels = {
				'user':'user',
				'productname' : 'Prouct Name',
				'Category' : 'Category',
				'Subcategory' : 'Subcategory',
				'Size' : 'Size',
				'PSize' : 'PSize',
				'Price' : 'Price',
				'Subtotal' : 'Subtotal',
				'Cost' : 'Cost',
				'Qty' : 'Qty',
		}
		widgets = {
				'user' : forms.NumberInput(attrs={'class':'form-control clear','type':'hidden','placeholder':'Enter Product Name here...','id':'punchedid'}),
				'productname' : forms.TextInput(attrs={'class':'form-control clearname','readonly':'readonly','style':'width:130%;background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':'produktopangalan'}),
				'Category' : forms.TextInput(attrs={'class':'form-control clearcat','readonly':'readonly','style':'background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':'kategorya'}),
				'Subcategory' : forms.TextInput(attrs={'class':'form-control clearsubcat','readonly':'readonly','style':'background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':'subkategorya'}),
				'Size' : forms.TextInput(attrs={'class':'form-control clear','readonly':'readonly','style':'width:135%;background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':'sukatna'}),
				'PSize' : forms.TextInput(attrs={'class':'form-control clear','readonly':'readonly','style':'display:none;width:135%;background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':'psukatna'}),
				'Price' : forms.NumberInput(attrs={'class':'form-control clear','readonly':'readonly','style':'width:130%;background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':'presyona'}),
				'Subtotal' : forms.NumberInput(attrs={'class':'form-control clear','readonly':'readonly','style':'width:120%;background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':'subtotalna'}),
				'Cost' : forms.NumberInput(attrs={'class':'form-control clear', 'type':'hidden','id':'costnaid','name':'costnaname'}),
				'Qty' : forms.NumberInput(attrs={'class':'form-control clear','readonly':'readonly','style':'width:135%;background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':'quantity'}),
		}
class punchedso(ModelForm):
	class Meta:
		model = punchedprodso
		fields = ['user','productname','Category','Subcategory','Size','PSize' ,'Price','Cost','Subtotal','Qty']
		labels = {
				'user':'user',
				'productname' : 'Prouct Name',
				'Category' : 'Category',
				'Subcategory' : 'Subcategory',
				'Size' : 'Size',
				'PSize' : 'PSize',
				'Price' : 'Price',
				'Subtotal' : 'Subtotal',
				'Cost' : 'Cost',
				'Qty' : 'Qty',
		}
		widgets = {
				'user' : forms.NumberInput(attrs={'class':'form-control clear','type':'hidden','placeholder':'Enter Product Name here...','id':'punchedid'}),
				'productname' : forms.TextInput(attrs={'class':'form-control clear','readonly':'readonly','style':'text-align: center;width:130%;background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':'produktopangalan'}),
				'Category' : forms.TextInput(attrs={'class':'form-control clear','readonly':'readonly','style':'text-align: center;width:120%;background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':'kategorya'}),
				'Subcategory' : forms.TextInput(attrs={'class':'form-control clear','readonly':'readonly','style':'text-align: center;width:120%;background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':'subkategorya'}),
				'Size' : forms.TextInput(attrs={'class':'form-control clear','readonly':'readonly','style':'text-align: center;width:135%;background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':'sukatna'}),
				'PSize' : forms.TextInput(attrs={'class':'form-control clear','readonly':'readonly','style':'text-align: center;width:135%;background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':'psukatna'}),
				'Price' : forms.NumberInput(attrs={'class':'form-control clear','readonly':'readonly','style':'text-align: center;width:130%;background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':'presyona'}),
				'Subtotal' : forms.NumberInput(attrs={'class':'form-control clear','readonly':'readonly','style':'text-align: center;width:120%;background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':'subtotalna'}),
				'Cost' : forms.NumberInput(attrs={'class':'form-control clear', 'type':'hidden','id':'costnaid','name':'costnaname'}),
				'Qty' : forms.NumberInput(attrs={'class':'form-control clear','readonly':'readonly','style':'text-align: center;width:135%;background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':'quantity'}),
		}

class stocksandexpenses(ModelForm):
	class Meta:
		model = Sales
		fields = ['user','Categoryaes','Subcategorys','Subcategorye','Amount','Description','Receipt']
		labels = {
				'user':'user',
				'Categoryaes' : 'Categoryaes',
				'Subcategorys' : 'Subcategorys',
				'Subcategorye' : 'Subcategorye',
				'Amount' : 'Amount',
				'Description' : 'Description',
				'Receipt' : 'Receipt',

		}
		widgets = {
				'user' : forms.NumberInput(attrs={'class':'form-control clear','type':'hidden','placeholder':'Enter Product Name here...','id':'user2id'}),
				'Categoryaes' : forms.Select(attrs={'class':'form-control clear','placeholder':'Enter Category here...','onchange':'myFunctioncat()','id':'Categ'}),
				'Subcategorys' : forms.Select(attrs={'class':'form-control clear','placeholder':'Enter Subcategory here...','onchange':'myFunctionsubcats()','id':'subcategs'}),
				'Subcategorye' : forms.Select(attrs={'class':'form-control clear','placeholder':'Enter Subcategory here...','onchange':'myFunctionsubcate()','id':'subcatege'}),
				'Amount' : forms.NumberInput(attrs={'class':'form-control clear','placeholder':'Enter Amount here...','id':'amount'}),
				'Description' : forms.TextInput(attrs={'class':'form-control clear','placeholder':'Enter Description here...','id':'lagyu'}),
				
		}


class stockorderform(ModelForm):
	class Meta:
		model = submitstockorder
		fields = ['user','productname','Category','Price','Cost','Subtotal','Qty','CusName','DeliveryAddress','ShippingFee','contactnumber']

		widgets = {
				'user' : forms.NumberInput(attrs={'class':'form-control clear','type':'hidden','placeholder':'Enter Product Name here...','id':'userrr'}),
				'productname' : forms.TextInput(attrs={'class':'form-control','readonly':'readonly','style':'text-align: center;width:130%;background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':''}),
				'Category' : forms.TextInput(attrs={'class':'form-control','readonly':'readonly','style':'text-align: center;width:120%;background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':''}),
				'Price' : forms.NumberInput(attrs={'class':'form-control','readonly':'readonly','style':'text-align: center;width:130%;background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':''}),
				'Subtotal' : forms.NumberInput(attrs={'class':'form-control','readonly':'readonly','style':'text-align: center;width:120%;background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':''}),
				'Cost' : forms.NumberInput(attrs={'class':'form-control', 'type':'hidden','id':'costnaid','name':'costnaname'}),
				'Qty' : forms.NumberInput(attrs={'class':'form-control','readonly':'readonly','style':'text-align: center;width:135%;background-color:#2d2c29;color:#A0A0A0;border-style:none;','id':''}),
				'CusName' :forms.TextInput(attrs={'class':'form-control','style':'width:500px','placeholder':'Enter your Name'}),
				'DeliveryAddress':forms.TextInput(attrs={'class':'form-control','style':'width:500px;height:30px;','placeholder':'Enter your Delivery Address'}),
				'ShippingFee':forms.NumberInput(attrs={'class':'form-control','style':'width:500px;height:30px;','placeholder':'Enter Shipping Fee here'}),
				'contactnumber':forms.NumberInput(attrs={'class':'form-control','style':'width:500px;height:30px;','placeholder':'Enter your Contact Number'}),
		}
