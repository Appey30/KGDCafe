from django.urls import path, re_path
from . import views

app_name = "AutomationApp"
urlpatterns = [

#path('add',views.addproduct, name='addprod.html'), 
#path('/<str:prodd_id>', views.dproduct , name='deleteprod'),
path('<int:del_id>', views.delprod , name='delprod'),
path('edit/<int:edit_id>', views.editprod , name='editprod'),
path('item/<int:product_id>', views.messengercafe , name='items'),
#re_path(r'^api/fb/webhook/85f449d37a9f01958ed52ed4b0491315f6fbbf7b7bebba424f96b9f23bc9/$', views.FacebookWebhookView.as_view(), name='webhook'),
#re_path(r'^webhook/85f449d37a9f01958ed52ed4b0491315f6fbbf7b7bebba424f96b9f23bc9/$', views.FacebookWebhookView.as_view(), name='webhook'),
re_path(r'^85f449d37a9f01958ed52ed4b0491315f6fbbf7b7bebba424f96b9f23bc9/?$', views.FacebookWebhookView.as_view()) 
]
