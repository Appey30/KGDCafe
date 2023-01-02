"""ProjectAutomation URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import TemplateView
from AutomationApp import views
from django.contrib.auth import views as auth_views 


urlpatterns = [

      path('admin/',admin.site.urls),
      path('index/',views.login_user,name='index.html'),
      path('',views.redirecttoonlineorder,name='Onlineorder.html'),
	  path('index/kgdlog', views.login_user,name='kgdlog'),
	  path('index/products',views.products,name='Products.html'),
      path('checkout/',views.checkout,name='checkout.html'),
      path('index/coupon',views.coupon,name='coupon.html'),
      path('index/posthree',views.posthree,name='posthree.html'),
      path('index/pos',views.postwo,name='postwo.html'),
      path('index/onlineorder/<int:admin_id>/',views.Onlineordersystem,name='Onlineorder.html'),
      path('index/onlineordertesting/<int:admin_id>/',views.Onlineordertestingsystem,name='Onlineordertesting.html'),
      #path('index/postwo',views.postwo,name='postwo.html'),
      path('index/inventory',views.inventory,name='inventory.html'),
      path('index/kgddashboard',views.kgddashboard,name='kgddashboard.html'),
      path('index/products/delete/', include ('AutomationApp.urls', namespace = 'modaldel')),
      path('index/products/', include ('AutomationApp.urls', namespace = 'modaledit')),
      path('messengershop/', include ('AutomationApp.urls', namespace = 'messenger')),
      #path('messengersubscribe/',views.messengerlogin,name='messengerloginbot.html'),
      path('index/StocksandExp',views.StocksandExp,name='StocksandExp.html'),
      path('index/Stocksorder',views.StocksOrder,name='StockOrder.html'),
      path('index/Stocksorderadmin',views.stockorderad,name='stockorderadmin.html'),
      path('index/Rider',views.RiderPOV,name='Rider.html'),
      path('index/onlineorder/<int:admin_id>/OrderProgress/',views.orderprogress,name='orderprogress.html'),
      path('index/TermsandConditions',views.TermsandConditions,name='TermsandConditions.html'),
      path('index/PrivacyPolicy',views.PrivacyPolicy,name='privacypolicy.html'),
      path('index/saletoday',views.saletoday,name='saletoday.html'),
      path('index/staff',views.staff,name='staff.html'),
      path('index/marketing',views.marketingaspect,name='Marketing.html'),
      path('index/appeybought',views.totalboughtappey,name='totalboughtappey.html'),
      path('oauth/', include('social_django.urls', namespace='social')),
      path('logout/', auth_views.LogoutView.as_view(next_page='../index/onlineorder/4/'),name='logout'),
      #path('login/', auth_views.LoginView.as_view(next_page=''),name='login'),
      #path('logout/', views.logout.as_view(next_page='home'),name='logout'),
      #path('accounts/', include('allauth.urls')),
      #FIREBASE AREA
      path('index/onlineorder/<int:admin_id>/submitted' , views.submitted, name="submittedorder"),
      #path('api/fb/webhook/85f449d37a9f01958ed52ed4b0491315f6fbbf7b7bebba424f96b9f23bc9/', views.FacebookWebhookView.as_view(), name='webhook'),
      path('api/fb/webhook/', include ('AutomationApp.urls', namespace = 'bot')),
      
      #path('firebase-messaging-sw.js',views.showFirebaseJS,name="show_firebase_js"),
      
              ]
if settings.DEBUG: # new
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
