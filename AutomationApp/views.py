from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import auth, User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import timesheet, Acceptorder, Rejectorder,Customer, acknowledgedstockorder,submitstockorder, user1, Categories, Sizes, Subcategories, PSizes, punchedprod,punchedprodso,queue1, queue2, queue3, Sales, Dailysales, couponlist
from .forms import editform, punched,punchedso, stocksandexpenses,stockorderform
from django.db.models.functions import (TruncDate, TruncDay, TruncHour, TruncMinute, TruncSecond)
from django.urls import reverse
import copy, pickle
import random
from django.http import JsonResponse
from django.db.models import Sum, F
import datetime
import pytz
from django.utils import timezone
from django.conf import settings
import os, errno
from django.utils.timezone import localtime 
from django.contrib.auth.decorators import login_required
#from webpos import settings
from collections import namedtuple
from qrcode import *
import json
import requests, re
from django.core import serializers
from decimal import Decimal
from pyfcm import FCMNotification
#from allauth.socialaccount.models import SocialAccount
from django.db.models.functions import Lower
#from allauth.socialaccount.models import SocialApp
from django.contrib.auth.hashers import make_password
from django.template import *
from PIL import Image
from io import BytesIO
import base64
import string
from django.utils.encoding import smart_str
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .logic import LOGIC_RESPONSES
from pprint import pprint
from django.utils.datastructures import MultiValueDictKeyError

PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')


# Helper function
def handleMessage(fbid, response):
    post_message_url = 'https://graph.facebook.com/v15.0/me/messages?access_token=%s'%PAGE_ACCESS_TOKEN
    textorattachment=response.get('text',[]);
    if textorattachment:
        jokes = { 'hi': ["""hello """, 
                             """hello!"""], 
                 'hello':      ["""hi """, 
                              """ hi!"""], 
                 }

        # Remove all punctuations, lower case the text and split it based on space
        tokens = re.sub(r"[^a-zA-Z0-9\s]",' ',response['text']).lower().split()
        joke_text = ''
        for token in tokens:
            if token in jokes:
                joke_text = random.choice(jokes[token])
                break
        if not joke_text:
        
            joke_text = "I didn't understand!!" 

        user_details_url = "https://graph.facebook.com/v15.0/%s"%fbid+'?fields=first_name,last_name&access_token=%s'%PAGE_ACCESS_TOKEN
        user_details_params = {'fields':'first_name,last_name', 'access_token':PAGE_ACCESS_TOKEN} 
        user_details = requests.get(user_details_url, user_details_params).json() 
    
        try:
            userdetailsfirstname=user_details['first_name']
        

        except KeyError:
            userdetailsfirstname="Ma'am/Sir"
        
        joke_text = joke_text+', '+userdetailsfirstname+'..! '
    
        
        response_msg = json.dumps({
        "recipient":{"id":fbid}, 
        "message":{"text":joke_text}
        })
    elif response.get('attachments'):
        
        attachments=response.get('attachments',[])
        for attachmentsfinal in attachments:
            if attachmentsfinal['type'] == 'image':
                attachment_url = attachmentsfinal['payload']['url']
                response_msg = json.dumps({
                    "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "generic",
                        "elements": [{
                        "title": "Did you send this pic?",
                        "subtitle": "Tap a button to answer.",
                        "image_url": attachment_url,
                        "buttons": [
                            {
                            "type": "postback",
                            "title": "Yes!",
                            "payload": "yes",
                            },
                            {
                            "type": "postback",
                            "title": "No!",
                            "payload": "no",
                            }
                        ],
                        }]
                    }
                    }
                })
    else:
        pass
    if userdetailsfirstname == 'Appey':
        status = requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg)
        print(status.json())
    else:
        pass

def handlePostback(fbid, received_postback):
    print('handlepostback called received_postback value is: ',received_postback)
    payload = received_postback.payload;

    if payload == 'yes':
        response_msg = { "text": "Your answer is YES!" }
    elif payload == 'no':
        response_msg = { "text": "Your answer is No!" }

    if userdetailsfirstname == 'Appey':
        status = requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg)
        print(status.json())
    else:
        pass

def set_get_started_button():
    post_message_url = 'https://graph.facebook.com/v15.0/me/messenger_profile?access_token=%s'%PAGE_ACCESS_TOKEN
    payload = {
        "get_started": {
            "payload": "GET_STARTED"
        }
    }

    #params = {
    #"access_token": ACCESS_TOKEN
    #}
    if userdetailsfirstname == 'Appey':
        status = requests.post(post_message_url, headers={"Content-Type": "application/json"},data=payload)
        print(status.json())
    else:
        pass
    #requests.post(url, json=payload, headers=headers)

# Create your views here.
class FacebookWebhookView(View):
    def get(self, request, *args, **kwargs):
        try:
            token=self.request.GET['hub.verify_token']
        except MultiValueDictKeyError:
            token=False
        try:
            mode=self.request.GET['hub.mode']
        except MultiValueDictKeyError:
            mode=False
        if token == VERIFY_TOKEN and mode=='subscribe':
            print('Congrats! Webhook_verified')
            return HttpResponse('Challenge: '+self.request.GET['hub.challenge']+'     mode: '+mode)
        else:
            print('hub.verify_token: ',token)
            return HttpResponse('Error, invalid token')
        
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return View.dispatch(self, request, *args, **kwargs)


    # Post function to handle Facebook messages
    def post(self, request, *args, **kwargs):

        # Converts the text payload into a python dictionary
        incoming_message = json.loads(self.request.body.decode('utf-8'))
        
        # Facebook recommends going through every entry since they might send
        # multiple messages in a single call during high load
        for entry in incoming_message['entry']:
            for message in entry['messaging']:
                # Check to make sure the received call is a message call
                # This might be delivery, optin, postback for other events 
                
                if 'message' in message:
                    
                    # Print the message to the terminal
                    print(message) 
                    print('MESSAGE_SENDER_ID: ',message['sender']['id'])
                    print('MESSAGE_text: ',message['message'])
                    # Assuming the sender only sends text. Non-text messages like stickers, audio, pictures
                    # are sent as attachments and must be handled accordingly. 

                    handleMessage(message['sender']['id'], message['message'])
                elif 'postback' in message:
                    handlePostback(message['sender']['id'], message['postback'])
    
        
                    

                
        return HttpResponse()    








########################################################




def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

def PrivacyPolicy(request):
    userr=request.user.id
    return render(request, 'privacypolicy.html')

def TermsandConditions(request):
    userr=request.user.id
    return render(request, 'TermsandConditions.html')


def redirecttoonlineorder(request):
    userr=request.user.id
    promocodegeti=request.GET.get('prmcd', '')
    
    if promocodegeti:
        return HttpResponseRedirect('/index/onlineorder/4/?prmcd='+promocodegeti)
    else:
        return HttpResponseRedirect('/index/onlineorder/4/')

@login_required
def totalboughtappey(request):
    userr=request.user.id
    datetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
    monthtoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m')
    yeartoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y')
    boughtjoy=Sales.objects.filter(CusName='Joy Macapinlac', DateTime__month=monthtoday, DateTime__year = yeartoday).aggregate(Sum('Subtotal')).get('Subtotal__sum')
    boughtappey=Sales.objects.filter(CusName='Appey De Guzman', DateTime__month=monthtoday, DateTime__year = yeartoday).aggregate(Sum('Subtotal')).get('Subtotal__sum')
    boughtcontainsappey=Sales.objects.filter(CusName__contains='appey', DateTime__month=monthtoday, DateTime__year = yeartoday).aggregate(Sum('Subtotal')).get('Subtotal__sum')
    print('boughtjoy: ',boughtjoy)
    print('boughtappey: ',boughtappey)
    print('boughtcontainsappey: ',boughtcontainsappey)
    return render(request, 'totalboughtappey.html',{'boughtappey':boughtappey})

@login_required
def marketingaspect(request):
    userr=request.user.id
    datetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
    monthtoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m')
    yeartoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y')
    try:
        january=User.objects.filter(date_joined__year='2022',date_joined__month='01').exclude(username='kylie12').exclude(username='kylie ROSE').exclude(username='kylie').exclude(username='appey30').exclude(username='Moneth50!').exclude(username='Moneth50').exclude(username='Moneth').exclude(username='Mjmacapinlac').exclude(username='MaryJoyMacapinlac').exclude(username='MJMacapinlac').exclude(username='MJAraezMacapinlac').exclude(username='MJ24').exclude(username='Kylie Rose').exclude(username='Kimjasper30').exclude(username='KimJasperDeGuzman').exclude(username='KGDCafe28').exclude(username='AppeyGDeGuzman').distinct('username').count()
    except User.DoesNotExist:
        january=0
    try:
        february=User.objects.filter(date_joined__year='2022',date_joined__month='02').exclude(username='kylie12').exclude(username='kylie ROSE').exclude(username='kylie').exclude(username='appey30').exclude(username='Moneth50!').exclude(username='Moneth50').exclude(username='Moneth').exclude(username='Mjmacapinlac').exclude(username='MaryJoyMacapinlac').exclude(username='MJMacapinlac').exclude(username='MJAraezMacapinlac').exclude(username='MJ24').exclude(username='Kylie Rose').exclude(username='Kimjasper30').exclude(username='KimJasperDeGuzman').exclude(username='KGDCafe28').exclude(username='AppeyGDeGuzman').distinct('username').count()
    except User.DoesNotExist:
        february=0
    try:
        march=User.objects.filter(date_joined__year='2022',date_joined__month='03').exclude(username='kylie12').exclude(username='kylie ROSE').exclude(username='kylie').exclude(username='appey30').exclude(username='Moneth50!').exclude(username='Moneth50').exclude(username='Moneth').exclude(username='Mjmacapinlac').exclude(username='MaryJoyMacapinlac').exclude(username='MJMacapinlac').exclude(username='MJAraezMacapinlac').exclude(username='MJ24').exclude(username='Kylie Rose').exclude(username='Kimjasper30').exclude(username='KimJasperDeGuzman').exclude(username='KGDCafe28').exclude(username='AppeyGDeGuzman').distinct('username').count()
    except User.DoesNotExist:
        march=0
    try:
        april=User.objects.filter(date_joined__year='2022',date_joined__month='04').exclude(username='kylie12').exclude(username='kylie ROSE').exclude(username='kylie').exclude(username='appey30').exclude(username='Moneth50!').exclude(username='Moneth50').exclude(username='Moneth').exclude(username='Mjmacapinlac').exclude(username='MaryJoyMacapinlac').exclude(username='MJMacapinlac').exclude(username='MJAraezMacapinlac').exclude(username='MJ24').exclude(username='Kylie Rose').exclude(username='Kimjasper30').exclude(username='KimJasperDeGuzman').exclude(username='KGDCafe28').exclude(username='AppeyGDeGuzman').distinct('username').count()
    except User.DoesNotExist:
        april=0
    try:
        may=User.objects.filter(date_joined__year='2022',date_joined__month='05').exclude(username='kylie12').exclude(username='kylie ROSE').exclude(username='kylie').exclude(username='appey30').exclude(username='Moneth50!').exclude(username='Moneth50').exclude(username='Moneth').exclude(username='Mjmacapinlac').exclude(username='MaryJoyMacapinlac').exclude(username='MJMacapinlac').exclude(username='MJAraezMacapinlac').exclude(username='MJ24').exclude(username='Kylie Rose').exclude(username='Kimjasper30').exclude(username='KimJasperDeGuzman').exclude(username='KGDCafe28').exclude(username='AppeyGDeGuzman').distinct('username').count()
    except User.DoesNotExist:
        may=0
    try:
        june=User.objects.filter(date_joined__year='2022',date_joined__month='06').exclude(username='kylie12').exclude(username='kylie ROSE').exclude(username='kylie').exclude(username='appey30').exclude(username='Moneth50!').exclude(username='Moneth50').exclude(username='Moneth').exclude(username='Mjmacapinlac').exclude(username='MaryJoyMacapinlac').exclude(username='MJMacapinlac').exclude(username='MJAraezMacapinlac').exclude(username='MJ24').exclude(username='Kylie Rose').exclude(username='Kimjasper30').exclude(username='KimJasperDeGuzman').exclude(username='KGDCafe28').exclude(username='AppeyGDeGuzman').distinct('username').count()
    except User.DoesNotExist:
        june=0
    try:
        july=User.objects.filter(date_joined__year='2022',date_joined__month='07').exclude(username='kylie12').exclude(username='kylie ROSE').exclude(username='kylie').exclude(username='appey30').exclude(username='Moneth50!').exclude(username='Moneth50').exclude(username='Moneth').exclude(username='Mjmacapinlac').exclude(username='MaryJoyMacapinlac').exclude(username='MJMacapinlac').exclude(username='MJAraezMacapinlac').exclude(username='MJ24').exclude(username='Kylie Rose').exclude(username='Kimjasper30').exclude(username='KimJasperDeGuzman').exclude(username='KGDCafe28').exclude(username='AppeyGDeGuzman').distinct('username').count()
    except User.DoesNotExist:
        july=0
    try:
        august=User.objects.filter(date_joined__year='2022',date_joined__month='08').exclude(username='kylie12').exclude(username='kylie ROSE').exclude(username='kylie').exclude(username='appey30').exclude(username='Moneth50!').exclude(username='Moneth50').exclude(username='Moneth').exclude(username='Mjmacapinlac').exclude(username='MaryJoyMacapinlac').exclude(username='MJMacapinlac').exclude(username='MJAraezMacapinlac').exclude(username='MJ24').exclude(username='Kylie Rose').exclude(username='Kimjasper30').exclude(username='KimJasperDeGuzman').exclude(username='KGDCafe28').exclude(username='AppeyGDeGuzman').distinct('username').count()
    except User.DoesNotExist:
        august=0
    try:
        september=User.objects.filter(date_joined__year='2022',date_joined__month='09').exclude(username='kylie12').exclude(username='kylie ROSE').exclude(username='kylie').exclude(username='appey30').exclude(username='Moneth50!').exclude(username='Moneth50').exclude(username='Moneth').exclude(username='Mjmacapinlac').exclude(username='MaryJoyMacapinlac').exclude(username='MJMacapinlac').exclude(username='MJAraezMacapinlac').exclude(username='MJ24').exclude(username='Kylie Rose').exclude(username='Kimjasper30').exclude(username='KimJasperDeGuzman').exclude(username='KGDCafe28').exclude(username='AppeyGDeGuzman').distinct('username').count()
    except User.DoesNotExist:
        september=0
    try:
        october=User.objects.filter(date_joined__year='2022',date_joined__month='10').exclude(username='kylie12').exclude(username='kylie ROSE').exclude(username='kylie').exclude(username='appey30').exclude(username='Moneth50!').exclude(username='Moneth50').exclude(username='Moneth').exclude(username='Mjmacapinlac').exclude(username='MaryJoyMacapinlac').exclude(username='MJMacapinlac').exclude(username='MJAraezMacapinlac').exclude(username='MJ24').exclude(username='Kylie Rose').exclude(username='Kimjasper30').exclude(username='KimJasperDeGuzman').exclude(username='KGDCafe28').exclude(username='AppeyGDeGuzman').distinct('username').count()
    except User.DoesNotExist:
        october=0
    try:
        november=User.objects.filter(date_joined__year='2022',date_joined__month='11').exclude(username='kylie12').exclude(username='kylie ROSE').exclude(username='kylie').exclude(username='appey30').exclude(username='Moneth50!').exclude(username='Moneth50').exclude(username='Moneth').exclude(username='Mjmacapinlac').exclude(username='MaryJoyMacapinlac').exclude(username='MJMacapinlac').exclude(username='MJAraezMacapinlac').exclude(username='MJ24').exclude(username='Kylie Rose').exclude(username='Kimjasper30').exclude(username='KimJasperDeGuzman').exclude(username='KGDCafe28').exclude(username='AppeyGDeGuzman').distinct('username').count()
    except User.DoesNotExist:
        november=0
    try:
        december=User.objects.filter(date_joined__year='2022',date_joined__month='12').exclude(username='kylie12').exclude(username='kylie ROSE').exclude(username='kylie').exclude(username='appey30').exclude(username='Moneth50!').exclude(username='Moneth50').exclude(username='Moneth').exclude(username='Mjmacapinlac').exclude(username='MaryJoyMacapinlac').exclude(username='MJMacapinlac').exclude(username='MJAraezMacapinlac').exclude(username='MJ24').exclude(username='Kylie Rose').exclude(username='Kimjasper30').exclude(username='KimJasperDeGuzman').exclude(username='KGDCafe28').exclude(username='AppeyGDeGuzman').distinct('username').count()
    except User.DoesNotExist:
        december=0
    total=int(january)+int(february)+int(march)+int(april)+int(may)+int(june)+int(july)+int(august)+int(september)+int(october)+int(november)+int(december)
    #########Repeat Orders############
    try:
        januaryROii=Sales.objects.filter(DateTime__year='2022',DateTime__month='01').exclude(CusName__contains='Appey').exclude(CusName__contains='KGD').exclude(CusName__contains='Kim Jasper').exclude(CusName__contains='Kylie').exclude(CusName__contains='MJ Arañez Macapinlac').exclude(CusName__contains='Maryjoy Macapinlac').exclude(CusName__contains='Mary Joy Macapinlac').exclude(CusName__contains='MJ Macapinlac').exclude(CusName__contains='Moneth	De guzman').exclude(CusName__contains='Ramonita	De Guzman').exclude(CusName__contains='Monet De Guzman').exclude(CusName__contains='kylie rose Deguzman').exclude(CusName__contains='kylie Rose G De GUZMAN').exclude(CusName__contains='kylie heart').exclude(CusName__contains='kylie heart').values_list('contactnumber',flat=True)
        jancountRO=0
        MAINjanROcounts=0
        while jancountRO<januaryROii.count():
            januaryROi=Sales.objects.filter(DateTime__year='2022',DateTime__month='01',contactnumber=januaryROii[jancountRO]).annotate(date=TruncDate('DateTime'),day=TruncDay('DateTime'),hour=TruncHour('DateTime'),minute=TruncMinute('DateTime')).values_list('date', flat=True).distinct().count()
            if januaryROi==2:
                MAINjanROcounts+=1
            jancountRO+=1
    except Sales.DoesNotExist:
        MAINjanROcounts=0
    try:
        februaryROii=Sales.objects.filter(DateTime__year='2022',DateTime__month='02' or '01').exclude(CusName__contains='Appey').exclude(CusName__contains='KGD').exclude(CusName__contains='Kim Jasper').exclude(CusName__contains='Kylie').exclude(CusName__contains='MJ Arañez Macapinlac').exclude(CusName__contains='Maryjoy Macapinlac').exclude(CusName__contains='Mary Joy Macapinlac').exclude(CusName__contains='MJ Macapinlac').exclude(CusName__contains='Moneth	De guzman').exclude(CusName__contains='Ramonita	De Guzman').exclude(CusName__contains='Monet De Guzman').exclude(CusName__contains='kylie rose Deguzman').exclude(CusName__contains='kylie Rose G De GUZMAN').exclude(CusName__contains='kylie heart').exclude(CusName__contains='kylie heart').values_list('contactnumber',flat=True)
        febcountRO=0
        MAINfebROcounts=0
        while febcountRO<februaryROii.count():
            febuaryROi=Sales.objects.filter(DateTime__year='2022',DateTime__month='02' or '01',contactnumber=febuaryROii[febcountRO]).annotate(date=TruncDate('DateTime'),day=TruncDay('DateTime'),hour=TruncHour('DateTime'),minute=TruncMinute('DateTime')).values_list('date', flat=True).distinct().count()
            if febuaryROi==2:
                MAINfebROcounts+=1
            febcountRO+=1
    except Sales.DoesNotExist:
        MAINfebROcounts=0
    try:
        marchROii=Sales.objects.filter(DateTime__year='2022',DateTime__month='03' or '02').exclude(CusName__contains='Appey').exclude(CusName__contains='KGD').exclude(CusName__contains='Kim Jasper').exclude(CusName__contains='Kylie').exclude(CusName__contains='MJ Arañez Macapinlac').exclude(CusName__contains='Maryjoy Macapinlac').exclude(CusName__contains='Mary Joy Macapinlac').exclude(CusName__contains='MJ Macapinlac').exclude(CusName__contains='Moneth	De guzman').exclude(CusName__contains='Ramonita	De Guzman').exclude(CusName__contains='Monet De Guzman').exclude(CusName__contains='kylie rose Deguzman').exclude(CusName__contains='kylie Rose G De GUZMAN').exclude(CusName__contains='kylie heart').exclude(CusName__contains='kylie heart').values_list('contactnumber',flat=True)
        marcountRO=0
        MAINmarROcounts=0
        while marcountRO<marchROii.count():
            marchROi=Sales.objects.filter(DateTime__year='2022',DateTime__month='03' or '02',contactnumber=marchROii[marcountRO]).annotate(date=TruncDate('DateTime'),day=TruncDay('DateTime'),hour=TruncHour('DateTime'),minute=TruncMinute('DateTime')).values_list('date', flat=True).distinct().count()
            if marchROi==2:
                MAINmarROcounts+=1
            marcountRO+=1
    except Sales.DoesNotExist:
        MAINmarROcounts=0
    try:
        aprilROii=Sales.objects.filter(DateTime__year='2022',DateTime__month='04' or '03').exclude(CusName__contains='Appey').exclude(CusName__contains='KGD').exclude(CusName__contains='Kim Jasper').exclude(CusName__contains='Kylie').exclude(CusName__contains='MJ Arañez Macapinlac').exclude(CusName__contains='Maryjoy Macapinlac').exclude(CusName__contains='Mary Joy Macapinlac').exclude(CusName__contains='MJ Macapinlac').exclude(CusName__contains='Moneth	De guzman').exclude(CusName__contains='Ramonita	De Guzman').exclude(CusName__contains='Monet De Guzman').exclude(CusName__contains='kylie rose Deguzman').exclude(CusName__contains='kylie Rose G De GUZMAN').exclude(CusName__contains='kylie heart').exclude(CusName__contains='kylie heart').values_list('contactnumber',flat=True)
        aprcountRO=0
        MAINaprROcounts=0
        while aprcountRO<aprilROii.count():
            aprilROi=Sales.objects.filter(DateTime__year='2022',DateTime__month='04' or '03',contactnumber=aprilROii[aprcountRO]).annotate(date=TruncDate('DateTime'),day=TruncDay('DateTime'),hour=TruncHour('DateTime'),minute=TruncMinute('DateTime')).values_list('date', flat=True).distinct().count()
            if aprilROi==2:
                MAINaprROcounts+=1
            aprcountRO+=1
    except Sales.DoesNotExist:
        MAINaprROcounts=0
    try:
        mayROii=Sales.objects.filter(DateTime__year='2022',DateTime__month='05' or '04').exclude(CusName__contains='Appey').exclude(CusName__contains='KGD').exclude(CusName__contains='Kim Jasper').exclude(CusName__contains='Kylie').exclude(CusName__contains='MJ Arañez Macapinlac').exclude(CusName__contains='Maryjoy Macapinlac').exclude(CusName__contains='Mary Joy Macapinlac').exclude(CusName__contains='MJ Macapinlac').exclude(CusName__contains='Moneth	De guzman').exclude(CusName__contains='Ramonita	De Guzman').exclude(CusName__contains='Monet De Guzman').exclude(CusName__contains='kylie rose Deguzman').exclude(CusName__contains='kylie Rose G De GUZMAN').exclude(CusName__contains='kylie heart').exclude(CusName__contains='kylie heart').values_list('contactnumber',flat=True)
        maycountRO=0
        MAINmayROcounts=0
        while maycountRO<mayROii.count():
            mayROi=Sales.objects.filter(DateTime__year='2022',DateTime__month='05' or '04',contactnumber=mayROii[maycountRO]).annotate(date=TruncDate('DateTime'),day=TruncDay('DateTime'),hour=TruncHour('DateTime'),minute=TruncMinute('DateTime')).values_list('date', flat=True).distinct().count()
            if mayROi==2:
                MAINmayROcounts+=1
            maycountRO+=1
    except Sales.DoesNotExist:
        MAINmayROcounts=0
    try:
        juneROii=Sales.objects.filter(DateTime__year='2022',DateTime__month='06' or '05').exclude(CusName__contains='Appey').exclude(CusName__contains='KGD').exclude(CusName__contains='Kim Jasper').exclude(CusName__contains='Kylie').exclude(CusName__contains='MJ Arañez Macapinlac').exclude(CusName__contains='Maryjoy Macapinlac').exclude(CusName__contains='Mary Joy Macapinlac').exclude(CusName__contains='MJ Macapinlac').exclude(CusName__contains='Moneth	De guzman').exclude(CusName__contains='Ramonita	De Guzman').exclude(CusName__contains='Monet De Guzman').exclude(CusName__contains='kylie rose Deguzman').exclude(CusName__contains='kylie Rose G De GUZMAN').exclude(CusName__contains='kylie heart').exclude(CusName__contains='kylie heart').values_list('contactnumber',flat=True)
        juncountRO=0
        MAINjunROcounts=0
        while juncountRO<juneROii.count():
            juneROi=Sales.objects.filter(DateTime__year='2022',DateTime__month='06' or '05',contactnumber=juneROii[juncountRO]).annotate(date=TruncDate('DateTime')).values_list('date', flat=True).distinct().count()
            if juneROi==2:
                MAINjunROcounts+=1
            juncountRO+=1
    except Sales.DoesNotExist:
        MAINjunROcounts=0
    try:
        julyROii=Sales.objects.filter(DateTime__year='2022',DateTime__month='07' or '06').exclude(CusName__contains='Appey').exclude(CusName__contains='KGD').exclude(CusName__contains='Kim Jasper').exclude(CusName__contains='Kylie').exclude(CusName__contains='MJ Arañez Macapinlac').exclude(CusName__contains='Maryjoy Macapinlac').exclude(CusName__contains='Mary Joy Macapinlac').exclude(CusName__contains='MJ Macapinlac').exclude(CusName__contains='Moneth	De guzman').exclude(CusName__contains='Ramonita	De Guzman').exclude(CusName__contains='Monet De Guzman').exclude(CusName__contains='kylie rose Deguzman').exclude(CusName__contains='kylie Rose G De GUZMAN').exclude(CusName__contains='kylie heart').exclude(CusName__contains='kylie heart').values_list('contactnumber',flat=True)
        julcountRO=0
        MAINjulROcounts=0
        while julcountRO<julyROii.count():
            julyROi=Sales.objects.filter(DateTime__year='2022',DateTime__month='07' or '06',contactnumber=julyROii[julcountRO]).annotate(date=TruncDate('DateTime'),day=TruncDay('DateTime'),hour=TruncHour('DateTime'),minute=TruncMinute('DateTime')).values_list('date', flat=True).distinct().count()
            if julyROi==2:
                MAINjulROcounts+=1
            julcountRO+=1
    except Sales.DoesNotExist:
        MAINjulROcounts=0
    try:
        augustROii=Sales.objects.filter(DateTime__year='2022',DateTime__month='08' or '07').exclude(CusName__contains='Appey').exclude(CusName__contains='KGD').exclude(CusName__contains='Kim Jasper').exclude(CusName__contains='Kylie').exclude(CusName__contains='MJ Arañez Macapinlac').exclude(CusName__contains='Maryjoy Macapinlac').exclude(CusName__contains='Mary Joy Macapinlac').exclude(CusName__contains='MJ Macapinlac').exclude(CusName__contains='Moneth	De guzman').exclude(CusName__contains='Ramonita	De Guzman').exclude(CusName__contains='Monet De Guzman').exclude(CusName__contains='kylie rose Deguzman').exclude(CusName__contains='kylie Rose G De GUZMAN').exclude(CusName__contains='kylie heart').exclude(CusName__contains='kylie heart').values_list('contactnumber',flat=True)
        augcountRO=0
        MAINaugROcounts=0
        while augcountRO<augustROii.count():
            augustROi=Sales.objects.filter(DateTime__year='2022',DateTime__month='08' or '07',contactnumber=augustROii[augcountRO]).annotate(date=TruncDate('DateTime'),day=TruncDay('DateTime'),hour=TruncHour('DateTime'),minute=TruncMinute('DateTime')).values_list('date', flat=True).distinct().count()
            if augustROi==2:
                MAINaugROcounts+=1
            augcountRO+=1
    except Sales.DoesNotExist:
        MAINaugROcounts=0
    try:
        septemberROii=Sales.objects.filter(DateTime__year='2022',DateTime__month='09' or '08').exclude(CusName__contains='Appey').exclude(CusName__contains='KGD').exclude(CusName__contains='Kim Jasper').exclude(CusName__contains='Kylie').exclude(CusName__contains='MJ Arañez Macapinlac').exclude(CusName__contains='Maryjoy Macapinlac').exclude(CusName__contains='Mary Joy Macapinlac').exclude(CusName__contains='MJ Macapinlac').exclude(CusName__contains='Moneth	De guzman').exclude(CusName__contains='Ramonita	De Guzman').exclude(CusName__contains='Monet De Guzman').exclude(CusName__contains='kylie rose Deguzman').exclude(CusName__contains='kylie Rose G De GUZMAN').exclude(CusName__contains='kylie heart').exclude(CusName__contains='kylie heart').values_list('contactnumber',flat=True)
        septcountRO=0
        MAINseptROcounts=0
        while septcountRO<septemberROii.count():
            septemberROi=Sales.objects.filter(DateTime__year='2022',DateTime__month='09' or '08',contactnumber=septemberROii[septcountRO]).annotate(date=TruncDate('DateTime'),day=TruncDay('DateTime'),hour=TruncHour('DateTime'),minute=TruncMinute('DateTime')).values_list('date', flat=True).distinct().count()
            if septemberROi==2:
                MAINseptROcounts+=1
            septcountRO+=1
    except Sales.DoesNotExist:
        MAINseptROcounts=0
    try:
        octoberROii=Sales.objects.filter(DateTime__year='2022',DateTime__month='10' or '09').exclude(CusName__contains='Appey').exclude(CusName__contains='KGD').exclude(CusName__contains='Kim Jasper').exclude(CusName__contains='Kylie').exclude(CusName__contains='MJ Arañez Macapinlac').exclude(CusName__contains='Maryjoy Macapinlac').exclude(CusName__contains='Mary Joy Macapinlac').exclude(CusName__contains='MJ Macapinlac').exclude(CusName__contains='Moneth	De guzman').exclude(CusName__contains='Ramonita	De Guzman').exclude(CusName__contains='Monet De Guzman').exclude(CusName__contains='kylie rose Deguzman').exclude(CusName__contains='kylie Rose G De GUZMAN').exclude(CusName__contains='kylie heart').exclude(CusName__contains='kylie heart').values_list('contactnumber',flat=True)
        octcountRO=0
        MAINoctROcounts=0
        while octcountRO<octoberROii.count():
            octoberROi=Sales.objects.filter(DateTime__year='2022',DateTime__month='10' or '09',contactnumber=octoberROii[octcountRO]).annotate(date=TruncDate('DateTime'),day=TruncDay('DateTime'),hour=TruncHour('DateTime'),minute=TruncMinute('DateTime')).values_list('date', flat=True).distinct().count()
            if octoberROi==2:
                MAINoctROcounts+=1
            octcountRO+=1
    except Sales.DoesNotExist:
        MAINoctROcounts=0
    try:
        novemberROii=Sales.objects.filter(DateTime__year='2022',DateTime__month='11' or '10').exclude(CusName__contains='Appey').exclude(CusName__contains='KGD').exclude(CusName__contains='Kim Jasper').exclude(CusName__contains='Kylie').exclude(CusName__contains='MJ Arañez Macapinlac').exclude(CusName__contains='Maryjoy Macapinlac').exclude(CusName__contains='Mary Joy Macapinlac').exclude(CusName__contains='MJ Macapinlac').exclude(CusName__contains='Moneth	De guzman').exclude(CusName__contains='Ramonita	De Guzman').exclude(CusName__contains='Monet De Guzman').exclude(CusName__contains='kylie rose Deguzman').exclude(CusName__contains='kylie Rose G De GUZMAN').exclude(CusName__contains='kylie heart').exclude(CusName__contains='kylie heart').values_list('contactnumber',flat=True)
        novcountRO=0
        MAINnovROcounts=0
        while novcountRO<novemberROii.count():
            novemberROi=Sales.objects.filter(DateTime__year='2022',DateTime__month__gte='10',  DateTime__month__lte='11',contactnumber=novemberROii[novcountRO]).annotate(date=TruncDate('DateTime'),day=TruncDay('DateTime'),hour=TruncHour('DateTime'),minute=TruncMinute('DateTime')).values_list('date', flat=True).distinct().count()
            novnov=Sales.objects.filter(DateTime__year='2022',DateTime__month__gte='10',  DateTime__month__lte='11',contactnumber=novemberROii[novcountRO]).annotate(date=TruncDate('DateTime'),day=TruncDay('DateTime'),hour=TruncHour('DateTime'),minute=TruncMinute('DateTime')).values_list('date', flat=True).distinct()
            print('novnov: ',novnov)
            if novemberROi==2:
                MAINnovROcounts+=1
            novcountRO+=1
        
    except Sales.DoesNotExist:
       
        MAINnovROcounts=0
    try:
        decemberROii=Sales.objects.filter(DateTime__year='2022',DateTime__month__gte='11', DateTime__month__lte='12').exclude(CusName__contains='Appey').exclude(CusName__contains='KGD').exclude(CusName__contains='Kim Jasper').exclude(CusName__contains='Kylie').exclude(CusName__contains='MJ Arañez Macapinlac').exclude(CusName__contains='Maryjoy Macapinlac').exclude(CusName__contains='Mary Joy Macapinlac').exclude(CusName__contains='MJ Macapinlac').exclude(CusName__contains='Moneth	De guzman').exclude(CusName__contains='Ramonita	De Guzman').exclude(CusName__contains='Monet De Guzman').exclude(CusName__contains='kylie rose Deguzman').exclude(CusName__contains='kylie Rose G De GUZMAN').exclude(CusName__contains='kylie heart').exclude(CusName__contains='kylie heart').values_list('contactnumber',flat=True)
        deccountRO=0
        MAINdecROcounts=0
        while deccountRO<decemberROii.count():
            decemberROi=Sales.objects.filter(DateTime__year='2022',DateTime__month__gte='11', DateTime__month__lte='12',contactnumber=decemberROii[deccountRO]).annotate(date=TruncDate('DateTime'),day=TruncDay('DateTime'),hour=TruncHour('DateTime'),minute=TruncMinute('DateTime')).values_list('date', flat=True).distinct().count()
           
            decdec=Sales.objects.filter(DateTime__year='2022',DateTime__month__gte='11', DateTime__month__lte='12',contactnumber=decemberROii[deccountRO]).annotate(date=TruncDate('DateTime'),day=TruncDay('DateTime'),hour=TruncHour('DateTime'),minute=TruncMinute('DateTime')).values_list('date', flat=True).distinct()
            print('decdec: ',decdec)
            if decemberROi==2:
                MAINdecROcounts+=1
            deccountRO+=1
        
    except Sales.DoesNotExist:
        
        MAINdecROcounts=0
    totalRO=int(MAINjanROcounts)+int(MAINfebROcounts)+int(MAINmarROcounts)+int(MAINaprROcounts)+int(MAINmayROcounts)+int(MAINjunROcounts)+int(MAINjulROcounts)+int(MAINaugROcounts)+int(MAINseptROcounts)+int(MAINoctROcounts)+int(MAINnovROcounts)+int(MAINdecROcounts)
    return render(request, 'Marketing.html',{'userr':userr,'totalRO':totalRO,'MAINdecROcounts':MAINdecROcounts,'MAINnovROcounts':MAINnovROcounts,'MAINoctROcounts':MAINoctROcounts,'MAINseptROcounts':MAINseptROcounts,'MAINaugROcounts':MAINaugROcounts,'MAINjulROcounts':MAINjulROcounts,'MAINjunROcounts':MAINjunROcounts,'MAINmayROcounts':MAINmayROcounts,'MAINaprROcounts':MAINaprROcounts,'MAINmarROcounts':MAINmarROcounts,'MAINfebROcounts':MAINfebROcounts,'MAINjanROcounts':MAINjanROcounts,'total':total,'january':january,'february':february,'march':march,'april':april,'may':may,'june':june,'july':july,'august':august,'september':september,'october':october,'november':november,'december':december})

@login_required
def RiderPOV(request):
    userr=request.user.id
    if is_ajax(request=request) and request.GET.get('riderni'):
        if (len(Acceptorder.objects.filter(Rider='Appey')))>0:
            rengkakungideliveri=Acceptorder.objects.filter(Rider='Appey').distinct('contactnumber')
        else:
            rengkakungideliveri=Acceptorder.objects.none()

        rengkakungideliver=serializers.serialize('json',rengkakungideliveri, cls=JSONEncoder)
        viewordersriderii={}
        arrayonerider=[]
        contactdistincterrideri = Acceptorder.objects.filter(Rider='Appey').distinct('contactnumber')
        contactdistincterrider=contactdistincterrideri.values_list('contactnumber',flat=True)
        i=0
        for cndistinctrider in contactdistincterrider:  
            arrayseparatorrideriii=Acceptorder.objects.filter(Rider='Appey',contactnumber=cndistinctrider).values()
            arrayseparatorrideri = list(arrayseparatorrideriii)
            arrayseparatorrider=json.dumps(arrayseparatorrideri, cls=JSONEncoder)
            viewordersriderii[contactdistincterrider[i]]=arrayseparatorrider
            i=i+1
        viewordersrideri=viewordersriderii
        viewordersrider=json.dumps(viewordersrideri, cls=JSONEncoder)
        contextrider={
        'rengkakungideliver':rengkakungideliver,
        'viewordersrider':viewordersrider
        }
        
        return JsonResponse(contextrider)
    
    return render(request, 'Rider.html')


def login_user(request):
    if request.method=="POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
             
        # Redirect to a success page.
            return redirect('kgddashboard.html')
        else:
            # Return an 'invalid login' error message.
            messages.success(request,"Account does not exist or invalid!! ❌")
            return render(request, 'index.html')    
    else:
        return render(request, 'index.html')

@login_required
def delprod(request, del_id):

        userr=request.user.id
        prodd = user1.objects.get(id=del_id)
        productss = user1.objects.all().filter(user__id=userr)
        if request.method == "POST":
            prodd.delete()
            return redirect('Products.html')
        else:
            return render(request, 'deletreproduct.html',{'prodd':prodd,'productss':productss})

@login_required
def editprod(request, edit_id):

        userr=request.user.id
        prodidtarget=edit_id
        eprodd = user1.objects.get(id=edit_id)
        productss = user1.objects.all().filter(user__id=userr)
        if request.method == "POST":
            if request.POST.get("editcateg"):
                editcategi = request.POST.get("editcateg")
                if editcategi == "Milktea":
                    editcateg = 1
                elif editcategi == "Frappe":
                    editcateg = 2
                elif editcategi == "Freeze":
                    editcateg = 3
                elif editcategi == "Snacks":
                    editcateg = 4
                elif editcategi == "Add-ons":
                    editcateg = 5
                finaleprodd=user1.objects.filter(id=prodidtarget).update(Category=editcateg)
            if request.POST.get("editproductnamename"):
                editproductnamename = request.POST.get("editproductnamename")
                finaleprodd=user1.objects.filter(id=prodidtarget).update(productname=editproductnamename)
            if request.POST.get("editsubcateg"):
                editsubcategi = request.POST.get("editsubcateg")
                if editsubcategi == "Pizza":
                    editsubcateg = 1
                elif editsubcategi == "Fries":
                    editsubcateg = 2
                elif editsubcategi == "Shawarma":
                    editsubcateg = 3
                elif editsubcategi == "Cookies":
                    editsubcateg = 4
                elif editsubcategi == "Bubble Waffle":
                    editsubcateg = 5
                else:
                    editsubcateg = None
                finaleprodd=user1.objects.filter(id=prodidtarget).update(Subcategory=editsubcateg)
            if request.POST.get("editsize"):
                editsizei = request.POST.get("editsize")
                if editsizei == "Reg":
                    editsize = 1
                elif editsizei == "Full":
                    editsize = 2
                elif editsizei == "Small":
                    editsize = 3
                else:
                    editsize = None
                finaleprodd=user1.objects.filter(id=prodidtarget).update(Size=editsize)
            if request.POST.get("editpsize"):
                editpsizei = request.POST.get("editpsize")
                if editpsizei == 'Barkada(10")':
                    editpsize = 1
                elif editpsizei == 'Pamilya(12")':
                    editpsize = 2
                else:
                    editpsize = None
                finaleprodd=user1.objects.filter(id=prodidtarget).update(PSize=editpsize)
            if request.POST.get("editpricename"):
                editpricename = request.POST.get("editpricename")
                finaleprodd=user1.objects.filter(id=prodidtarget).update(Price=editpricename)
            if request.POST.get("editcostname"):
                editcostname = request.POST.get("editcostname")
                finaleprodd=user1.objects.filter(id=prodidtarget).update(Cost=editcostname)
            if request.POST.get("editpdescriptionname"):
                editpdescriptionname = request.POST.get("editpdescriptionname")
                finaleprodd=user1.objects.filter(id=prodidtarget).update(PDescription=editpdescriptionname)
            return redirect('Products.html')
        else:
            return render(request, 'editproduct.html',{'eprodd':eprodd,'productss':productss})


@login_required
def coupon(request):
       userr=request.user.id
       if request.GET.get('acceptcontactno'):
            contactnumberaccept = request.GET.get('acceptcontactno')
            rider = request.GET.get('rider')
            getETA = request.GET.get('ETA')
            Accepted = Customer.objects.filter(Admin=userr,contactnumber=contactnumberaccept)
            
            objs = [Acceptorder(
                        Admin=Accepted.Admin,
                        Customername=Accepted.Customername,
                        codecoupon=Accepted.codecoupon,
                        discount=Accepted.discount or None,
                        Province=Accepted.Province,
                        MunicipalityCity=Accepted.MunicipalityCity,
                        Barangay=Accepted.Barangay,
                        StreetPurok=Accepted.StreetPurok,
                        Housenumber=Accepted.Housenumber or None,
                        LandmarksnNotes=Accepted.LandmarksnNotes or None,
                        DeliveryFee=Accepted.DeliveryFee or 0,
                        contactnumber=Accepted.contactnumber,
                        Rider=rider,
                        productname=Accepted.productname,
                        Category=Accepted.Category,
                        Subcategory=Accepted.Subcategory or None,
                        Size=Accepted.Size  or None,
                        PSize=Accepted.PSize or None,
                        Addons=Accepted.Addons or None,
                        QtyAddons= Accepted.QtyAddons or 0,
                        Price=Accepted.Price,
                        Subtotal = Accepted.Subtotal,
                        GSubtotal=Accepted.GSubtotal,
                        Cost=Accepted.Cost,
                        Qty=Accepted.Qty,
                        Bill=Accepted.Bill or 0,
                        Change=Accepted.Change or 0,
                        ETA=getETA,
                        MOP=Accepted.MOP,
                        ordertype='Online',
                        Timetodeliver=Accepted.Timetodeliver,
                        ScheduleTime=Accepted.ScheduleTime,
                        gpslat = Accepted.gpslat,
                        gpslng = Accepted.gpslng,
                        gpsaccuracy = Accepted.gpsaccuracy,
                        pinnedlat = Accepted.pinnedlat,
                        pinnedlng = Accepted.pinnedlng,
                            
                        tokens = Accepted.tokens or None,
                        DateTime=Accepted.DateTime,
                )
                for Accepted in Accepted
            ]
            Acceptorders = Acceptorder.objects.bulk_create(objs)
            Accepted.delete()
            messageacknowledgetokeni=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberaccept).values_list('tokens',flat=True).first()
            messageacknowledgetoken = ["dHEGNR4YGO8a-AVQWfIE33:APA91bGkNxUcRZEHJQCkUy3k3THUEMxml9q4819bDQw1b8UkD05qThidgXq3Nnr46I1pwQikZgwiGFuBgKwUxHO6kUXI9KId3ZK0fQ0zi83QegTtVimqV18a2pDqBq5qnJf-BK74Z1nL", messageacknowledgetokeni]
            acknowledge(request, messageacknowledgetoken)
            MessageRider(request)
            return HttpResponseRedirect('/index/pos')

       if len(Acceptorder.objects.filter(Admin=userr))>0:
            acceptedorder = Acceptorder.objects.filter(Admin=userr).distinct('contactnumber')
            acceptedorderall = Acceptorder.objects.filter(Admin=userr)
       else:
            acceptedorder = Acceptorder.objects.none()
            acceptedorderall = Acceptorder.objects.none()
       viewordersacceptii={}
       arrayoneaccept=[]
       contactdistincteraccepti = Acceptorder.objects.filter(Admin=userr).distinct('contactnumber')
       contactdistincteraccept=contactdistincteraccepti.values_list('contactnumber',flat=True)
       i=0
       for cndistinctaccept in contactdistincteraccept:
            arrayseparatoracceptiii=Acceptorder.objects.filter(Admin=userr,contactnumber=cndistinctaccept).exclude(productname='Ready').values()
            arrayseparatoraccepti = list(arrayseparatoracceptiii)
            arrayseparatoraccept=json.dumps(arrayseparatoraccepti, cls=JSONEncoder)
            viewordersacceptii[contactdistincteraccept[i]]=arrayseparatoraccept
            i=i+1
       viewordersaccepti=viewordersacceptii
       viewordersaccept=json.dumps(viewordersaccepti, cls=JSONEncoder)
        

       if (request.GET.get('rider') == "") and (request.GET.get('contactnoreject') or request.GET.get('contactnoaccepted')):
            if request.GET.get('contactnoreject'):
                contactnumberreject = request.GET.get('contactnoreject')
                Rejected = Customer.objects.filter(Admin=userr,contactnumber=contactnumberreject)
            elif request.GET.get('contactnoaccepted'):
                contactnumberreject = request.GET.get('contactnoaccepted')
                if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject, productname='Ready'):
                    deletethis=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject, productname='Ready')
                    deletethis.delete()
                Rejected = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject)
            
            objs = [Rejectorder(
                        Admin=userr,
                        Customername=Rejected.Customername,
                        codecoupon=Rejected.codecoupon,
                        discount=Rejected.discount or None,
                        Province=Rejected.Province,
                        MunicipalityCity=Rejected.MunicipalityCity,
                        Barangay=Rejected.Barangay,
                        StreetPurok=Rejected.StreetPurok,
                        Housenumber=Rejected.Housenumber or None,
                        LandmarksnNotes=Rejected.LandmarksnNotes or None,
                        DeliveryFee=Rejected.DeliveryFee or 0,
                        contactnumber=Rejected.contactnumber,
                        productname=Rejected.productname,
                        Category=Rejected.Category,
                        Subcategory=Rejected.Subcategory or None,
                        Size=Rejected.Size  or None,
                        PSize=Rejected.PSize or None,
                        Addons=Rejected.Addons or None,
                        QtyAddons= Rejected.QtyAddons or 0,
                        Price=Rejected.Price,
                        Subtotal = Rejected.Subtotal,
                        GSubtotal=Rejected.GSubtotal,
                        Cost=Rejected.Cost,
                        Qty=Rejected.Qty,
                        Bill=Rejected.Bill or 0,
                        Change=Rejected.Change or 0,
                        MOP=Rejected.MOP,
                        ordertype='Online',
                        Timetodeliver=Rejected.Timetodeliver,
                        ScheduleTime=Rejected.ScheduleTime,
                        gpslat = Rejected.gpslat,
                        gpslng = Rejected.gpslng,
                        gpsaccuracy = Rejected.gpsaccuracy,
                        pinnedlat = Rejected.pinnedlat,
                        pinnedlng = Rejected.pinnedlng,
                            
                        tokens = Rejected.tokens  or None,
                        DateTime=Rejected.DateTime,
                )
                for Rejected in Rejected
            ]
            Rejectorders = Rejectorder.objects.bulk_create(objs)
            Rejected.delete()
            return HttpResponseRedirect('/index/pos')

       if len(Rejectorder.objects.filter(Admin=userr))>0:
            rejectedorder = Rejectorder.objects.filter(Admin=userr).distinct('contactnumber')
            rejectedorderall = Rejectorder.objects.filter(Admin=userr)
       else:
            rejectedorder = Rejectorder.objects.none()
            rejectedorderall = Rejectorder.objects.none()
       viewordersrejectii={}
       arrayonereject=[]
       contactdistincterrejecti = Rejectorder.objects.filter(Admin=userr).distinct('contactnumber')
       contactdistincterreject=contactdistincterrejecti.values_list('contactnumber',flat=True)
       i=0
       for cndistinctreject in contactdistincterreject:
            arrayseparatorrejectiii=Rejectorder.objects.filter(Admin=userr,contactnumber=cndistinctreject).exclude(productname='Ready').values()
            arrayseparatorrejecti = list(arrayseparatorrejectiii)
            arrayseparatorreject=json.dumps(arrayseparatorrejecti, cls=JSONEncoder)
            viewordersrejectii[contactdistincterreject[i]]=arrayseparatorreject
            i=i+1
       viewordersrejecti=viewordersrejectii
       viewordersreject=json.dumps(viewordersrejecti, cls=JSONEncoder)

        

       if request.GET.get('contactnorestore'):
            contactnumberrestore = request.GET.get('contactnorestore')
            Restored = Rejectorder.objects.filter(Admin=userr,contactnumber=contactnumberrestore)
            
            objs = [Customer(
                        Admin=userr,
                        Customername=Restored.Customername,
                        codecoupon=Restored.codecoupon,
                        discount=Restored.discount or None,
                        Province=Restored.Province,
                        MunicipalityCity=Restored.MunicipalityCity,
                        Barangay=Restored.Barangay,
                        StreetPurok=Restored.StreetPurok,
                        Housenumber=Restored.Housenumber or None,
                        LandmarksnNotes=Restored.LandmarksnNotes or None,
                        DeliveryFee=Restored.DeliveryFee or 0,
                        contactnumber=Restored.contactnumber,
                        productname=Restored.productname,
                        Category=Restored.Category,
                        Subcategory=Restored.Subcategory or None,
                        Size=Restored.Size  or None,
                        PSize=Restored.PSize or None,
                        Addons=Restored.Addons or None,
                        QtyAddons= Restored.QtyAddons or 0,
                        Price=Restored.Price,
                        Subtotal = Restored.Subtotal,
                        GSubtotal=Restored.GSubtotal,
                        Cost=Restored.Cost,
                        Qty=Restored.Qty,
                        Bill=Restored.Bill or 0,
                        Change=Restored.Change or 0,
                        MOP=Restored.MOP,
                        ordertype='Online',
                        Timetodeliver=Restored.Timetodeliver,
                        ScheduleTime=Restored.ScheduleTime,
                        gpslat = Restored.gpslat,
                        gpslng = Restored.gpslng,
                        gpsaccuracy = Restored.gpsaccuracy,
                        pinnedlat = Restored.pinnedlat,
                        pinnedlng = Restored.pinnedlng,
                          
                        tokens = Restored.tokens  or None,
                        DateTime=Restored.DateTime,
                )
                for Restored in Restored
            ]
            Restore = Customer.objects.bulk_create(objs)
            Restored.delete()
            return HttpResponseRedirect('/index/pos')

       if len(Customer.objects.filter(Admin=userr))>0:
            onlineorder = Customer.objects.filter(Admin=userr).distinct('contactnumber')
            onlineorderall = Customer.objects.filter(Admin=userr)
       else:
            onlineorder = Customer.objects.none()
            onlineorderall = Customer.objects.none()
       viewordersii={}
       arrayone=[]
       contactdistincteri = Customer.objects.filter(Admin=userr).distinct('contactnumber')
       contactdistincter=contactdistincteri.values_list('contactnumber',flat=True)
       i=0
       for cndistinct in contactdistincter:  
            arrayseparatoriii=Customer.objects.filter(Admin=userr,contactnumber=cndistinct).values()
            arrayseparatori = list(arrayseparatoriii)
            arrayseparator=json.dumps(arrayseparatori, cls=JSONEncoder)
            viewordersii[contactdistincter[i]]=arrayseparator
            i=i+1
       viewordersi=viewordersii
       vieworders=json.dumps(viewordersi, cls=JSONEncoder)

       onlineordercounter = len(Customer.objects.filter(Admin=userr).distinct('contactnumber'))

       if is_ajax(request=request) and request.POST.get("Ready"):
            contactnumberready = request.POST.get('Ready')
            Readyadd = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).first()
            Readyacceptorder=Acceptorder.objects.create(
                        Admin=userr,
                        Customername=Readyadd.Customername,
                        codecoupon=Readyadd.codecoupon,
                        discount=Readyadd.discount or None,
                        Province=Readyadd.Province,
                        MunicipalityCity=Readyadd.MunicipalityCity,
                        Barangay=Readyadd.Barangay,
                        StreetPurok=Readyadd.StreetPurok,
                        Housenumber=Readyadd.Housenumber or None,
                        LandmarksnNotes=Readyadd.LandmarksnNotes or None,
                        DeliveryFee=0,
                        contactnumber=Readyadd.contactnumber,
                        productname='Ready',
                        Category=Readyadd.Category,
                        Subcategory=None,
                        Size=None,
                        PSize=None,
                        Addons=None,
                        QtyAddons= 0,
                        Price=0,
                        Subtotal = 0,
                        GSubtotal=Readyadd.GSubtotal,
                        Cost=0,
                        Qty=0,
                        Bill=Readyadd.Bill or 0,
                        Change=Readyadd.Change or 0,
                        MOP=Readyadd.MOP,
                        ordertype='Online',
                        Timetodeliver=Readyadd.Timetodeliver,
                        ScheduleTime=Readyadd.ScheduleTime,
                        gpslat = Readyadd.gpslat,
                        gpslng = Readyadd.gpslng,
                        gpsaccuracy = Readyadd.gpsaccuracy,
                        pinnedlat = Readyadd.pinnedlat,
                        pinnedlng = Readyadd.pinnedlng,
                            
                        tokens = Readyadd.tokens  or None,
                        DateTime=Readyadd.DateTime,
                        )
            Readyacceptorder.save()
            if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready, MOP='COD'):
                orderprepared(request)
            messageacknowledgetokeni=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('tokens',flat=True).first()
            messageacknowledgetoken = ["dHEGNR4YGO8a-AVQWfIE33:APA91bGkNxUcRZEHJQCkUy3k3THUEMxml9q4819bDQw1b8UkD05qThidgXq3Nnr46I1pwQikZgwiGFuBgKwUxHO6kUXI9KId3ZK0fQ0zi83QegTtVimqV18a2pDqBq5qnJf-BK74Z1nL", messageacknowledgetokeni]
            if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('MOP',flat=True).first() == 'COD' or Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('MOP',flat=True).first() == 'GcashDelivery':
                deliveryotwRider(request)
                deliveryotwCustomer(request , messageacknowledgetoken)
            else:
                pickupCustomer(request , messageacknowledgetoken)
            return JsonResponse({'Ready':'Ready'})
       if is_ajax(request=request) and request.GET.get("apini"):
            onlineordercounterf = onlineordercounter
            onlineorderf = [serializers.serialize('json',onlineorder, cls=JSONEncoder),vieworders]
            return JsonResponse({'onlineorderf':onlineorderf})
            
       if is_ajax(request=request) and request.POST.get('doneorders'):
            contactnumberdonei = json.loads(request.POST.get('doneorders'))
            contactnumberdone = contactnumberdonei[0]['contactnumber']
            if contactnumberdonei[0]['codecoupon']:
                if couponlist.objects.filter(code=contactnumberdonei[0]['codecoupon']):
                    codeconsumereducerii=couponlist.objects.get(code=contactnumberdonei[0]['codecoupon'])
                    if codeconsumereducerii.is_consumable == True and codeconsumereducerii.redeemlimit>0:
                        codeconsumereduceri=int(codeconsumereducerii.redeemlimit)-1
                        codeconsumereducer=couponlist.objects.filter(code=contactnumberdonei[0]['codecoupon']).update(redeemlimit=codeconsumereduceri)
                    else:
                        pass
                else:
                    pass
            else:
                pass
            if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone, productname='Ready'):
                deletethis=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone, productname='Ready')
                deletethis.delete()
            Done = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone)
            try:
                Sales.objects.filter(contactnumber=contactnumberdonei[0]['contactnumber'], CusName=contactnumberdonei[0]['Customername'], productname='DeliveryFee', DateTime=contactnumberdonei[0]['DateTime'])
                deliveryfeepaid='true'
            except Sales.DoesNotExist:
                deliveryfeepaid='false'
            if contactnumberdonei[0]['DeliveryFee'] != None and deliveryfeepaid == 'true':
                devfeeassales=Sales.objects.create(
                        user=userr,
                        CusName=contactnumberdonei[0]['Customername'],
                        codecoupon=contactnumberdonei[0]['codecoupon'] or None,
                        discount=contactnumberdonei[0]['discount'] or None,
                        Province=contactnumberdonei[0]['Province'],
                        MunicipalityCity=contactnumberdonei[0]['MunicipalityCity'],
                        Barangay=contactnumberdonei[0]['Barangay'],
                        StreetPurok=contactnumberdonei[0]['StreetPurok'],
                        Housenumber=contactnumberdonei[0]['Housenumber'] or None,
                        LandmarksnNotes=contactnumberdonei[0]['LandmarksnNotes'] or None,
                        DeliveryFee=contactnumberdonei[0]['DeliveryFee'] or None,
                        contactnumber=contactnumberdonei[0]['contactnumber'],
                        productname='DeliveryFee',
                        Category='DeliveryFee',
                        Subcategory='DeliveryFee',
                        Size=None,
                        PSize=None,
                        Addons=None,
                        QtyAddons=0,
                        Price=contactnumberdonei[0]['DeliveryFee'],
                        Subtotal = contactnumberdonei[0]['DeliveryFee'],
                        GSubtotal=contactnumberdonei[0]['GSubtotal'],
                        Cost=0,
                        Qty=1,
                        Bill=contactnumberdonei[0]['Bill'] or 0,
                        Change=contactnumberdonei[0]['Change'] or 0,
                        MOP=contactnumberdonei[0]['MOP'],
                        ordertype='Online',
                        Timetodeliver=contactnumberdonei[0]['Timetodeliver'] or None,
                        ScheduleTime=contactnumberdonei[0]['ScheduleTime'] or None,
                        gpslat = contactnumberdonei[0]['gpslat'],
                        gpslng = contactnumberdonei[0]['gpslng'],
                        gpsaccuracy = contactnumberdonei[0]['gpsaccuracy'],
                        pinnedlat = contactnumberdonei[0]['pinnedlat'],
                        pinnedlng = contactnumberdonei[0]['pinnedlng'],
                            
                        tokens = contactnumberdonei[0]['tokens'] or None,
                        DateTime=contactnumberdonei[0]['DateTime'],
                )
                devfeeassales.save()
            if contactnumberdonei[0]['discount']:
                objs = [Sales(
                            user=userr,
                            CusName=Done.Customername,
                            codecoupon=Done.codecoupon,
                            discount=Readyadd.discount or None,
                            Province=Done.Province,
                            MunicipalityCity=Done.MunicipalityCity,
                            Barangay=Done.Barangay,
                            StreetPurok=Done.StreetPurok,
                            Housenumber=Done.Housenumber or None,
                            LandmarksnNotes=Done.LandmarksnNotes or None,
                            DeliveryFee=Done.DeliveryFee or None,
                            contactnumber=Done.contactnumber,
                            productname=Done.productname,
                            Category=Done.Category,
                            Subcategory=Done.Subcategory or None,
                            Size=Done.Size  or None,
                            PSize=Done.PSize or None,
                            Addons=Done.Addons or None,
                            QtyAddons= Done.QtyAddons or 0,
                            Price=Done.Price,
                            Subtotal = Done.Subtotal-((Done.Subtotal)*(Decimal(int(Done.discount)/100))),
                            GSubtotal=Done.GSubtotal,
                            Cost=Done.Cost,
                            Qty=Done.Qty,
                            Bill=Done.Bill or 0,
                            Change=Done.Change or 0,
                            MOP=Done.MOP,
                            ordertype='Online',
                            Timetodeliver=Done.Timetodeliver,
                            ScheduleTime=Done.ScheduleTime,
                            gpslat = Done.gpslat,
                            gpslng = Done.gpslng,
                            gpsaccuracy = Done.gpsaccuracy,
                            pinnedlat = Done.pinnedlat,
                            pinnedlng = Done.pinnedlng,
                            
                            tokens = Done.tokens or None,
                            DateTime=Done.DateTime,
                    )
                    for Done in Done
                ]
            else:
                objs = [Sales(
                            user=userr,
                            CusName=Done.Customername,
                            codecoupon=Done.codecoupon,
                            discount=Readyadd.discount or None,
                            Province=Done.Province,
                            MunicipalityCity=Done.MunicipalityCity,
                            Barangay=Done.Barangay,
                            StreetPurok=Done.StreetPurok,
                            Housenumber=Done.Housenumber or None,
                            LandmarksnNotes=Done.LandmarksnNotes or None,
                            DeliveryFee=Done.DeliveryFee or None,
                            contactnumber=Done.contactnumber,
                            productname=Done.productname,
                            Category=Done.Category,
                            Subcategory=Done.Subcategory or None,
                            Size=Done.Size  or None,
                            PSize=Done.PSize or None,
                            Addons=Done.Addons or None,
                            QtyAddons= Done.QtyAddons or 0,
                            Price=Done.Price,
                            Subtotal = Done.Subtotal,
                            GSubtotal=Done.GSubtotal,
                            Cost=Done.Cost,
                            Qty=Done.Qty,
                            Bill=Done.Bill or 0,
                            Change=Done.Change or 0,
                            MOP=Done.MOP,
                            ordertype='Online',
                            Timetodeliver=Done.Timetodeliver,
                            ScheduleTime=Done.ScheduleTime,
                            gpslat = Done.gpslat,
                            gpslng = Done.gpslng,
                            gpsaccuracy = Done.gpsaccuracy,
                            pinnedlat = Done.pinnedlat,
                            pinnedlng = Done.pinnedlng,
                            
                            tokens = Done.tokens or None,
                            DateTime=Done.DateTime,
                    )
                    for Done in Done
                ]
            Salesorders = Sales.objects.bulk_create(objs)
            Done.delete()
       #######  BASE NOTIFY FROM WEBSITE  ########
       notifyorder=acknowledgedstockorder.objects.filter(CusName="Notify",user=userr).count()
       if acknowledgedstockorder.objects.all().count()==0:
           notifyadmin=submitstockorder.objects.all().count()
       else:
           notifyadmin=0
       if couponlist.objects.filter(user__id=userr)==0:
          couponss = couponlist.objects.none()
       else:
          couponss = couponlist.objects.filter(user__id=userr).order_by('-id')

       if request.POST.get("activateornotid") and is_ajax(request=request):
          activatecouponid=request.POST.get("activateornotid");
          torf=couponlist.objects.get(user__id=userr,id=activatecouponid)
          if torf.is_active == True:
              couponlist.objects.filter(user__id=userr,id=activatecouponid).update(is_active=False)
              check="true"
          else:
              couponlist.objects.filter(user__id=userr,id=activatecouponid).update(is_active=True)
              check="false"
          return JsonResponse({'check':check})


       if request.POST.get("getcouponlist") and is_ajax(request=request):
           if couponlist.objects.filter(user__id=userr)==0:
              couponsajaxi = couponlist.objects.none()
           else:
              couponsajaxi = couponlist.objects.filter(user__id=userr).order_by('-id')
           couponsajax=serializers.serialize('json',couponsajaxi, cls=JSONEncoder)
           return JsonResponse({'couponsajax':couponsajax})



       if request.POST.get("couponnameid") and is_ajax(request=request):
          couponnameid = json.loads(request.POST.get("couponnameid"))
          categoryidi = json.loads(request.POST.get("categoryid"))
          if categoryidi=="One Code Many":
            categoryid=1
          else:
            categoryid=3
          codeid = json.loads(request.POST.get("codeid")) or None
          piecesidi = json.loads(request.POST.get("piecesid")) or 0
          if piecesidi:
            piecesid=int(piecesidi)
          else:
            piecesid=0
          discountpercentageidi = json.loads(request.POST.get("discountpercentageid")) or 0
          if discountpercentageidi:
            discountpercentageid=int(discountpercentageidi)
          else:
            discountpercentageid=0
          is_withMinimumAmountid = json.loads(request.POST.get("is_withMinimumAmountid")) or None
          if is_withMinimumAmountid == 'Yes':
            is_withMinimumAmountidTF = True
          else:
            is_withMinimumAmountidTF = False
          minimumamountidi = json.loads(request.POST.get("minimumamountid")) or 0
          if minimumamountidi:
            minimumamountid=int(minimumamountidi)
          else:
            minimumamountid=0
          is_activeid = json.loads(request.POST.get("is_activeid")) or None
          if is_activeid == 'Yes':
            is_activeidTF = True
          else:
            is_activeidTF = False
          is_maxredeemid = json.loads(request.POST.get("is_maxredeemid")) or None
          if is_maxredeemid == 'Yes':
            is_maxredeemidTF = True
          else:
            is_maxredeemidTF = False
          maxredeemlimitidi = json.loads(request.POST.get("maxredeemlimitid")) or 0
          if maxredeemlimitidi:
            maxredeemlimitid=int(maxredeemlimitidi)
          else:
            maxredeemlimitid=0
          
          if codeid:
                CodeTrue=[]
                CodeFalse=[]
                #?prmcd=<code>
                generateurl="https://kgdcafe.com/index/onlineorder/4/?prmcd="+codeid
                filename=codeid
                CodeTrue.insert(0,generateurl)
                CodeTrue.insert(1,filename)
                couponobjects=couponlist.objects.create(user=request.user, couponname=couponnameid, category_id=categoryid, code=codeid, url=generateurl, pieces=piecesid, discountamount=discountpercentageid, is_withMinimumAmount=is_withMinimumAmountidTF, is_consumable=is_maxredeemidTF,redeemlimit=maxredeemlimitid,MinimumAmount=minimumamountid, is_active=is_activeidTF) 
          else:
                CodeTrue=[]
                CodeFalse=[]
                i=0
                while i<piecesid:
                    allowed_chars = ''.join((string.ascii_letters, string.digits))
                    unique_id = ''.join(random.choice(allowed_chars) for _ in range(6))
                    codeid=unique_id
                    #?prmcd=<code>
                    generateurl="https://kgdcafe.com/index/onlineorder/4/?prmcd="+codeid

                    objectappender={
                    'generateurl':generateurl,
                    'filename':codeid
                    }
                    CodeFalse.insert(i, objectappender)

                    couponobjects=couponlist.objects.create(user=request.user, couponname=couponnameid, category_id=categoryid,code=codeid, url=generateurl,pieces=piecesid,discountamount=discountpercentageid,is_consumable=is_maxredeemidTF,redeemlimit=maxredeemlimitid,is_withMinimumAmount=is_withMinimumAmountidTF,MinimumAmount=minimumamountid,is_active=is_activeidTF)
                    i += 1
          Codei={}
          Codei={
          'CodeTrue':CodeTrue,
          'CodeFalse':CodeFalse
          }

          Code=json.dumps(Codei)
          data={
          'Code':Code
          }
          return JsonResponse(data)
       if len(Acceptorder.objects.filter(Admin=userr, productname='Ready'))>0:
            initial=Acceptorder.objects.filter(Admin=userr, productname='Ready').values_list('contactnumber', flat=True)
            readylistcontact=list(initial)
       else:
            readylistcontact=list(Acceptorder.objects.none())
       print('readylistcontact1:',readylistcontact)
       return render(request, 'coupon.html',{'readylistcontact':readylistcontact, 'onlineordercounter':onlineordercounter,'viewordersreject':viewordersreject,'rejectedorder':rejectedorder,'viewordersaccept':viewordersaccept,'acceptedorder':acceptedorder,'onlineorder':onlineorder,'notifyadmin':notifyadmin,'notifyorder':notifyorder,'couponss':couponss,'userr':userr})



@login_required
def products(request):
        userr=request.user.id
        if request.GET.get('acceptcontactno'):
            contactnumberaccept = request.GET.get('acceptcontactno')
            rider = request.GET.get('rider')
            getETA = request.GET.get('ETA')
            Accepted = Customer.objects.filter(Admin=userr,contactnumber=contactnumberaccept)
            
            objs = [Acceptorder(
                        Admin=Accepted.Admin,
                        Customername=Accepted.Customername,
                        codecoupon=Accepted.codecoupon,
                        discount=Accepted.discount or None,
                        Province=Accepted.Province,
                        MunicipalityCity=Accepted.MunicipalityCity,
                        Barangay=Accepted.Barangay,
                        StreetPurok=Accepted.StreetPurok,
                        Housenumber=Accepted.Housenumber or None,
                        LandmarksnNotes=Accepted.LandmarksnNotes or None,
                        DeliveryFee=Accepted.DeliveryFee or 0,
                        contactnumber=Accepted.contactnumber,
                        Rider=rider,
                        productname=Accepted.productname,
                        Category=Accepted.Category,
                        Subcategory=Accepted.Subcategory or None,
                        Size=Accepted.Size  or None,
                        PSize=Accepted.PSize or None,
                        Addons=Accepted.Addons or None,
                        QtyAddons= Accepted.QtyAddons or 0,
                        Price=Accepted.Price,
                        Subtotal = Accepted.Subtotal,
                        GSubtotal=Accepted.GSubtotal,
                        Cost=Accepted.Cost,
                        Qty=Accepted.Qty,
                        Bill=Accepted.Bill or 0,
                        Change=Accepted.Change or 0,
                        ETA=getETA,
                        MOP=Accepted.MOP,
                        ordertype='Online',
                        Timetodeliver=Accepted.Timetodeliver,
                        ScheduleTime=Accepted.ScheduleTime,
                        gpslat = Accepted.gpslat,
                        gpslng = Accepted.gpslng,
                        gpsaccuracy = Accepted.gpsaccuracy,
                        pinnedlat = Accepted.pinnedlat,
                        pinnedlng = Accepted.pinnedlng,
                            
                        tokens = Accepted.tokens or None,
                        DateTime=Accepted.DateTime,
                )
                for Accepted in Accepted
            ]
            Acceptorders = Acceptorder.objects.bulk_create(objs)
            Accepted.delete()
            messageacknowledgetokeni=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberaccept).values_list('tokens',flat=True).first()
            messageacknowledgetoken = ["dHEGNR4YGO8a-AVQWfIE33:APA91bGkNxUcRZEHJQCkUy3k3THUEMxml9q4819bDQw1b8UkD05qThidgXq3Nnr46I1pwQikZgwiGFuBgKwUxHO6kUXI9KId3ZK0fQ0zi83QegTtVimqV18a2pDqBq5qnJf-BK74Z1nL", messageacknowledgetokeni]
            acknowledge(request, messageacknowledgetoken)
            MessageRider(request)
            return HttpResponseRedirect('/index/pos')

        if len(Acceptorder.objects.filter(Admin=userr))>0:
            acceptedorder = Acceptorder.objects.filter(Admin=userr).distinct('contactnumber')
            acceptedorderall = Acceptorder.objects.filter(Admin=userr)
        else:
            acceptedorder = Acceptorder.objects.none()
            acceptedorderall = Acceptorder.objects.none()
        viewordersacceptii={}
        arrayoneaccept=[]
        contactdistincteraccepti = Acceptorder.objects.filter(Admin=userr).distinct('contactnumber')
        contactdistincteraccept=contactdistincteraccepti.values_list('contactnumber',flat=True)
        i=0
        for cndistinctaccept in contactdistincteraccept:
            arrayseparatoracceptiii=Acceptorder.objects.filter(Admin=userr,contactnumber=cndistinctaccept).exclude(productname='Ready').values()
            arrayseparatoraccepti = list(arrayseparatoracceptiii)
            arrayseparatoraccept=json.dumps(arrayseparatoraccepti, cls=JSONEncoder)
            viewordersacceptii[contactdistincteraccept[i]]=arrayseparatoraccept
            i=i+1
        viewordersaccepti=viewordersacceptii
        viewordersaccept=json.dumps(viewordersaccepti, cls=JSONEncoder)
        

        if (request.GET.get('rider') == "") and (request.GET.get('contactnoreject') or request.GET.get('contactnoaccepted')):
            if request.GET.get('contactnoreject'):
                contactnumberreject = request.GET.get('contactnoreject')
                Rejected = Customer.objects.filter(Admin=userr,contactnumber=contactnumberreject)
            elif request.GET.get('contactnoaccepted'):
                contactnumberreject = request.GET.get('contactnoaccepted')
                if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject, productname='Ready'):
                    deletethis=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject, productname='Ready')
                    deletethis.delete()
                Rejected = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject)
            
            objs = [Rejectorder(
                        Admin=userr,
                        Customername=Rejected.Customername,
                        codecoupon=Rejected.codecoupon,
                        discount=Rejected.discount or None,
                        Province=Rejected.Province,
                        MunicipalityCity=Rejected.MunicipalityCity,
                        Barangay=Rejected.Barangay,
                        StreetPurok=Rejected.StreetPurok,
                        Housenumber=Rejected.Housenumber or None,
                        LandmarksnNotes=Rejected.LandmarksnNotes or None,
                        DeliveryFee=Rejected.DeliveryFee or 0,
                        contactnumber=Rejected.contactnumber,
                        productname=Rejected.productname,
                        Category=Rejected.Category,
                        Subcategory=Rejected.Subcategory or None,
                        Size=Rejected.Size  or None,
                        PSize=Rejected.PSize or None,
                        Addons=Rejected.Addons or None,
                        QtyAddons= Rejected.QtyAddons or 0,
                        Price=Rejected.Price,
                        Subtotal = Rejected.Subtotal,
                        GSubtotal=Rejected.GSubtotal,
                        Cost=Rejected.Cost,
                        Qty=Rejected.Qty,
                        Bill=Rejected.Bill or 0,
                        Change=Rejected.Change or 0,
                        MOP=Rejected.MOP,
                        ordertype='Online',
                        Timetodeliver=Rejected.Timetodeliver,
                        ScheduleTime=Rejected.ScheduleTime,
                        gpslat = Rejected.gpslat,
                        gpslng = Rejected.gpslng,
                        gpsaccuracy = Rejected.gpsaccuracy,
                        pinnedlat = Rejected.pinnedlat,
                        pinnedlng = Rejected.pinnedlng,
                            
                        tokens = Rejected.tokens  or None,
                        DateTime=Rejected.DateTime,
                )
                for Rejected in Rejected
            ]
            Rejectorders = Rejectorder.objects.bulk_create(objs)
            Rejected.delete()
            return HttpResponseRedirect('/index/pos')

        if len(Rejectorder.objects.filter(Admin=userr))>0:
            rejectedorder = Rejectorder.objects.filter(Admin=userr).distinct('contactnumber')
            rejectedorderall = Rejectorder.objects.filter(Admin=userr)
        else:
            rejectedorder = Rejectorder.objects.none()
            rejectedorderall = Rejectorder.objects.none()
        viewordersrejectii={}
        arrayonereject=[]
        contactdistincterrejecti = Rejectorder.objects.filter(Admin=userr).distinct('contactnumber')
        contactdistincterreject=contactdistincterrejecti.values_list('contactnumber',flat=True)
        i=0
        for cndistinctreject in contactdistincterreject:
            arrayseparatorrejectiii=Rejectorder.objects.filter(Admin=userr,contactnumber=cndistinctreject).exclude(productname='Ready').values()
            arrayseparatorrejecti = list(arrayseparatorrejectiii)
            arrayseparatorreject=json.dumps(arrayseparatorrejecti, cls=JSONEncoder)
            viewordersrejectii[contactdistincterreject[i]]=arrayseparatorreject
            i=i+1
        viewordersrejecti=viewordersrejectii
        viewordersreject=json.dumps(viewordersrejecti, cls=JSONEncoder)

        

        if request.GET.get('contactnorestore'):
            contactnumberrestore = request.GET.get('contactnorestore')
            Restored = Rejectorder.objects.filter(Admin=userr,contactnumber=contactnumberrestore)
            
            objs = [Customer(
                        Admin=userr,
                        Customername=Restored.Customername,
                        codecoupon=Restored.codecoupon,
                        discount=Restored.discount or None,
                        Province=Restored.Province,
                        MunicipalityCity=Restored.MunicipalityCity,
                        Barangay=Restored.Barangay,
                        StreetPurok=Restored.StreetPurok,
                        Housenumber=Restored.Housenumber or None,
                        LandmarksnNotes=Restored.LandmarksnNotes or None,
                        DeliveryFee=Restored.DeliveryFee or 0,
                        contactnumber=Restored.contactnumber,
                        productname=Restored.productname,
                        Category=Restored.Category,
                        Subcategory=Restored.Subcategory or None,
                        Size=Restored.Size  or None,
                        PSize=Restored.PSize or None,
                        Addons=Restored.Addons or None,
                        QtyAddons= Restored.QtyAddons or 0,
                        Price=Restored.Price,
                        Subtotal = Restored.Subtotal,
                        GSubtotal=Restored.GSubtotal,
                        Cost=Restored.Cost,
                        Qty=Restored.Qty,
                        Bill=Restored.Bill or 0,
                        Change=Restored.Change or 0,
                        MOP=Restored.MOP,
                        ordertype='Online',
                        Timetodeliver=Restored.Timetodeliver,
                        ScheduleTime=Restored.ScheduleTime,
                        gpslat = Restored.gpslat,
                        gpslng = Restored.gpslng,
                        gpsaccuracy = Restored.gpsaccuracy,
                        pinnedlat = Restored.pinnedlat,
                        pinnedlng = Restored.pinnedlng,
                          
                        tokens = Restored.tokens  or None,
                        DateTime=Restored.DateTime,
                )
                for Restored in Restored
            ]
            Restore = Customer.objects.bulk_create(objs)
            Restored.delete()
            return HttpResponseRedirect('/index/pos')

        if len(Customer.objects.filter(Admin=userr))>0:
            onlineorder = Customer.objects.filter(Admin=userr).distinct('contactnumber')
            onlineorderall = Customer.objects.filter(Admin=userr)
        else:
            onlineorder = Customer.objects.none()
            onlineorderall = Customer.objects.none()
        viewordersii={}
        arrayone=[]
        contactdistincteri = Customer.objects.filter(Admin=userr).distinct('contactnumber')
        contactdistincter=contactdistincteri.values_list('contactnumber',flat=True)
        i=0
        for cndistinct in contactdistincter:  
            arrayseparatoriii=Customer.objects.filter(Admin=userr,contactnumber=cndistinct).values()
            arrayseparatori = list(arrayseparatoriii)
            arrayseparator=json.dumps(arrayseparatori, cls=JSONEncoder)
            viewordersii[contactdistincter[i]]=arrayseparator
            i=i+1
        viewordersi=viewordersii
        vieworders=json.dumps(viewordersi, cls=JSONEncoder)

        onlineordercounter = len(Customer.objects.filter(Admin=userr).distinct('contactnumber'))

        if is_ajax(request=request) and request.POST.get("Ready"):
            contactnumberready = request.POST.get('Ready')
            Readyadd = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).first()
            Readyacceptorder=Acceptorder.objects.create(
                        Admin=userr,
                        Customername=Readyadd.Customername,
                        codecoupon=Readyadd.codecoupon,
                        discount=Readyadd.discount or None,
                        Province=Readyadd.Province,
                        MunicipalityCity=Readyadd.MunicipalityCity,
                        Barangay=Readyadd.Barangay,
                        StreetPurok=Readyadd.StreetPurok,
                        Housenumber=Readyadd.Housenumber or None,
                        LandmarksnNotes=Readyadd.LandmarksnNotes or None,
                        DeliveryFee=0,
                        contactnumber=Readyadd.contactnumber,
                        productname='Ready',
                        Category=Readyadd.Category,
                        Subcategory=None,
                        Size=None,
                        PSize=None,
                        Addons=None,
                        QtyAddons= 0,
                        Price=0,
                        Subtotal = 0,
                        GSubtotal=Readyadd.GSubtotal,
                        Cost=0,
                        Qty=0,
                        Bill=Readyadd.Bill or 0,
                        Change=Readyadd.Change or 0,
                        MOP=Readyadd.MOP,
                        ordertype='Online',
                        Timetodeliver=Readyadd.Timetodeliver,
                        ScheduleTime=Readyadd.ScheduleTime,
                        gpslat = Readyadd.gpslat,
                        gpslng = Readyadd.gpslng,
                        gpsaccuracy = Readyadd.gpsaccuracy,
                        pinnedlat = Readyadd.pinnedlat,
                        pinnedlng = Readyadd.pinnedlng,
                            
                        tokens = Readyadd.tokens  or None,
                        DateTime=Readyadd.DateTime,
                        )
            Readyacceptorder.save()
            if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready, MOP='COD'):
                orderprepared(request)
            messageacknowledgetokeni=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('tokens',flat=True).first()
            messageacknowledgetoken = ["dHEGNR4YGO8a-AVQWfIE33:APA91bGkNxUcRZEHJQCkUy3k3THUEMxml9q4819bDQw1b8UkD05qThidgXq3Nnr46I1pwQikZgwiGFuBgKwUxHO6kUXI9KId3ZK0fQ0zi83QegTtVimqV18a2pDqBq5qnJf-BK74Z1nL", messageacknowledgetokeni]
            if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('MOP',flat=True).first() == 'COD' or Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('MOP',flat=True).first() == 'GcashDelivery':
                deliveryotwRider(request)
                deliveryotwCustomer(request , messageacknowledgetoken)
            else:
                pickupCustomer(request , messageacknowledgetoken)
            return JsonResponse({'Ready':'Ready'})
        if is_ajax(request=request) and request.GET.get("apini"):
            onlineordercounterf = onlineordercounter
            onlineorderf = [serializers.serialize('json',onlineorder, cls=JSONEncoder),vieworders]
            return JsonResponse({'onlineorderf':onlineorderf})
            
        if is_ajax(request=request) and request.POST.get('doneorders'):
            contactnumberdonei = json.loads(request.POST.get('doneorders'))
            contactnumberdone = contactnumberdonei[0]['contactnumber']
            if contactnumberdonei[0]['codecoupon']:
                if couponlist.objects.filter(code=contactnumberdonei[0]['codecoupon']):
                    codeconsumereducerii=couponlist.objects.get(code=contactnumberdonei[0]['codecoupon'])
                    if codeconsumereducerii.is_consumable == True and codeconsumereducerii.redeemlimit>0:
                        codeconsumereduceri=int(codeconsumereducerii.redeemlimit)-1
                        codeconsumereducer=couponlist.objects.filter(code=contactnumberdonei[0]['codecoupon']).update(redeemlimit=codeconsumereduceri)
                    else:
                        pass
                else:
                    pass
            else:
                pass
            if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone, productname='Ready'):
                deletethis=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone, productname='Ready')
                deletethis.delete()
            Done = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone)
            try:
                Sales.objects.filter(contactnumber=contactnumberdonei[0]['contactnumber'], CusName=contactnumberdonei[0]['Customername'], productname='DeliveryFee', DateTime=contactnumberdonei[0]['DateTime'])
                deliveryfeepaid='true'
            except Sales.DoesNotExist:
                deliveryfeepaid='false'
            if contactnumberdonei[0]['DeliveryFee'] != None and deliveryfeepaid == 'true':
                devfeeassales=Sales.objects.create(
                        user=userr,
                        CusName=contactnumberdonei[0]['Customername'],
                        codecoupon=contactnumberdonei[0]['codecoupon'] or None,
                        discount=contactnumberdonei[0]['discount'] or None,
                        Province=contactnumberdonei[0]['Province'],
                        MunicipalityCity=contactnumberdonei[0]['MunicipalityCity'],
                        Barangay=contactnumberdonei[0]['Barangay'],
                        StreetPurok=contactnumberdonei[0]['StreetPurok'],
                        Housenumber=contactnumberdonei[0]['Housenumber'] or None,
                        LandmarksnNotes=contactnumberdonei[0]['LandmarksnNotes'] or None,
                        DeliveryFee=contactnumberdonei[0]['DeliveryFee'] or None,
                        contactnumber=contactnumberdonei[0]['contactnumber'],
                        productname='DeliveryFee',
                        Category='DeliveryFee',
                        Subcategory='DeliveryFee',
                        Size=None,
                        PSize=None,
                        Addons=None,
                        QtyAddons=0,
                        Price=contactnumberdonei[0]['DeliveryFee'],
                        Subtotal = contactnumberdonei[0]['DeliveryFee'],
                        GSubtotal=contactnumberdonei[0]['GSubtotal'],
                        Cost=0,
                        Qty=1,
                        Bill=contactnumberdonei[0]['Bill'] or 0,
                        Change=contactnumberdonei[0]['Change'] or 0,
                        MOP=contactnumberdonei[0]['MOP'],
                        ordertype='Online',
                        Timetodeliver=contactnumberdonei[0]['Timetodeliver'] or None,
                        ScheduleTime=contactnumberdonei[0]['ScheduleTime'] or None,
                        gpslat = contactnumberdonei[0]['gpslat'],
                        gpslng = contactnumberdonei[0]['gpslng'],
                        gpsaccuracy = contactnumberdonei[0]['gpsaccuracy'],
                        pinnedlat = contactnumberdonei[0]['pinnedlat'],
                        pinnedlng = contactnumberdonei[0]['pinnedlng'],
                            
                        tokens = contactnumberdonei[0]['tokens'] or None,
                        DateTime=contactnumberdonei[0]['DateTime'],
                )
                devfeeassales.save()
            if contactnumberdonei[0]['discount']:
                objs = [Sales(
                            user=userr,
                            CusName=Done.Customername,
                            codecoupon=Done.codecoupon,
                            discount=Done.discount or None,
                            Province=Done.Province,
                            MunicipalityCity=Done.MunicipalityCity,
                            Barangay=Done.Barangay,
                            StreetPurok=Done.StreetPurok,
                            Housenumber=Done.Housenumber or None,
                            LandmarksnNotes=Done.LandmarksnNotes or None,
                            DeliveryFee=Done.DeliveryFee or None,
                            contactnumber=Done.contactnumber,
                            productname=Done.productname,
                            Category=Done.Category,
                            Subcategory=Done.Subcategory or None,
                            Size=Done.Size  or None,
                            PSize=Done.PSize or None,
                            Addons=Done.Addons or None,
                            QtyAddons= Done.QtyAddons or 0,
                            Price=Done.Price,
                            Subtotal = Done.Subtotal-((Done.Subtotal)*(Decimal(int(Done.discount)/100))),
                            GSubtotal=Done.GSubtotal,
                            Cost=Done.Cost,
                            Qty=Done.Qty,
                            Bill=Done.Bill or 0,
                            Change=Done.Change or 0,
                            MOP=Done.MOP,
                            ordertype='Online',
                            Timetodeliver=Done.Timetodeliver,
                            ScheduleTime=Done.ScheduleTime,
                            gpslat = Done.gpslat,
                            gpslng = Done.gpslng,
                            gpsaccuracy = Done.gpsaccuracy,
                            pinnedlat = Done.pinnedlat,
                            pinnedlng = Done.pinnedlng,
                            
                            tokens = Done.tokens or None,
                            DateTime=Done.DateTime,
                    )
                    for Done in Done
                ]
            else:
                objs = [Sales(
                            user=userr,
                            CusName=Done.Customername,
                            codecoupon=Done.codecoupon,
                            discount=Done.discount or None,
                            Province=Done.Province,
                            MunicipalityCity=Done.MunicipalityCity,
                            Barangay=Done.Barangay,
                            StreetPurok=Done.StreetPurok,
                            Housenumber=Done.Housenumber or None,
                            LandmarksnNotes=Done.LandmarksnNotes or None,
                            DeliveryFee=Done.DeliveryFee or None,
                            contactnumber=Done.contactnumber,
                            productname=Done.productname,
                            Category=Done.Category,
                            Subcategory=Done.Subcategory or None,
                            Size=Done.Size  or None,
                            PSize=Done.PSize or None,
                            Addons=Done.Addons or None,
                            QtyAddons= Done.QtyAddons or 0,
                            Price=Done.Price,
                            Subtotal = Done.Subtotal,
                            GSubtotal=Done.GSubtotal,
                            Cost=Done.Cost,
                            Qty=Done.Qty,
                            Bill=Done.Bill or 0,
                            Change=Done.Change or 0,
                            MOP=Done.MOP,
                            ordertype='Online',
                            Timetodeliver=Done.Timetodeliver,
                            ScheduleTime=Done.ScheduleTime,
                            gpslat = Done.gpslat,
                            gpslng = Done.gpslng,
                            gpsaccuracy = Done.gpsaccuracy,
                            pinnedlat = Done.pinnedlat,
                            pinnedlng = Done.pinnedlng,
                            
                            tokens = Done.tokens or None,
                            DateTime=Done.DateTime,
                    )
                    for Done in Done
                ]
            Salesorders = Sales.objects.bulk_create(objs)
            Done.delete()

        ####### BASE Order from website ######
        notifyorder=acknowledgedstockorder.objects.filter(CusName="Notify",user=userr).count()
        if acknowledgedstockorder.objects.all().count()==0:
           notifyadmin=submitstockorder.objects.all().count()
        else:
           notifyadmin=0
        if len(Acceptorder.objects.filter(Admin=userr, productname='Ready'))>0:
            initial=Acceptorder.objects.filter(Admin=userr, productname='Ready').values_list('contactnumber', flat=True)
            readylistcontact=list(initial)
        else:
            readylistcontact=list(Acceptorder.objects.none())
        print('readylistcontact1:',readylistcontact)
        productss = user1.objects.all().filter(user__id=userr).order_by('-id')
        submitted = False
        if request.method == "POST":
            aprod = editform(request.POST)
            if aprod.is_valid():
                aprod.save()
                
                return render(request, 'Products.html',{'readylistcontact':readylistcontact,'onlineordercounter':onlineordercounter,'viewordersreject':viewordersreject,'rejectedorder':rejectedorder,'viewordersaccept':viewordersaccept,'acceptedorder':acceptedorder,'onlineorder':onlineorder,'notifyadmin':notifyadmin,'notifyorder':notifyorder,'productss':productss,'aprod':aprod,'submitted':submitted,'userr':userr})
            else:
                return render(request, 'Products.html',{'readylistcontact':readylistcontact,'onlineordercounter':onlineordercounter,'viewordersreject':viewordersreject,'rejectedorder':rejectedorder,'viewordersaccept':viewordersaccept,'acceptedorder':acceptedorder,'onlineorder':onlineorder,'notifyadmin':notifyadmin,'notifyorder':notifyorder,'productss':productss,'aprod':aprod,'submitted':submitted,'userr':userr})
        else:
           aprod = editform
           return render(request, 'Products.html',{'readylistcontact':readylistcontact,'onlineordercounter':onlineordercounter,'viewordersreject':viewordersreject,'rejectedorder':rejectedorder,'viewordersaccept':viewordersaccept,'acceptedorder':acceptedorder,'onlineorder':onlineorder,'notifyadmin':notifyadmin,'notifyorder':notifyorder,'productss':productss,'aprod':aprod,'submitted':submitted,'userr':userr})

@login_required
def posthree(request):
        userr=request.user.id
        #print(Acceptorder.objects.filter(Customername='Ysabelle Caluza').values_list('LocationMarker', flat=True)[0])
        if request.GET.get('acceptcontactno'):
            contactnumberaccept = request.GET.get('acceptcontactno')
            rider = request.GET.get('rider')
            getETA = request.GET.get('ETA')
            Accepted = Customer.objects.filter(Admin=userr,contactnumber=contactnumberaccept)
            
            objs = [Acceptorder(
                        Admin=Accepted.Admin,
                        Customername=Accepted.Customername,
                        codecoupon=Accepted.codecoupon,
                        discount=Accepted.discount or None,
                        Province=Accepted.Province,
                        MunicipalityCity=Accepted.MunicipalityCity,
                        Barangay=Accepted.Barangay,
                        StreetPurok=Accepted.StreetPurok,
                        Housenumber=Accepted.Housenumber or None,
                        LandmarksnNotes=Accepted.LandmarksnNotes or None,
                        DeliveryFee=Accepted.DeliveryFee or 0,
                        contactnumber=Accepted.contactnumber,
                        Rider=rider,
                        productname=Accepted.productname,
                        Category=Accepted.Category,
                        Subcategory=Accepted.Subcategory or None,
                        Size=Accepted.Size  or None,
                        PSize=Accepted.PSize or None,
                        Addons=Accepted.Addons or None,
                        QtyAddons= Accepted.QtyAddons or 0,
                        Price=Accepted.Price,
                        Subtotal = Accepted.Subtotal,
                        GSubtotal=Accepted.GSubtotal,
                        Cost=Accepted.Cost,
                        Qty=Accepted.Qty,
                        Bill=Accepted.Bill or 0,
                        Change=Accepted.Change or 0,
                        ETA=getETA,
                        MOP=Accepted.MOP,
                        ordertype='Online',
                        Timetodeliver=Accepted.Timetodeliver,
                        ScheduleTime=Accepted.ScheduleTime,
                        gpslat = Accepted.gpslat,
                        gpslng = Accepted.gpslng,
                        gpsaccuracy = Accepted.gpsaccuracy,
                        pinnedlat = Accepted.pinnedlat,
                        pinnedlng = Accepted.pinnedlng,
                        tokens = Accepted.tokens or None,
                        DateTime=Accepted.DateTime,
                )
                for Accepted in Accepted
            ]
            Acceptorders = Acceptorder.objects.bulk_create(objs)
            Accepted.delete()
            messageacknowledgetokeni=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberaccept).values_list('tokens',flat=True).first()
            messageacknowledgetoken = ["dHEGNR4YGO8a-AVQWfIE33:APA91bGkNxUcRZEHJQCkUy3k3THUEMxml9q4819bDQw1b8UkD05qThidgXq3Nnr46I1pwQikZgwiGFuBgKwUxHO6kUXI9KId3ZK0fQ0zi83QegTtVimqV18a2pDqBq5qnJf-BK74Z1nL", messageacknowledgetokeni]
            acknowledge(request, messageacknowledgetoken)
            MessageRider(request)
            return HttpResponseRedirect('/index/pos')

        if len(Acceptorder.objects.filter(Admin=userr))>0:
            acceptedorder = Acceptorder.objects.filter(Admin=userr).distinct('contactnumber')
            acceptedorderall = Acceptorder.objects.filter(Admin=userr)
        else:
            acceptedorder = Acceptorder.objects.none()
            acceptedorderall = Acceptorder.objects.none()
        viewordersacceptii={}
        arrayoneaccept=[]
        contactdistincteraccepti = Acceptorder.objects.filter(Admin=userr).distinct('contactnumber')
        contactdistincteraccept=contactdistincteraccepti.values_list('contactnumber',flat=True)
        i=0
        for cndistinctaccept in contactdistincteraccept:
            arrayseparatoracceptiii=Acceptorder.objects.filter(Admin=userr,contactnumber=cndistinctaccept).exclude(productname='Ready').values()
            arrayseparatoraccepti = list(arrayseparatoracceptiii)
            arrayseparatoraccept=json.dumps(arrayseparatoraccepti, cls=JSONEncoder)
            viewordersacceptii[contactdistincteraccept[i]]=arrayseparatoraccept
            i=i+1
        viewordersaccepti=viewordersacceptii
        viewordersaccept=json.dumps(viewordersaccepti, cls=JSONEncoder)
        

        if (request.GET.get('rider') == "") and (request.GET.get('contactnoreject') or request.GET.get('contactnoaccepted')):
            if request.GET.get('contactnoreject'):
                contactnumberreject = request.GET.get('contactnoreject')
                Rejected = Customer.objects.filter(Admin=userr,contactnumber=contactnumberreject)
            elif request.GET.get('contactnoaccepted'):
                contactnumberreject = request.GET.get('contactnoaccepted')
                if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject, productname='Ready'):
                    deletethis=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject, productname='Ready')
                    deletethis.delete()
                Rejected = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject)
            
            objs = [Rejectorder(
                        Admin=userr,
                        Customername=Rejected.Customername,
                        codecoupon=Rejected.codecoupon,
                        discount=Rejected.discount or None,
                        Province=Rejected.Province,
                        MunicipalityCity=Rejected.MunicipalityCity,
                        Barangay=Rejected.Barangay,
                        StreetPurok=Rejected.StreetPurok,
                        Housenumber=Rejected.Housenumber or None,
                        LandmarksnNotes=Rejected.LandmarksnNotes or None,
                        DeliveryFee=Rejected.DeliveryFee or 0,
                        contactnumber=Rejected.contactnumber,
                        productname=Rejected.productname,
                        Category=Rejected.Category,
                        Subcategory=Rejected.Subcategory or None,
                        Size=Rejected.Size  or None,
                        PSize=Rejected.PSize or None,
                        Addons=Rejected.Addons or None,
                        QtyAddons= Rejected.QtyAddons or 0,
                        Price=Rejected.Price,
                        Subtotal = Rejected.Subtotal,
                        GSubtotal=Rejected.GSubtotal,
                        Cost=Rejected.Cost,
                        Qty=Rejected.Qty,
                        Bill=Rejected.Bill or 0,
                        Change=Rejected.Change or 0,
                        MOP=Rejected.MOP,
                        ordertype='Online',
                        Timetodeliver=Rejected.Timetodeliver,
                        ScheduleTime=Rejected.ScheduleTime,
                        gpslat = Rejected.gpslat,
                        gpslng = Rejected.gpslng,
                        gpsaccuracy = Rejected.gpsaccuracy,
                        pinnedlat = Rejected.pinnedlat,
                        pinnedlng = Rejected.pinnedlng,
                        tokens = Rejected.tokens  or None,
                        DateTime=Rejected.DateTime,
                )
                for Rejected in Rejected
            ]
            Rejectorders = Rejectorder.objects.bulk_create(objs)
            Rejected.delete()
            return HttpResponseRedirect('/index/pos')

        if len(Rejectorder.objects.filter(Admin=userr))>0:
            rejectedorder = Rejectorder.objects.filter(Admin=userr).distinct('contactnumber')
            rejectedorderall = Rejectorder.objects.filter(Admin=userr)
        else:
            rejectedorder = Rejectorder.objects.none()
            rejectedorderall = Rejectorder.objects.none()
        viewordersrejectii={}
        arrayonereject=[]
        contactdistincterrejecti = Rejectorder.objects.filter(Admin=userr).distinct('contactnumber')
        contactdistincterreject=contactdistincterrejecti.values_list('contactnumber',flat=True)
        i=0
        for cndistinctreject in contactdistincterreject:
            arrayseparatorrejectiii=Rejectorder.objects.filter(Admin=userr,contactnumber=cndistinctreject).exclude(productname='Ready').values()
            arrayseparatorrejecti = list(arrayseparatorrejectiii)
            arrayseparatorreject=json.dumps(arrayseparatorrejecti, cls=JSONEncoder)
            viewordersrejectii[contactdistincterreject[i]]=arrayseparatorreject
            i=i+1
        viewordersrejecti=viewordersrejectii
        viewordersreject=json.dumps(viewordersrejecti, cls=JSONEncoder)

        

        if request.GET.get('contactnorestore'):
            contactnumberrestore = request.GET.get('contactnorestore')
            Restored = Rejectorder.objects.filter(Admin=userr,contactnumber=contactnumberrestore)
            
            objs = [Customer(
                        Admin=userr,
                        Customername=Restored.Customername,
                        codecoupon=Restored.codecoupon,
                        discount=Restored.discount or None,
                        Province=Restored.Province,
                        MunicipalityCity=Restored.MunicipalityCity,
                        Barangay=Restored.Barangay,
                        StreetPurok=Restored.StreetPurok,
                        Housenumber=Restored.Housenumber or None,
                        LandmarksnNotes=Restored.LandmarksnNotes or None,
                        DeliveryFee=Restored.DeliveryFee or 0,
                        contactnumber=Restored.contactnumber,
                        productname=Restored.productname,
                        Category=Restored.Category,
                        Subcategory=Restored.Subcategory or None,
                        Size=Restored.Size  or None,
                        PSize=Restored.PSize or None,
                        Addons=Restored.Addons or None,
                        QtyAddons= Restored.QtyAddons or 0,
                        Price=Restored.Price,
                        Subtotal = Restored.Subtotal,
                        GSubtotal=Restored.GSubtotal,
                        Cost=Restored.Cost,
                        Qty=Restored.Qty,
                        Bill=Restored.Bill or 0,
                        Change=Restored.Change or 0,
                        MOP=Restored.MOP,
                        ordertype='Online',
                        Timetodeliver=Restored.Timetodeliver,
                        ScheduleTime=Restored.ScheduleTime,
                        gpslat = Restored.gpslat,
                        gpslng = Restored.gpslng,
                        gpsaccuracy = Restored.gpsaccuracy,
                        pinnedlat = Restored.pinnedlat,
                        pinnedlng = Restored.pinnedlng,
                        
                        tokens = Restored.tokens  or None,
                        DateTime=Restored.DateTime,
                )
                for Restored in Restored
            ]
            Restore = Customer.objects.bulk_create(objs)
            Restored.delete()
            return HttpResponseRedirect('/index/pos')

        if len(Customer.objects.filter(Admin=userr))>0:
            onlineorder = Customer.objects.filter(Admin=userr).distinct('contactnumber')
            onlineorderall = Customer.objects.filter(Admin=userr)
        else:
            onlineorder = Customer.objects.none()
            onlineorderall = Customer.objects.none()
        viewordersii={}
        arrayone=[]
        contactdistincteri = Customer.objects.filter(Admin=userr).distinct('contactnumber')
        contactdistincter=contactdistincteri.values_list('contactnumber',flat=True)
        i=0
        for cndistinct in contactdistincter:  
            arrayseparatoriii=Customer.objects.filter(Admin=userr,contactnumber=cndistinct).values()
            arrayseparatori = list(arrayseparatoriii)
            arrayseparator=json.dumps(arrayseparatori, cls=JSONEncoder)
            viewordersii[contactdistincter[i]]=arrayseparator
            i=i+1
        viewordersi=viewordersii
        vieworders=json.dumps(viewordersi, cls=JSONEncoder)

        onlineordercounter = len(Customer.objects.filter(Admin=userr).distinct('contactnumber'))

        if is_ajax(request=request) and request.POST.get("Ready"):
            contactnumberready = request.POST.get('Ready')
            Readyadd = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).first()
            Readyacceptorder=Acceptorder.objects.create(
                        Admin=userr,
                        Customername=Readyadd.Customername,
                        codecoupon=Readyadd.codecoupon,
                        discount=Readyadd.discount or None,
                        Province=Readyadd.Province,
                        MunicipalityCity=Readyadd.MunicipalityCity,
                        Barangay=Readyadd.Barangay,
                        StreetPurok=Readyadd.StreetPurok,
                        Housenumber=Readyadd.Housenumber or None,
                        LandmarksnNotes=Readyadd.LandmarksnNotes or None,
                        DeliveryFee=0,
                        contactnumber=Readyadd.contactnumber,
                        productname='Ready',
                        Category=Readyadd.Category,
                        Subcategory=None,
                        Size=None,
                        PSize=None,
                        Addons=None,
                        QtyAddons= 0,
                        Price=0,
                        Subtotal = 0,
                        GSubtotal=Readyadd.GSubtotal,
                        Cost=0,
                        Qty=0,
                        Bill=Readyadd.Bill or 0,
                        Change=Readyadd.Change or 0,
                        MOP=Readyadd.MOP,
                        ordertype='Online',
                        Timetodeliver=Readyadd.Timetodeliver,
                        ScheduleTime=Readyadd.ScheduleTime,
                        gpslat = Readyadd.gpslat,
                        gpslng = Readyadd.gpslng,
                        gpsaccuracy = Readyadd.gpsaccuracy,
                        pinnedlat = Readyadd.pinnedlat,
                        pinnedlng = Readyadd.pinnedlng,
                        
                        tokens = Readyadd.tokens  or None,
                        DateTime=Readyadd.DateTime,
                        )
            Readyacceptorder.save()
            if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready, MOP='COD'):
                orderprepared(request)
            messageacknowledgetokeni=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('tokens',flat=True).first()
            messageacknowledgetoken = ["dHEGNR4YGO8a-AVQWfIE33:APA91bGkNxUcRZEHJQCkUy3k3THUEMxml9q4819bDQw1b8UkD05qThidgXq3Nnr46I1pwQikZgwiGFuBgKwUxHO6kUXI9KId3ZK0fQ0zi83QegTtVimqV18a2pDqBq5qnJf-BK74Z1nL", messageacknowledgetokeni]
            if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('MOP',flat=True).first() == 'COD' or Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('MOP',flat=True).first() == 'GcashDelivery':
                deliveryotwRider(request)
                deliveryotwCustomer(request , messageacknowledgetoken)
            else:
                pickupCustomer(request , messageacknowledgetoken)
            return JsonResponse({'Ready':'Ready'})
        if is_ajax(request=request) and request.GET.get("apini"):
            onlineordercounterf = onlineordercounter
            onlineorderf = [serializers.serialize('json',onlineorder, cls=JSONEncoder),vieworders]

            return JsonResponse({'onlineorderf':onlineorderf})
            
        if is_ajax(request=request) and request.POST.get('doneorders'):
            contactnumberdonei = json.loads(request.POST.get('doneorders'))
            contactnumberdone = contactnumberdonei[0]['contactnumber']
            if contactnumberdonei[0]['codecoupon']:
                if couponlist.objects.filter(code=contactnumberdonei[0]['codecoupon']):
                    codeconsumereducerii=couponlist.objects.get(code=contactnumberdonei[0]['codecoupon'])
                    if codeconsumereducerii.is_consumable == True and codeconsumereducerii.redeemlimit > 0:
                        codeconsumereduceri=int(codeconsumereducerii.redeemlimit)-1
                        codeconsumereducer=couponlist.objects.filter(code=contactnumberdonei[0]['codecoupon']).update(redeemlimit=codeconsumereduceri)
                    else:
                        pass
                else:
                    pass
            else:
                pass
            if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone, productname='Ready'):
                deletethis=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone, productname='Ready')
                deletethis.delete()
            Done = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone)
            try:
                Sales.objects.filter(contactnumber=contactnumberdonei[0]['contactnumber'], CusName=contactnumberdonei[0]['Customername'], productname='DeliveryFee', DateTime=contactnumberdonei[0]['DateTime'])
                deliveryfeepaid='true'
            except Sales.DoesNotExist:
                deliveryfeepaid='false'
            if contactnumberdonei[0]['DeliveryFee'] != None and deliveryfeepaid == 'true':
                devfeeassales=Sales.objects.create(
                        user=userr,
                        CusName=contactnumberdonei[0]['Customername'],
                        codecoupon=contactnumberdonei[0]['codecoupon'] or None,
                        discount=contactnumberdonei[0]['discount'] or None,
                        Province=contactnumberdonei[0]['Province'],
                        MunicipalityCity=contactnumberdonei[0]['MunicipalityCity'],
                        Barangay=contactnumberdonei[0]['Barangay'],
                        StreetPurok=contactnumberdonei[0]['StreetPurok'],
                        Housenumber=contactnumberdonei[0]['Housenumber'] or None,
                        LandmarksnNotes=contactnumberdonei[0]['LandmarksnNotes'] or None,
                        DeliveryFee=contactnumberdonei[0]['DeliveryFee'] or None,
                        contactnumber=contactnumberdonei[0]['contactnumber'],
                        productname='DeliveryFee',
                        Category='DeliveryFee',
                        Subcategory='DeliveryFee',
                        Size=None,
                        PSize=None,
                        Addons=None,
                        QtyAddons=0,
                        Price=contactnumberdonei[0]['DeliveryFee'],
                        Subtotal = contactnumberdonei[0]['DeliveryFee'],
                        GSubtotal=contactnumberdonei[0]['GSubtotal'],
                        Cost=0,
                        Qty=1,
                        Bill=contactnumberdonei[0]['Bill'] or 0,
                        Change=contactnumberdonei[0]['Change'] or 0,
                        MOP=contactnumberdonei[0]['MOP'],
                        ordertype='Online',
                        Timetodeliver=contactnumberdonei[0]['Timetodeliver'] or None,
                        ScheduleTime=contactnumberdonei[0]['ScheduleTime'] or None,
                        gpslat = contactnumberdonei[0]['gpslat'],
                        gpslng = contactnumberdonei[0]['gpslng'],
                        gpsaccuracy = contactnumberdonei[0]['gpsaccuracy'],
                        pinnedlat = contactnumberdonei[0]['pinnedlat'],
                        pinnedlng = contactnumberdonei[0]['pinnedlng'],
                        
                        tokens = contactnumberdonei[0]['tokens'] or None,
                        DateTime=contactnumberdonei[0]['DateTime'],
                )
                devfeeassales.save()
            if contactnumberdonei[0]['discount']:
                objs = [Sales(
                            user=userr,
                            CusName=Done.Customername,
                            codecoupon=Done.codecoupon,
                            discount=Done.discount or None,
                            Province=Done.Province,
                            MunicipalityCity=Done.MunicipalityCity,
                            Barangay=Done.Barangay,
                            StreetPurok=Done.StreetPurok,
                            Housenumber=Done.Housenumber or None,
                            LandmarksnNotes=Done.LandmarksnNotes or None,
                            DeliveryFee=Done.DeliveryFee or None,
                            contactnumber=Done.contactnumber,
                            productname=Done.productname,
                            Category=Done.Category,
                            Subcategory=Done.Subcategory or None,
                            Size=Done.Size  or None,
                            PSize=Done.PSize or None,
                            Addons=Done.Addons or None,
                            QtyAddons= Done.QtyAddons or 0,
                            Price=Done.Price,
                            Subtotal = Done.Subtotal-((Done.Subtotal)*(Decimal(int(Done.discount)/100))),
                            GSubtotal=Done.GSubtotal,
                            Cost=Done.Cost,
                            Qty=Done.Qty,
                            Bill=Done.Bill or 0,
                            Change=Done.Change or 0,
                            MOP=Done.MOP,
                            ordertype='Online',
                            Timetodeliver=Done.Timetodeliver,
                            ScheduleTime=Done.ScheduleTime,
                            gpslat = Done.gpslat,
                            gpslng = Done.gpslng,
                            gpsaccuracy = Done.gpsaccuracy,
                            pinnedlat = Done.pinnedlat,
                            pinnedlng = Done.pinnedlng,
                       
                            tokens = Done.tokens or None,
                            DateTime=Done.DateTime,
                    )
                    for Done in Done
                ]
            else:
                objs = [Sales(
                            user=userr,
                            CusName=Done.Customername,
                            codecoupon=Done.codecoupon,
                            discount=Done.discount or None,
                            Province=Done.Province,
                            MunicipalityCity=Done.MunicipalityCity,
                            Barangay=Done.Barangay,
                            StreetPurok=Done.StreetPurok,
                            Housenumber=Done.Housenumber or None,
                            LandmarksnNotes=Done.LandmarksnNotes or None,
                            DeliveryFee=Done.DeliveryFee or None,
                            contactnumber=Done.contactnumber,
                            productname=Done.productname,
                            Category=Done.Category,
                            Subcategory=Done.Subcategory or None,
                            Size=Done.Size  or None,
                            PSize=Done.PSize or None,
                            Addons=Done.Addons or None,
                            QtyAddons= Done.QtyAddons or 0,
                            Price=Done.Price,
                            Subtotal = Done.Subtotal,
                            GSubtotal=Done.GSubtotal,
                            Cost=Done.Cost,
                            Qty=Done.Qty,
                            Bill=Done.Bill or 0,
                            Change=Done.Change or 0,
                            MOP=Done.MOP,
                            ordertype='Online',
                            Timetodeliver=Done.Timetodeliver,
                            ScheduleTime=Done.ScheduleTime,
                            gpslat = Done.gpslat,
                            gpslng = Done.gpslng,
                            gpsaccuracy = Done.gpsaccuracy,
                            pinnedlat = Done.pinnedlat,
                            pinnedlng = Done.pinnedlng,
                       
                            tokens = Done.tokens or None,
                            DateTime=Done.DateTime,
                    )
                    for Done in Done
                ]
            Salesorders = Sales.objects.bulk_create(objs)
            Done.delete()
            datetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
            monthtoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m')
            yeartoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y')
            try:
                getdailysales=Dailysales.objects.filter(user=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Sales', flat=True)[0]
                timesheetupdate=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(Sales=getdailysales)
            except IndexError:
                timesheetupdate=timesheet.objects.none()
                getdailysales=0
            if getdailysales >= 2000 and timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday):
                getinitialsalarytoday=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('ISalary', flat=True)
                getASLBALANCEtodayi=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('ASLbalance', flat=True)
                addbonusornot=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Identifybonus', flat=True)
                if addbonusornot[0] == 'Added bonus':
                    pass
                else:
                    twokeysalebonus=getinitialsalarytoday[0]+30
                    if getASLBALANCEtodayi[0] >= 30:
                        getASLBALANCEtoday=getASLBALANCEtodayi[0]-30
                        timesheetupdatetwo=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(ISalary=twokeysalebonus, ASLbalance=getASLBALANCEtoday,Identifybonus='Added bonus')
                    else:
                        getASLBALANCEtoday=0
                        addtofinalsalaryi=30-getASLBALANCEtodayi[0]
                        getfinalsalarytoday=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('FSalary', flat=True)
                        addtofinalsalary=addtofinalsalaryi+getfinalsalarytoday
                        timesheetupdatetwo=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(ISalary=twokeysalebonus, ASLbalance=getASLBALANCEtoday,Identifybonus='Added bonus',FSalary=addtofinalsalary)
            return HttpResponseRedirect('/index/pos')



        notifyorder=acknowledgedstockorder.objects.filter(CusName="Notify",user=userr).count()
        if acknowledgedstockorder.objects.all().count()==0:
            notifyadmin=submitstockorder.objects.all().count()
        else:
            notifyadmin=0
        print('userr:',userr) 
        if punchedprod.objects.filter(user=userr).count()==0:
            punchedtotal=0
        else:
            punchedtotal=punchedprod.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
        
        mtbuttons = user1.objects.filter(Category__Categorychoices='Milktea',user__id=userr).distinct('productname')
        i=0
        mtpricess={}
        mtpricesii = user1.objects.filter(Category__Categorychoices='Milktea',user__id=userr).values_list('Price',flat=True).order_by('-id')
        
        mtproductnameii=mtpricesii.values_list('productname',flat=True)
        
        mtsizeii=mtpricesii.values_list('Size__Sizechoices',flat=True)
        
        while i<mtpricesii.count():
            mtpricess[mtproductnameii[i]+mtsizeii[i]]=mtpricesii[i]

            i += 1
        mtpricesss=mtpricess
        
        mtprices=json.dumps(mtpricesss)
        
        ii=0
        mtcostss={}
        mtcostsii = user1.objects.filter(Category__Categorychoices='Milktea',user__id=userr).values_list('Cost',flat=True).order_by('-id')
        
        mtproductnameii=mtcostsii.values_list('productname',flat=True)
        
        mtsizeii=mtcostsii.values_list('Size__Sizechoices',flat=True)
        
        while ii<mtcostsii.count():
            mtcostss[mtproductnameii[ii]+mtsizeii[ii]]=mtcostsii[ii]

            ii += 1
        counter=len(mtcostss)
        
        iii=0
        keys=[]
        mtcostaaai=[]
        for key, mtcostaaa in mtcostss.items():
            keys.append(key)
            mtcostaaai.append(float(mtcostaaa))
        
        
        mtcostsss=mtcostss.values()
        mtcostsi=mtcostaaai
        mtcosts=json.dumps(mtcostsi)

        mtkeyscosts=json.dumps(keys)

        mtsizes = Sizes.objects.all()
        Categoriess = Categories.objects.all()
        Subcategoriess = Subcategories.objects.all()
        frbuttons = user1.objects.filter(Category__Categorychoices='Frappe',user__id=userr).distinct('productname')
        iiii=0
        frpricess={}
        frpricesii = user1.objects.filter(Category__Categorychoices='Frappe',user__id=userr).values_list('Price',flat=True).order_by('-id')
        
        frproductnameii=frpricesii.values_list('productname',flat=True)
        
        frsizeii=frpricesii.values_list('Size__Sizechoices',flat=True)
        
        while iiii<frpricesii.count():
            frpricess[frproductnameii[iiii]+frsizeii[iiii]]=frpricesii[iiii]

            iiii += 1
        frpricesss=frpricess
        
        frprices=json.dumps(frpricesss)

        iiiii=0
        frcostss={}
        frcostsii = user1.objects.filter(Category__Categorychoices='Frappe',user__id=userr).values_list('Cost',flat=True).order_by('-id')
        
        frproductnameii=frcostsii.values_list('productname',flat=True)
        
        frsizeii=frcostsii.values_list('Size__Sizechoices',flat=True)
        
        while iiiii<frcostsii.count():
            frcostss[frproductnameii[iiiii]+frsizeii[iiiii]]=frcostsii[iiiii]

            iiiii += 1
        counterfr=len(frcostss)
        
        iiiiii=0
        keysfr=[]
        frcostaaai=[]
        for key, frcostaaa in frcostss.items():
            keysfr.append(key)
            frcostaaai.append(float(frcostaaa))
        
        
        frcostsss=frcostss.values()
        frcostsi=frcostaaai
        frcosts=json.dumps(frcostsi)
        
        frkeyscosts=json.dumps(keysfr)
        
        frsizes = Sizes.objects.all().exclude(Sizechoices__exact='Small')
        psizes = PSizes.objects.all()
        addonsbuttons = user1.objects.filter(Category__Categorychoices='Add-ons',user__id=userr).distinct('productname')
        iiiiiii=0
        aopricess={}
        aopricesii = user1.objects.filter(Category__Categorychoices='Add-ons',user__id=userr).values_list('Price',flat=True).order_by('-id')
        
        aoproductnameii=aopricesii.values_list('productname',flat=True)
        
        #aosizeii=aopricesii.values_list('Size__Sizechoices',flat=True)
        
        while iiiiiii<aopricesii.count():
            aopricess[aoproductnameii[iiiiiii]]=aopricesii[iiiiiii]

            iiiiiii += 1
        aopricesss=aopricess
        
        aoprices=json.dumps(aopricesss)
        
        iiiiiiii=0
        aocostss={}
        aocostsii = user1.objects.filter(Category__Categorychoices='Add-ons',user__id=userr).values_list('Cost',flat=True).order_by('-id')
        
        aoproductnameii=aocostsii.values_list('productname',flat=True)
        
        
        
        while iiiiiiii<aocostsii.count():
            aocostss[aoproductnameii[iiiiiiii]]=aocostsii[iiiiiiii]

            iiiiiiii += 1
        counterao=len(aocostss)
        
        iiiiiiiii=0
        keysao=[]
        aocostaaai=[]
        for key, aocostaaa in aocostss.items():
            keysao.append(key)
            aocostaaai.append(float(aocostaaa))
        
        
        aocostsss=aocostss.values()
        aocostsi=aocostaaai
        aocosts=json.dumps(aocostsi)
       
        aokeyscosts=json.dumps(keysao)
        
        freezebuttons = user1.objects.filter(Category__Categorychoices='Freeze',user__id=userr).distinct('productname')
        
        iiiiiiiiii=0
        frzpricess={}
        frzpricesii = user1.objects.filter(Category__Categorychoices='Freeze',user__id=userr).values_list('Price',flat=True).order_by('-id')
        
        frzproductnameii=frzpricesii.values_list('productname',flat=True)
        
        #frzsizeii=frzpricesii.values_list('Size__Sizechoices',flat=True)
        
        while iiiiiiiiii<frzpricesii.count():
            frzpricess[frzproductnameii[iiiiiiiiii]]=frzpricesii[iiiiiiiiii]

            iiiiiiiiii += 1
        frzpricesss=frzpricess
        
        frzprices=json.dumps(frzpricesss)
        
        iiiiiiiiiii=0
        frzcostss={}
        frzcostsii = user1.objects.filter(Category__Categorychoices='Freeze',user__id=userr).values_list('Cost',flat=True).order_by('-id')
        
        frzproductnameii=frzcostsii.values_list('productname',flat=True)
        
        
        
        while iiiiiiiiiii<frzcostsii.count():
            frzcostss[frzproductnameii[iiiiiiiiiii]]=frzcostsii[iiiiiiiiiii]

            iiiiiiiiiii += 1
        counterfrz=len(frzcostss)
        
        iiiiiiiiiiii=0
        keysfrz=[]
        frzcostaaai=[]
        for key, frzcostaaa in frzcostss.items():
            keysfrz.append(key)
            frzcostaaai.append(float(frzcostaaa))
        
        
        frzcostsss=frzcostss.values()
        frzcostsi=frzcostaaai
        frzcosts=json.dumps(frzcostsi)
        
        frzkeyscosts=json.dumps(keysfrz)
        
        cookiesbuttons = user1.objects.filter(Subcategory__Subcategorychoices='Cookies',user__id=userr).distinct('productname')

        
        
        iiiiiiiiiiiii=0
        cookiespricess={}
        cookiespricesii = user1.objects.filter(Subcategory__Subcategorychoices='Cookies',user__id=userr).values_list('Price',flat=True).order_by('-id')
        
        cookiesproductnameii=cookiespricesii.values_list('productname',flat=True)
        
        #cookiessizeii=cookiespricesii.values_list('Size__Sizechoices',flat=True)
        
        while iiiiiiiiiiiii<cookiespricesii.count():
            cookiespricess[cookiesproductnameii[iiiiiiiiiiiii]]=cookiespricesii[iiiiiiiiiiiii]

            iiiiiiiiiiiii += 1
        cookiespricesss=cookiespricess
        
        cookiesprices=json.dumps(cookiespricesss)
        
        iiiiiiiiiiiiii=0
        cookiescostss={}
        cookiescostsii = user1.objects.filter(Subcategory__Subcategorychoices='Cookies',user__id=userr).values_list('Cost',flat=True).order_by('-id')
        
        cookiesproductnameii=cookiescostsii.values_list('productname',flat=True)
        
        
        
        while iiiiiiiiiiiiii<cookiescostsii.count():
            cookiescostss[cookiesproductnameii[iiiiiiiiiiiiii]]=cookiescostsii[iiiiiiiiiiiiii]

            iiiiiiiiiiiiii += 1
        countercookies=len(cookiescostss)
        
        iiiiiiiiiiiiiii=0
        keyscookies=[]
        cookiescostaaai=[]
        for key, cookiescostaaa in cookiescostss.items():
            keyscookies.append(key)
            cookiescostaaai.append(float(cookiescostaaa))
        
        
        cookiescostsss=cookiescostss.values()
        cookiescostsi=cookiescostaaai
        cookiescosts=json.dumps(cookiescostsi)
        
        cookieskeyscosts=json.dumps(keyscookies)
        
        friesbuttons = user1.objects.filter(Subcategory__Subcategorychoices='Fries',user__id=userr).distinct('productname').exclude(productname='Free Fries')

        
        
        iiiiiiiiiiiiiiii=0
        friespricess={}
        friespricesii = user1.objects.filter(Subcategory__Subcategorychoices='Fries',user__id=userr).values_list('Price',flat=True).order_by('-id')
        
        friesproductnameii=friespricesii.values_list('productname',flat=True)
        
        #friessizeii=friespricesii.values_list('Size__Sizechoices',flat=True)
        
        while iiiiiiiiiiiiiiii<friespricesii.count():
            friespricess[friesproductnameii[iiiiiiiiiiiiiiii]]=friespricesii[iiiiiiiiiiiiiiii]

            iiiiiiiiiiiiiiii += 1
        friespricesss=friespricess
        
        friesprices=json.dumps(friespricesss)
        
        iiiiiiiiiiiiiiiii=0
        friescostss={}
        friescostsii = user1.objects.filter(Subcategory__Subcategorychoices='Fries',user__id=userr).values_list('Cost',flat=True).order_by('-id')
        
        friesproductnameii=friescostsii.values_list('productname',flat=True)
        
        
        
        while iiiiiiiiiiiiiiiii<friescostsii.count():
            friescostss[friesproductnameii[iiiiiiiiiiiiiiiii]]=friescostsii[iiiiiiiiiiiiiiiii]

            iiiiiiiiiiiiiiiii += 1
        counterfries=len(friescostss)
        
        iiiiiiiiiiiiiiiiii=0
        keysfries=[]
        friescostaaai=[]
        for key, friescostaaa in friescostss.items():
            keysfries.append(key)
            friescostaaai.append(float(friescostaaa))
        
        
        friescostsss=friescostss.values()
        friescostsi=friescostaaai
        friescosts=json.dumps(friescostsi)
        
        frieskeyscosts=json.dumps(keysfries)
        
        shawarmabuttons = user1.objects.filter(Subcategory__Subcategorychoices='Shawarma',user__id=userr).distinct('productname')
        
        
        
        iiiiiiiiiiiiiiiiiii=0
        shawarmapricess={}
        shawarmapricesii = user1.objects.filter(Subcategory__Subcategorychoices='Shawarma',user__id=userr).values_list('Price',flat=True).order_by('-id')
        
        shawarmaproductnameii=shawarmapricesii.values_list('productname',flat=True)
        
        #friessizeii=friespricesii.values_list('Size__Sizechoices',flat=True)
        
        while iiiiiiiiiiiiiiiiiii<shawarmapricesii.count():
            shawarmapricess[shawarmaproductnameii[iiiiiiiiiiiiiiiiiii]]=shawarmapricesii[iiiiiiiiiiiiiiiiiii]

            iiiiiiiiiiiiiiiiiii += 1
        shawarmapricesss=shawarmapricess
        
        shawarmaprices=json.dumps(shawarmapricesss)
        
        iiiiiiiiiiiiiiiiiiii=0
        shawarmacostss={}
        shawarmacostsii = user1.objects.filter(Subcategory__Subcategorychoices='Shawarma',user__id=userr).values_list('Cost',flat=True).order_by('-id')
        
        shawarmaproductnameii=shawarmacostsii.values_list('productname',flat=True)
        
        
        
        while iiiiiiiiiiiiiiiiiiii<shawarmacostsii.count():
            shawarmacostss[shawarmaproductnameii[iiiiiiiiiiiiiiiiiiii]]=shawarmacostsii[iiiiiiiiiiiiiiiiiiii]

            iiiiiiiiiiiiiiiiiiii += 1
        countershawarma=len(shawarmacostss)
        
        iiiiiiiiiiiiiiiiiiiii=0
        keysshawarma=[]
        shawarmacostaaai=[]
        for key, shawarmacostaaa in shawarmacostss.items():
            keysshawarma.append(key)
            shawarmacostaaai.append(float(shawarmacostaaa))
        
        
        shawarmacostsss=shawarmacostss.values()
        shawarmacostsi=shawarmacostaaai
        shawarmacosts=json.dumps(shawarmacostsi)
        
        shawarmakeyscosts=json.dumps(keysshawarma)
        
        bubwafbuttons = user1.objects.filter(Subcategory__Subcategorychoices='Bubble Waffle',user__id=userr).distinct('productname')
        
        
        
        iiiiiiiiiiiiiiiiiiiiii=0
        bubwafpricess={}
        bubwafpricesii = user1.objects.filter(Subcategory__Subcategorychoices='Bubble Waffle',user__id=userr).values_list('Price',flat=True).order_by('-id')
        
        bubwafproductnameii=bubwafpricesii.values_list('productname',flat=True)
        
        #friessizeii=friespricesii.values_list('Size__Sizechoices',flat=True)
        
        while iiiiiiiiiiiiiiiiiiiiii<bubwafpricesii.count():
            bubwafpricess[bubwafproductnameii[iiiiiiiiiiiiiiiiiiiiii]]=bubwafpricesii[iiiiiiiiiiiiiiiiiiiiii]

            iiiiiiiiiiiiiiiiiiiiii += 1
        bubwafpricesss=bubwafpricess
        
        bubwafprices=json.dumps(bubwafpricesss)
        
        iiiiiiiiiiiiiiiiiiiiiii=0
        bubwafcostss={}
        bubwafcostsii = user1.objects.filter(Subcategory__Subcategorychoices='Bubble Waffle',user__id=userr).values_list('Cost',flat=True).order_by('-id')
        
        bubwafproductnameii=bubwafcostsii.values_list('productname',flat=True)
        
        
        
        while iiiiiiiiiiiiiiiiiiiiiii<bubwafcostsii.count():
            bubwafcostss[bubwafproductnameii[iiiiiiiiiiiiiiiiiiiiiii]]=bubwafcostsii[iiiiiiiiiiiiiiiiiiiiiii]

            iiiiiiiiiiiiiiiiiiiiiii += 1
        counterbubwaf=len(bubwafcostss)
        
        iiiiiiiiiiiiiiiiiiiiiiii=0
        keysbubwaf=[]
        bubwafcostaaai=[]
        for key, bubwafcostaaa in bubwafcostss.items():
            keysbubwaf.append(key)
            bubwafcostaaai.append(float(bubwafcostaaa))
        
        
        bubwafcostsss=bubwafcostss.values()
        bubwafcostsi=bubwafcostaaai
        bubwafcosts=json.dumps(bubwafcostsi)
        
        bubwafkeyscosts=json.dumps(keysbubwaf)
        
        pizzabuttons = user1.objects.filter(Subcategory__Subcategorychoices='Pizza',user__id=userr).distinct('productname')
        
        
        
        iiiiiiiiiiiiiiiiiiiiiiiii=0
        pizzapricess={}
        pizzapricesii = user1.objects.filter(Subcategory__Subcategorychoices='Pizza',user__id=userr).values_list('Price',flat=True).order_by('-id')
        
        pizzaproductnameii=pizzapricesii.values_list('productname',flat=True)
        
        pizzasizeii=pizzapricesii.values_list('PSize__PSizechoices',flat=True)
        
        while iiiiiiiiiiiiiiiiiiiiiiiii<pizzapricesii.count():
            pizzapricess[pizzaproductnameii[iiiiiiiiiiiiiiiiiiiiiiiii]+pizzasizeii[iiiiiiiiiiiiiiiiiiiiiiiii]]=pizzapricesii[iiiiiiiiiiiiiiiiiiiiiiiii]

            iiiiiiiiiiiiiiiiiiiiiiiii += 1
        pizzapricesss=pizzapricess
        
        pizzaprices=json.dumps(pizzapricesss)
        
        iiiiiiiiiiiiiiiiiiiiiiiiii=0
        pizzacostss={}
        pizzacostsii = user1.objects.filter(Subcategory__Subcategorychoices='Pizza',user__id=userr).values_list('Cost',flat=True).order_by('-id')
        
        pizzaproductnameii=pizzacostsii.values_list('productname',flat=True)
        
        
        
        while iiiiiiiiiiiiiiiiiiiiiiiiii<pizzacostsii.count():
            pizzacostss[pizzaproductnameii[iiiiiiiiiiiiiiiiiiiiiiiiii]+pizzasizeii[iiiiiiiiiiiiiiiiiiiiiiiiii]]=pizzacostsii[iiiiiiiiiiiiiiiiiiiiiiiiii]

            iiiiiiiiiiiiiiiiiiiiiiiiii += 1
        counterpizza=len(pizzacostss)
        
        iiiiiiiiiiiiiiiiiiiiiiiiiii=0
        keyspizza=[]
        pizzacostaaai=[]
        for key, pizzacostaaa in pizzacostss.items():
            keyspizza.append(key)
            pizzacostaaai.append(float(pizzacostaaa))
        
        
        pizzacostsss=pizzacostss.values()
        pizzacostsi=pizzacostaaai
        pizzacosts=json.dumps(pizzacostsi)
        
        pizzakeyscosts=json.dumps(keyspizza)
        
        snbuttons = user1.objects.filter(Category__Categorychoices='Snacks',user__id=userr)
        #punchedla=punchedprod.objects.filter(user=userr)
        qq1=queue1.objects.all().filter(user=userr)
        qq2=queue2.objects.all().filter(user=userr)
        qq3=queue3.objects.all().filter(user=userr)
        mepunched=punched
        if request.POST.get('done1')=='done1':
            objs = [Sales(
                        user=Sales1pass.user,
                        productname=Sales1pass.productname,
                        Category=Sales1pass.Category,
                        Subcategory=Sales1pass.Subcategory,
                        Size=Sales1pass.Size,
                        PSize=Sales1pass.PSize,
                        Price=Sales1pass.Price,
                        Cost=Sales1pass.Cost,
                        Subtotal=Sales1pass.Subtotal,
                        Qty=Sales1pass.Qty,
                        Bill=Sales1pass.Bill,
                        Change=Sales1pass.Change,
                        CusName=Sales1pass.CusName,
                        DateTime=datetime.datetime.now(pytz.timezone('Asia/Singapore')),
                )
                for Sales1pass in qq1
            ]
            disablepay="disabled"
            Sales1create = Sales.objects.bulk_create(objs)
            qq1.delete()
            messages.success(request,"Orders are done, and saved the record of your transaction! ")

            return HttpResponseRedirect('/index/kgddashboard?next=/index/pos')
        elif request.POST.get('done2'):
            objs = [Sales(
                        user=Sales2pass.user,
                        productname=Sales2pass.productname,
                        Category=Sales2pass.Category,
                        Subcategory=Sales2pass.Subcategory,
                        Size=Sales2pass.Size,
                        PSize=Sales2pass.PSize,
                        Price=Sales2pass.Price,
                        Cost=Sales2pass.Cost,
                        Subtotal=Sales2pass.Subtotal,
                        Qty=Sales2pass.Qty,
                        Bill=Sales2pass.Bill,
                        Change=Sales2pass.Change,
                        CusName=Sales2pass.CusName,
                        DateTime=datetime.datetime.now(pytz.timezone('Asia/Singapore')),
                    
                )
                for Sales2pass in qq2
            ]
            disablepay="disabled"
            Sales2create = Sales.objects.bulk_create(objs)
            qq2.delete()
            messages.success(request,"Orders are done, and saved the record of your transaction! ")
            return HttpResponseRedirect('/index/kgddashboard?next=/index/pos')
        elif request.POST.get('done3')=='done3':

            objs = [Sales(
                        user=Sales3pass.user,
                        productname=Sales3pass.productname,
                        Category=Sales3pass.Category,
                        Subcategory=Sales3pass.Subcategory,
                        Size=Sales3pass.Size,
                        PSize=Sales3pass.PSize,
                        Price=Sales3pass.Price,
                        Cost=Sales3pass.Cost,
                        Subtotal=Sales3pass.Subtotal,
                        Qty=Sales3pass.Qty,
                        Bill=Sales3pass.Bill,
                        Change=Sales3pass.Change,
                        CusName=Sales3pass.CusName,
                        DateTime=datetime.datetime.now(pytz.timezone('Asia/Singapore')),
                )
                for Sales3pass in qq3
            ]
            disablepay="disabled"
            Sales3create = Sales.objects.bulk_create(objs)
            qq3.delete()
            messages.success(request,"Orders are done, and saved the record of your transaction! ")
            return HttpResponseRedirect('/index/kgddashboard?next=/index/pos')
        if request.POST.get('cancel1')=='cancel1':
            qq1.delete()
            return HttpResponseRedirect('/index/pos')
        elif request.POST.get('cancel2')=='cancel2':
            qq2.delete()
            return HttpResponseRedirect('/index/pos')
        elif request.POST.get('cancel3')=='cancel3':
            qq3.delete()
            return HttpResponseRedirect('/index/pos')
        if request.GET.get('Q1')=="Queue1":
            cuspaymentamount=int(request.GET.get('amountpay'))
            tot1=int(request.GET.get('total1'))
            changei=cuspaymentamount-tot1
            arraypunchedi=json.loads(request.GET.get('arrayname'))
            arraypunched=arraypunchedi
            for obj in arraypunched:
                object2=obj['productname']
            arraypunchedcounter=len(arraypunchedi)
            objs = [queue1(
                        user=userr,
                        productname=obj['productname'],
                        Category=obj['Category'],
                        Subcategory=obj['Subcategory'],
                        Size=obj['Size'],
                        Price=obj['Price'],
                        PSize=obj['PSize'],
                        Subtotal=obj['Subtotal'],
                        Qty=obj['Qty'],
                        Cost=obj['Cost'],
                        Bill=cuspaymentamount,
                        Change=changei,
                        CusName=request.GET.get('Cusname1'),
                        DateTime=datetime.datetime.now(pytz.timezone('Asia/Singapore')),

                )
                for obj in arraypunched
            ]
            Sales1create = queue1.objects.bulk_create(objs)
            q1=queue1.objects.all().filter(user=userr)
            q11=queue1.objects.all().filter(user=userr).values_list('CusName','Bill','Change').distinct()
            q111=queue1.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
            
            return HttpResponseRedirect('/index/pos')
        elif request.GET.get('Q2')=="Queue2": 
            cuspaymentamount2=int(request.GET.get('amountpay2'))
            tot2=int(request.GET.get('total2'))
            changei2=cuspaymentamount2-tot2
            arraypunchedi2=json.loads(request.GET.get('arrayname2'))
            arraypunched2=arraypunchedi2
            for obj2 in arraypunched2:
                object2=obj2['productname']
            
            arraypunchedcounter2=len(arraypunchedi2)
            objs2 = [queue2(
                        user=userr,
                        productname=obj2['productname'],
                        Category=obj2['Category'],
                        Subcategory=obj2['Subcategory'],
                        Size=obj2['Size'],
                        Price=obj2['Price'],
                        PSize=obj2['PSize'],
                        Subtotal=obj2['Subtotal'],
                        Qty=obj2['Qty'],
                        Cost=obj2['Cost'],
                        Bill=cuspaymentamount2,
                        Change=changei2,
                        CusName=request.GET.get('Cusname2'),
                        DateTime=datetime.datetime.now(pytz.timezone('Asia/Singapore')),

                )
                for obj2 in arraypunched2
            ]
            Sales2create = queue2.objects.bulk_create(objs2)
            q2=queue2.objects.all().filter(user=userr)
            q22=queue2.objects.all().filter(user=userr).values_list('CusName','Bill','Change').distinct()
            q222=queue2.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
            
            return HttpResponseRedirect('/index/pos')
        elif request.GET.get('Q3') =="Queue3": 
            cuspaymentamount3=int(request.GET.get('amountpay3'))
            tot3=int(request.GET.get('total3'))
            changei3=cuspaymentamount3-tot3
            arraypunchedi3=json.loads(request.GET.get('arrayname3'))
            arraypunched3=arraypunchedi3
            for obj3 in arraypunched3:
                object3=obj3['productname']
            arraypunchedcounter3=len(arraypunchedi3)
            objs3 = [queue3(
                        user=userr,
                        productname=obj3['productname'],
                        Category=obj3['Category'],
                        Subcategory=obj3['Subcategory'],
                        Size=obj3['Size'],
                        Price=obj3['Price'],
                        PSize=obj3['PSize'],
                        Subtotal=obj3['Subtotal'],
                        Qty=obj3['Qty'],
                        Cost=obj3['Cost'],
                        Bill=cuspaymentamount3,
                        Change=changei3,
                        CusName=request.GET.get('Cusname3'),
                        DateTime=datetime.datetime.now(pytz.timezone('Asia/Singapore')),

                )
                for obj3 in arraypunched3
            ]
            Sales3create = queue3.objects.bulk_create(objs3)
            q3=queue3.objects.all().filter(user=userr)
            q33=queue3.objects.all().filter(user=userr).values_list('CusName','Bill','Change').distinct()
            q333=queue3.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
            
            return HttpResponseRedirect('/index/pos')
        else:
            disable="disabled"
            q1=queue1.objects.all().filter(user=userr)
            q11=queue1.objects.all().filter(user=userr).values_list('CusName','Bill','Change').distinct()
            q111=queue1.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
            q2=queue2.objects.all().filter(user=userr)
            q22=queue2.objects.all().filter(user=userr).values_list('CusName','Bill','Change').distinct()
            q222=queue2.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
            q3=queue3.objects.all().filter(user=userr)
            q33=queue3.objects.all().filter(user=userr).values_list('CusName','Bill','Change').distinct()
            q333=queue3.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
            if len(Acceptorder.objects.filter(Admin=userr, productname='Ready'))>0:
                initial=Acceptorder.objects.filter(Admin=userr, productname='Ready').values_list('contactnumber', flat=True)
                readylistcontact=list(initial)
            else:
                readylistcontact=list(Acceptorder.objects.none())
            print('readylistcontact1:',readylistcontact)
            return render(request, 'posthree.html',{'readylistcontact':readylistcontact, 'onlineordercounter':onlineordercounter,'viewordersreject':viewordersreject,'rejectedorder':rejectedorder,'viewordersaccept':viewordersaccept,'acceptedorder':acceptedorder,'onlineorder':onlineorder,'mepunched':mepunched,'pizzakeyscosts':pizzakeyscosts,'pizzacosts':pizzacosts,'pizzaprices':pizzaprices,'bubwafkeyscosts':bubwafkeyscosts,'bubwafcosts':bubwafcosts,'bubwafprices':bubwafprices,'shawarmakeyscosts':shawarmakeyscosts,'shawarmacosts':shawarmacosts,'shawarmaprices':shawarmaprices,'frieskeyscosts':frieskeyscosts,'friescosts':friescosts,'friesprices':friesprices,'cookieskeyscosts':cookieskeyscosts,'cookiescosts':cookiescosts,'cookiesprices':cookiesprices,'aokeyscosts':aokeyscosts,'aocosts':aocosts,'aoprices':aoprices,'frkeyscosts':frkeyscosts,'frzkeyscosts':frzkeyscosts,'frzcosts':frzcosts,'frzprices':frzprices,'frcosts':frcosts,'frprices':frprices,'mtkeyscosts':mtkeyscosts,'mtcosts':mtcosts,'mtprices':mtprices,'notifyadmin':notifyadmin,'notifyorder':notifyorder,'punchedtotal':punchedtotal,'userr':userr,'disable':disable,'psizes':psizes,'q1':q1,'q11':q11,'q111':q111,'q2':q2,'q22':q22,'q222':q222,'q3':q3,'q33':q33,'q333':q333,'pizzabuttons':pizzabuttons,'bubwafbuttons':bubwafbuttons,'shawarmabuttons':shawarmabuttons,'friesbuttons':friesbuttons,'cookiesbuttons':cookiesbuttons,'addonsbuttons':addonsbuttons,'freezebuttons':freezebuttons,'Subcategoriess':Subcategoriess,'mtbuttons':mtbuttons,'frbuttons':frbuttons,'snbuttons':snbuttons,'psizes':psizes,'frsizes':frsizes,'mtsizes':mtsizes,'Categoriess':Categoriess})


@login_required
def stockorderad(request):
    userr=request.user.id

    if submitstockorder.objects.all().count()==0:
            punchedtotal=0
    else:
            punchedtotal=submitstockorder.objects.all().aggregate(Sum('Subtotal')).get('Subtotal__sum')
    detailstoreceive=submitstockorder.objects.filter(productname=None).first()
    toreceive=submitstockorder.objects.all().exclude(productname=None).exclude(productname="")
    if request.POST.get('aknowledgebutton'): 
        subb=submitstockorder.objects.all()
        if acknowledgedstockorder.objects.filter(user=submitstockorder.objects.all().values_list('user',flat=True).first()):
            pass
            print('existing na')
        else:
            objs = [acknowledgedstockorder(
                    user=sub.user,
                    productname=sub.productname,
                    Category=sub.Category,
                    Price =sub.Price,
                    Subtotal =sub.Subtotal,
                    Cost =sub.Cost,
                    Qty=sub.Qty,
                    CusName=sub.CusName,
                    DeliveryAddress=sub.DeliveryAddress,
                    ShippingFee=sub.ShippingFee,
                    contactnumber=sub.contactnumber,
                )
                for sub in subb
                ]
            acknowledgeorderi = acknowledgedstockorder.objects.bulk_create(objs)
        acknowledgeorder=acknowledgedstockorder.objects.all().exclude(productname="").exclude(CusName="Shipped").exclude(CusName="Notify").exclude(productname=None)
        detailacknowledge=acknowledgedstockorder.objects.filter(productname="").exclude(CusName="Shipped").exclude(CusName="Notify")
        
        if acknowledgeorder.count()==0:
            disable=""
        else:
            disable="disabled"
        
        
    else:
        ak=acknowledgedstockorder.objects.all()
        
        if ak.count()==0:
            acknowledgeorder=acknowledgedstockorder.objects.none()
            detailacknowledge=acknowledgedstockorder.objects.none()
            disable=""
        else:
            acknowledgeorder=acknowledgedstockorder.objects.all().exclude(productname="").exclude(CusName="Shipped").exclude(CusName="Notify").exclude(productname=None)
            detailacknowledge=acknowledgedstockorder.objects.filter(productname="").exclude(CusName="Shipped").exclude(CusName="Notify")
            disable="disabled"
        
        
    if request.POST.get('ship'):
        subb=submitstockorder.objects.all().first()

        objs = [acknowledgedstockorder(
                user=subb.user,
                CusName="Shipped",
            )
            ]
        ship = acknowledgedstockorder.objects.bulk_create(objs)
        
        shiporder=acknowledgedstockorder.objects.filter(CusName="Shipped").count()
        
    else:
        shiporder=acknowledgedstockorder.objects.filter(CusName="Shipped").count()
    if acknowledgedstockorder.objects.all().count()==0:
            acknowledge=0
    else:
            acknowledge=acknowledgedstockorder.objects.all().aggregate(Sum('Subtotal')).get('Subtotal__sum')
    if request.POST.get('Notify'):
        subb=submitstockorder.objects.all().first()
        objs = [acknowledgedstockorder(
                user=subb.user,
                CusName="Notify",
            )
            ]
        notify = acknowledgedstockorder.objects.bulk_create(objs)
        notifyorder=acknowledgedstockorder.objects.filter(CusName="Notify").count()
        
    else:
        notifyorder=acknowledgedstockorder.objects.filter(CusName="Notify").count()
    if acknowledgedstockorder.objects.all().count()==0:
        notifyadmin=submitstockorder.objects.all().count()
    else:
        notifyadmin=0
    return render(request, 'stockorderadmin.html',{'notifyadmin':notifyadmin,'notifyorder':notifyorder,'acknowledge':acknowledge,'shiporder':shiporder,'disable':disable,'detailacknowledge':detailacknowledge,'acknowledgeorder':acknowledgeorder,'userr':userr,'punchedtotal':punchedtotal,'detailstoreceive':detailstoreceive,'toreceive':toreceive,})


@login_required
def StocksOrder(request):
    userr=request.user.id
    
    cancel=request.POST.get('cancelbutton')

    if request.POST.get('received'): 
        subbiiiiii=acknowledgedstockorder.objects.all().exclude(CusName="Notify").exclude(CusName="Shipped")
        datetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
        monthtoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m')
        yeartoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y')
        if Sales.objects.filter(CusName=acknowledgedstockorder.objects.all().values_list('CusName',flat=True).first(), DateTime__day=datetoday, DateTime__month=monthtoday, DateTime__year = yeartoday):
            pass
        else:
            objs = [Sales(
                    user=1,
                    productname=sub.productname,
                    Category=sub.Category,
                    Price =sub.Price,
                    Subtotal =sub.Subtotal,
                    Cost =sub.Cost,
                    Qty=sub.Qty,
                    CusName=sub.CusName,
                )
                for sub in subbiiiiii
                ]
            submitorderii = Sales.objects.bulk_create(objs)
            deleteacknowledge=acknowledgedstockorder.objects.all()
            deleteacknowledge.delete()
            deletesubmit=submitstockorder.objects.all()
            deletesubmit.delete()
    notifyorder=acknowledgedstockorder.objects.filter(CusName="Notify",user=userr).count()
    if acknowledgedstockorder.objects.all().count()==0:
        notifyadmin=submitstockorder.objects.all().count()
    else:
        notifyadmin=0
    if punchedprodso.objects.filter(user=userr).count()==0:
            punchedtotal=0
    else:
            punchedtotal=punchedprodso.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
    stockbutton = user1.objects.filter(Category__Categorychoices='Stock',user__id="4").distinct('productname')
    punchedlaso=punchedprodso.objects.filter(user=userr)
    submitorder=stockorderform 
    acknowledgeorder=acknowledgedstockorder.objects.all().exclude(productname="").exclude(CusName="Shipped").exclude(CusName="Notify").exclude(productname=None)
    detailacknowledge=acknowledgedstockorder.objects.filter(productname="").exclude(CusName="Shipped").exclude(CusName="Notify")
   
    if acknowledgeorder.count()==0:
        if submitstockorder.objects.filter(user=userr).count()!=0:
            disablecancel=""
        else:
            disablecancel="disabled"
    else:
        disablecancel="disabled"
    if request.POST.get('cancelbutton'):    
        cancel=submitstockorder.objects.all().filter(user=userr)
        
        cancel.delete()
        punchedtotal=0
        submitorder=stockorderform 
        mepunched=punchedso
        disable="disabled"
        toreceive=submitstockorder.objects.filter(user=userr).exclude(productname="")
        toreceivetotal=toreceive.aggregate(Sum('Subtotal')).get('Subtotal__sum')
        counttoreceive=submitstockorder.objects.all().count()
        if counttoreceive==0:
            disablesubmit=""
        else:
            disablesubmit="disabled"
        return render(request, 'StockOrder.html',{'notifyadmin':notifyadmin,'notifyadmin':notifyadmin,'notifyorder':notifyorder,'disablecancel':disablecancel,'cancel':cancel,'disablesubmit':disablesubmit,'toreceivetotal':toreceivetotal,'toreceive':toreceive,'submitorder':submitorder,'punchedlaso':punchedlaso,'punchedtotal':punchedtotal,'userr':userr,'disable':disable,'stockbutton':stockbutton,'mepunched':mepunched})
    if request.GET.get('stock'):
            if request.GET.get('qty')!="":
                qty=int(request.GET.get('qty'))   
                disable=""
                stor=request.GET.get('stock')
                stock=request.GET.get('Stock')
                
                try:
                    presyoSTO=user1.objects.filter(Category__Categorychoices=stock,productname=stor,user__id=4).values('Price').get()
                    costSTO=user1.objects.filter(Category__Categorychoices=stock,productname=stor,user__id=4).values('Cost').get()
                    counttoreceive=submitstockorder.objects.all().count()
                    if counttoreceive == 0:
                        disablesubmit=""
                    else:
                        disablesubmit="disabled"
                except user1.DoesNotExist:
                    messages.success(request,"The chosen Size of the product does not exist, please add size product first! ❌")
                    disable="disabled"
                    return render(request, 'StockOrder.html',{'notifyadmin':notifyadmin,'notifyorder':notifyorder,'disablesubmit':disablesubmit,'submitorder':submitorder,'punchedtotal':punchedtotal,'punchedlaso':punchedlaso,'userr':userr,'disable':disable})
                except user1.MultipleObjectsReturned:
                    messages.success(request,"You registered similar product with same or conflict details, please remove the other! ❌")
                    return render(request, 'StockOrder.html',{'notifyadmin':notifyadmin,'notifyorder':notifyorder,'disablesubmit':disablesubmit,'submitorder':submitorder,'punchedtotal':punchedtotal,'punchedlaso':punchedlaso,'userr':userr,'disable':disable})
                for Price, priceSTO in presyoSTO.items():
                    presyoSTO['Price']=int(priceSTO)
                    subtotsto = presyoSTO['Price']* qty
                if request.POST.get('suspendbutton'):
                    delmepunched=punchedprodso.objects.all().filter(user=userr)
                    delmepunched.delete()
                    punchedtotal=0
                    submitorder=stockorderform 
                    qty=""
                    stor=""
                    stock=""
                    presyoSTO=""
                    costSTO=""
                    subtotsto=""
                    toreceive=submitstockorder.objects.filter(user=userr).exclude(productname="")
                    toreceivetotal=toreceive.aggregate(Sum('Subtotal')).get('Subtotal__sum')
                    counttoreceive=submitstockorder.objects.all().count()
                    if counttoreceive==0:
                        disablesubmit=""
                    else:
                        disablesubmit="disabled"
                    return render(request, 'StockOrder.html',{'notifyadmin':notifyadmin,'notifyorder':notifyorder,'disablecancel':disablecancel,'disablesubmit':disablesubmit,'toreceivetotal':toreceivetotal,'toreceive':toreceive,'submitorder':submitorder,'punchedtotal':punchedtotal,'punchedlaso':punchedlaso,'userr':userr,'stockbutton':stockbutton,'stor':stor,'qty':qty,'stock':stock,'presyoSTO':presyoSTO,'costSTO':costSTO,'subtotsto':subtotsto,'delmepunched':delmepunched})
                elif request.POST.get('addbutton'):
                    mepunched=punchedso(request.POST)
                    mepunched.save()
                    submitorder=stockorderform 
                    toreceive=submitstockorder.objects.filter(user=userr).exclude(productname="")
                    toreceivetotal=toreceive.aggregate(Sum('Subtotal')).get('Subtotal__sum')
                    punchedtotal=punchedprodso.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
                    counttoreceive=submitstockorder.objects.all().count()
                    if counttoreceive==0:
                        disablesubmit=""
                    else:
                        disablesubmit="disabled"
                    return render(request, 'StockOrder.html',{'notifyadmin':notifyadmin,'notifyorder':notifyorder,'disablecancel':disablecancel,'disablesubmit':disablesubmit,'toreceivetotal':toreceivetotal,'toreceive':toreceive,'submitorder':submitorder,'punchedlaso':punchedlaso,'punchedtotal':punchedtotal,'userr':userr,'disable':disable,'stockbutton':stockbutton,'stor':stor,'qty':qty,'stock':stock,'presyoSTO':presyoSTO,'costSTO':costSTO,'subtotsto':subtotsto,'mepunched':mepunched})
                elif request.POST.get('submitorderbutton'):
                    submitorder=stockorderform(request.POST)
                    submitorder.save()
                    subb=punchedprodso.objects.filter(user=userr)
                    objs = [submitstockorder(
                            user=userr,
                            productname=sub.productname,
                            Category=sub.Category,
                            Price =sub.Price,
                            Subtotal =sub.Subtotal,
                            Cost =sub.Cost,
                            Qty=sub.Qty,
                        )
                        for sub in subb
                        ]
                    submitorderii = submitstockorder.objects.bulk_create(objs)

                    subb.delete()
                    punchedtotal=0
                    toreceive=submitstockorder.objects.filter(user=userr).exclude(productname="")
                    toreceivetotal=toreceive.aggregate(Sum('Subtotal')).get('Subtotal__sum')
                    mepunched=punchedso
                    qty=""
                    stor=""
                    stock=""
                    presyoSTO=""
                    costSTO=""
                    subtotsto=""
                    counttoreceive=submitstockorder.objects.all().count()
                    if counttoreceive==0:
                        disablesubmit=""
                    else:
                        disablesubmit="disabled"
                    return render(request, 'StockOrder.html',{'notifyadmin':notifyadmin,'notifyorder':notifyorder,'disablecancel':disablecancel,'disablesubmit':disablesubmit,'toreceivetotal':toreceivetotal,'toreceive':toreceive,'submitorder':submitorder,'punchedlaso':punchedlaso,'punchedtotal':punchedtotal,'userr':userr,'disable':disable,'stockbutton':stockbutton,'stor':stor,'qty':qty,'stock':stock,'presyoSTO':presyoSTO,'costSTO':costSTO,'subtotsto':subtotsto,'mepunched':mepunched})

                else:
                    submitorder=stockorderform 
                    mepunched=punchedso
                    toreceive=submitstockorder.objects.filter(user=userr).exclude(productname="")
                    toreceivetotal=toreceive.aggregate(Sum('Subtotal')).get('Subtotal__sum')
                    counttoreceive=submitstockorder.objects.all().count()
                    if counttoreceive==0:
                        disablesubmit=""
                    else:
                        disablesubmit="disabled"
                    return render(request, 'StockOrder.html',{'notifyadmin':notifyadmin,'notifyorder':notifyorder,'disablecancel':disablecancel,'disablesubmit':disablesubmit,'toreceivetotal':toreceivetotal,'toreceive':toreceive,'submitorder':submitorder,'punchedtotal':punchedtotal,'punchedlaso':punchedlaso,'userr':userr,'disable':disable,'stockbutton':stockbutton,'stor':stor,'qty':qty,'stock':stock,'presyoSTO':presyoSTO,'costSTO':costSTO,'subtotsto':subtotsto,'mepunched':mepunched})
            else:
                qty=""
                disable="disabled"
                toreceive=submitstockorder.objects.filter(user=userr).exclude(productname="")
                toreceivetotal=toreceive.aggregate(Sum('Subtotal')).get('Subtotal__sum')
                counttoreceive=submitstockorder.objects.all().count()
                if counttoreceive==0:
                    disablesubmit=""
                else:
                    disablesubmit="disabled"
                return render(request, 'StockOrder.html',{'notifyadmin':notifyadmin,'notifyorder':notifyorder,'disablecancel':disablecancel,'disablesubmit':disablesubmit,'toreceivetotal':toreceivetotal,'toreceive':toreceive,'submitorder':submitorder,'punchedtotal':punchedtotal,'punchedlaso':punchedlaso,'userr':userr,'stockbutton':stockbutton,'qty':qty})
    else:
        qty=""
        disable="disabled"
        toreceive=submitstockorder.objects.filter(user=userr).exclude(productname="")
        toreceivetotal=toreceive.aggregate(Sum('Subtotal')).get('Subtotal__sum')
        counttoreceive=submitstockorder.objects.all().count()
        if counttoreceive==0:
            disablesubmit=""
        else:
            disablesubmit="disabled"
        return render(request, 'StockOrder.html',{'notifyadmin':notifyadmin,'notifyorder':notifyorder,'disablecancel':disablecancel,'userr':userr,'disablesubmit':disablesubmit,'toreceivetotal':toreceivetotal,'toreceive':toreceive,'submitorder':submitorder,'stockbutton':stockbutton,'qty':qty})

@login_required
def StocksandExp(request):
        userr=request.user.id
        if request.GET.get('acceptcontactno'):
            contactnumberaccept = request.GET.get('acceptcontactno')
            rider = request.GET.get('rider')
            getETA = request.GET.get('ETA')
            Accepted = Customer.objects.filter(Admin=userr,contactnumber=contactnumberaccept)
            
            objs = [Acceptorder(
                        Admin=Accepted.Admin,
                        Customername=Accepted.Customername,
                        codecoupon=Accepted.codecoupon,
                        discount=Accepted.discount or None,
                        Province=Accepted.Province,
                        MunicipalityCity=Accepted.MunicipalityCity,
                        Barangay=Accepted.Barangay,
                        StreetPurok=Accepted.StreetPurok,
                        Housenumber=Accepted.Housenumber or None,
                        LandmarksnNotes=Accepted.LandmarksnNotes or None,
                        DeliveryFee=Accepted.DeliveryFee or 0,
                        contactnumber=Accepted.contactnumber,
                        Rider=rider,
                        productname=Accepted.productname,
                        Category=Accepted.Category,
                        Subcategory=Accepted.Subcategory or None,
                        Size=Accepted.Size  or None,
                        PSize=Accepted.PSize or None,
                        Addons=Accepted.Addons or None,
                        QtyAddons= Accepted.QtyAddons or 0,
                        Price=Accepted.Price,
                        Subtotal = Accepted.Subtotal,
                        GSubtotal=Accepted.GSubtotal,
                        Cost=Accepted.Cost,
                        Qty=Accepted.Qty,
                        Bill=Accepted.Bill or 0,
                        Change=Accepted.Change or 0,
                        ETA=getETA,
                        MOP=Accepted.MOP,
                        ordertype='Online',
                        Timetodeliver=Accepted.Timetodeliver,
                        ScheduleTime=Accepted.ScheduleTime,
                        gpslat = Accepted.gpslat,
                        gpslng = Accepted.gpslng,
                        gpsaccuracy = Accepted.gpsaccuracy,
                        pinnedlat = Accepted.pinnedlat,
                        pinnedlng = Accepted.pinnedlng,
                            
                        tokens = Accepted.tokens or None,
                        DateTime=Accepted.DateTime,
                )
                for Accepted in Accepted
            ]
            Acceptorders = Acceptorder.objects.bulk_create(objs)
            Accepted.delete()
            messageacknowledgetokeni=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberaccept).values_list('tokens',flat=True).first()
            messageacknowledgetoken = ["dHEGNR4YGO8a-AVQWfIE33:APA91bGkNxUcRZEHJQCkUy3k3THUEMxml9q4819bDQw1b8UkD05qThidgXq3Nnr46I1pwQikZgwiGFuBgKwUxHO6kUXI9KId3ZK0fQ0zi83QegTtVimqV18a2pDqBq5qnJf-BK74Z1nL", messageacknowledgetokeni]
            acknowledge(request, messageacknowledgetoken)
            MessageRider(request)
            return HttpResponseRedirect('/index/pos')

        if len(Acceptorder.objects.filter(Admin=userr))>0:
            acceptedorder = Acceptorder.objects.filter(Admin=userr).distinct('contactnumber')
            acceptedorderall = Acceptorder.objects.filter(Admin=userr)
        else:
            acceptedorder = Acceptorder.objects.none()
            acceptedorderall = Acceptorder.objects.none()
        viewordersacceptii={}
        arrayoneaccept=[]
        contactdistincteraccepti = Acceptorder.objects.filter(Admin=userr).distinct('contactnumber')
        contactdistincteraccept=contactdistincteraccepti.values_list('contactnumber',flat=True)
        i=0
        for cndistinctaccept in contactdistincteraccept:
            arrayseparatoracceptiii=Acceptorder.objects.filter(Admin=userr,contactnumber=cndistinctaccept).exclude(productname='Ready').values()
            arrayseparatoraccepti = list(arrayseparatoracceptiii)
            arrayseparatoraccept=json.dumps(arrayseparatoraccepti, cls=JSONEncoder)
            viewordersacceptii[contactdistincteraccept[i]]=arrayseparatoraccept
            i=i+1
        viewordersaccepti=viewordersacceptii
        viewordersaccept=json.dumps(viewordersaccepti, cls=JSONEncoder)
        

        if (request.GET.get('rider') == "") and (request.GET.get('contactnoreject') or request.GET.get('contactnoaccepted')):
            if request.GET.get('contactnoreject'):
                contactnumberreject = request.GET.get('contactnoreject')
                Rejected = Customer.objects.filter(Admin=userr,contactnumber=contactnumberreject)
            elif request.GET.get('contactnoaccepted'):
                contactnumberreject = request.GET.get('contactnoaccepted')
                if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject, productname='Ready'):
                    deletethis=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject, productname='Ready')
                    deletethis.delete()
                Rejected = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject)
            
            objs = [Rejectorder(
                        Admin=userr,
                        Customername=Rejected.Customername,
                        codecoupon=Rejected.codecoupon,
                        discount=Rejected.discount or None,
                        Province=Rejected.Province,
                        MunicipalityCity=Rejected.MunicipalityCity,
                        Barangay=Rejected.Barangay,
                        StreetPurok=Rejected.StreetPurok,
                        Housenumber=Rejected.Housenumber or None,
                        LandmarksnNotes=Rejected.LandmarksnNotes or None,
                        DeliveryFee=Rejected.DeliveryFee or 0,
                        contactnumber=Rejected.contactnumber,
                        productname=Rejected.productname,
                        Category=Rejected.Category,
                        Subcategory=Rejected.Subcategory or None,
                        Size=Rejected.Size  or None,
                        PSize=Rejected.PSize or None,
                        Addons=Rejected.Addons or None,
                        QtyAddons= Rejected.QtyAddons or 0,
                        Price=Rejected.Price,
                        Subtotal = Rejected.Subtotal,
                        GSubtotal=Rejected.GSubtotal,
                        Cost=Rejected.Cost,
                        Qty=Rejected.Qty,
                        Bill=Rejected.Bill or 0,
                        Change=Rejected.Change or 0,
                        MOP=Rejected.MOP,
                        ordertype='Online',
                        Timetodeliver=Rejected.Timetodeliver,
                        ScheduleTime=Rejected.ScheduleTime,
                        gpslat = Rejected.gpslat,
                        gpslng = Rejected.gpslng,
                        gpsaccuracy = Rejected.gpsaccuracy,
                        pinnedlat = Rejected.pinnedlat,
                        pinnedlng = Rejected.pinnedlng,
                            
                        tokens = Rejected.tokens  or None,
                        DateTime=Rejected.DateTime,
                )
                for Rejected in Rejected
            ]
            Rejectorders = Rejectorder.objects.bulk_create(objs)
            Rejected.delete()
            return HttpResponseRedirect('/index/pos')

        if len(Rejectorder.objects.filter(Admin=userr))>0:
            rejectedorder = Rejectorder.objects.filter(Admin=userr).distinct('contactnumber')
            rejectedorderall = Rejectorder.objects.filter(Admin=userr)
        else:
            rejectedorder = Rejectorder.objects.none()
            rejectedorderall = Rejectorder.objects.none()
        viewordersrejectii={}
        arrayonereject=[]
        contactdistincterrejecti = Rejectorder.objects.filter(Admin=userr).distinct('contactnumber')
        contactdistincterreject=contactdistincterrejecti.values_list('contactnumber',flat=True)
        i=0
        for cndistinctreject in contactdistincterreject:
            arrayseparatorrejectiii=Rejectorder.objects.filter(Admin=userr,contactnumber=cndistinctreject).exclude(productname='Ready').values()
            arrayseparatorrejecti = list(arrayseparatorrejectiii)
            arrayseparatorreject=json.dumps(arrayseparatorrejecti, cls=JSONEncoder)
            viewordersrejectii[contactdistincterreject[i]]=arrayseparatorreject
            i=i+1
        viewordersrejecti=viewordersrejectii
        viewordersreject=json.dumps(viewordersrejecti, cls=JSONEncoder)

        

        if request.GET.get('contactnorestore'):
            contactnumberrestore = request.GET.get('contactnorestore')
            Restored = Rejectorder.objects.filter(Admin=userr,contactnumber=contactnumberrestore)
            
            objs = [Customer(
                        Admin=userr,
                        Customername=Restored.Customername,
                        codecoupon=Restored.codecoupon,
                        discount=Restored.discount or None,
                        Province=Restored.Province,
                        MunicipalityCity=Restored.MunicipalityCity,
                        Barangay=Restored.Barangay,
                        StreetPurok=Restored.StreetPurok,
                        Housenumber=Restored.Housenumber or None,
                        LandmarksnNotes=Restored.LandmarksnNotes or None,
                        DeliveryFee=Restored.DeliveryFee or 0,
                        contactnumber=Restored.contactnumber,
                        productname=Restored.productname,
                        Category=Restored.Category,
                        Subcategory=Restored.Subcategory or None,
                        Size=Restored.Size  or None,
                        PSize=Restored.PSize or None,
                        Addons=Restored.Addons or None,
                        QtyAddons= Restored.QtyAddons or 0,
                        Price=Restored.Price,
                        Subtotal = Restored.Subtotal,
                        GSubtotal=Restored.GSubtotal,
                        Cost=Restored.Cost,
                        Qty=Restored.Qty,
                        Bill=Restored.Bill or 0,
                        Change=Restored.Change or 0,
                        MOP=Restored.MOP,
                        ordertype='Online',
                        Timetodeliver=Restored.Timetodeliver,
                        ScheduleTime=Restored.ScheduleTime,
                        gpslat = Restored.gpslat,
                        gpslng = Restored.gpslng,
                        gpsaccuracy = Restored.gpsaccuracy,
                        pinnedlat = Restored.pinnedlat,
                        pinnedlng = Restored.pinnedlng,
                          
                        tokens = Restored.tokens  or None,
                        DateTime=Restored.DateTime,
                )
                for Restored in Restored
            ]
            Restore = Customer.objects.bulk_create(objs)
            Restored.delete()
            return HttpResponseRedirect('/index/pos')

        if len(Customer.objects.filter(Admin=userr))>0:
            onlineorder = Customer.objects.filter(Admin=userr).distinct('contactnumber')
            onlineorderall = Customer.objects.filter(Admin=userr)
        else:
            onlineorder = Customer.objects.none()
            onlineorderall = Customer.objects.none()
        viewordersii={}
        arrayone=[]
        contactdistincteri = Customer.objects.filter(Admin=userr).distinct('contactnumber')
        contactdistincter=contactdistincteri.values_list('contactnumber',flat=True)
        i=0
        for cndistinct in contactdistincter:  
            arrayseparatoriii=Customer.objects.filter(Admin=userr,contactnumber=cndistinct).values()
            arrayseparatori = list(arrayseparatoriii)
            arrayseparator=json.dumps(arrayseparatori, cls=JSONEncoder)
            viewordersii[contactdistincter[i]]=arrayseparator
            i=i+1
        viewordersi=viewordersii
        vieworders=json.dumps(viewordersi, cls=JSONEncoder)

        onlineordercounter = len(Customer.objects.filter(Admin=userr).distinct('contactnumber'))

        if is_ajax(request=request) and request.POST.get("Ready"):
            contactnumberready = request.POST.get('Ready')
            Readyadd = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).first()
            Readyacceptorder=Acceptorder.objects.create(
                        Admin=userr,
                        Customername=Readyadd.Customername,
                        codecoupon=Readyadd.codecoupon,
                        discount=Readyadd.discount or None,
                        Province=Readyadd.Province,
                        MunicipalityCity=Readyadd.MunicipalityCity,
                        Barangay=Readyadd.Barangay,
                        StreetPurok=Readyadd.StreetPurok,
                        Housenumber=Readyadd.Housenumber or None,
                        LandmarksnNotes=Readyadd.LandmarksnNotes or None,
                        DeliveryFee=0,
                        contactnumber=Readyadd.contactnumber,
                        productname='Ready',
                        Category=Readyadd.Category,
                        Subcategory=None,
                        Size=None,
                        PSize=None,
                        Addons=None,
                        QtyAddons= 0,
                        Price=0,
                        Subtotal = 0,
                        GSubtotal=Readyadd.GSubtotal,
                        Cost=0,
                        Qty=0,
                        Bill=Readyadd.Bill or 0,
                        Change=Readyadd.Change or 0,
                        MOP=Readyadd.MOP,
                        ordertype='Online',
                        Timetodeliver=Readyadd.Timetodeliver,
                        ScheduleTime=Readyadd.ScheduleTime,
                        gpslat = Readyadd.gpslat,
                        gpslng = Readyadd.gpslng,
                        gpsaccuracy = Readyadd.gpsaccuracy,
                        pinnedlat = Readyadd.pinnedlat,
                        pinnedlng = Readyadd.pinnedlng,
                            
                        tokens = Readyadd.tokens  or None,
                        DateTime=Readyadd.DateTime,
                        )
            Readyacceptorder.save()
            if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready, MOP='COD'):
                orderprepared(request)
            messageacknowledgetokeni=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('tokens',flat=True).first()
            messageacknowledgetoken = ["dHEGNR4YGO8a-AVQWfIE33:APA91bGkNxUcRZEHJQCkUy3k3THUEMxml9q4819bDQw1b8UkD05qThidgXq3Nnr46I1pwQikZgwiGFuBgKwUxHO6kUXI9KId3ZK0fQ0zi83QegTtVimqV18a2pDqBq5qnJf-BK74Z1nL", messageacknowledgetokeni]
            if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('MOP',flat=True).first() == 'COD' or Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('MOP',flat=True).first() == 'GcashDelivery':
                deliveryotwRider(request)
                deliveryotwCustomer(request , messageacknowledgetoken)
            else:
                pickupCustomer(request , messageacknowledgetoken)
            return JsonResponse({'Ready':'Ready'})
        if is_ajax(request=request) and request.GET.get("apini"):
            onlineordercounterf = onlineordercounter
            onlineorderf = [serializers.serialize('json',onlineorder, cls=JSONEncoder),vieworders]
            return JsonResponse({'onlineorderf':onlineorderf})
            
        if is_ajax(request=request) and request.POST.get('doneorders'):
            contactnumberdonei = json.loads(request.POST.get('doneorders'))
            contactnumberdone = contactnumberdonei[0]['contactnumber']
            if contactnumberdonei[0]['codecoupon']:
                if couponlist.objects.filter(code=contactnumberdonei[0]['codecoupon']):
                    codeconsumereducerii=couponlist.objects.get(code=contactnumberdonei[0]['codecoupon'])
                    if codeconsumereducerii.is_consumable == True and codeconsumereducerii.redeemlimit>0:
                        codeconsumereduceri=int(codeconsumereducerii.redeemlimit)-1
                        codeconsumereducer=couponlist.objects.filter(code=contactnumberdonei[0]['codecoupon']).update(redeemlimit=codeconsumereduceri)
                    else:
                        pass
                else:
                    pass
            else:
                pass
            if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone, productname='Ready'):
                deletethis=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone, productname='Ready')
                deletethis.delete()
            Done = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone)
            try:
                Sales.objects.filter(contactnumber=contactnumberdonei[0]['contactnumber'], CusName=contactnumberdonei[0]['Customername'], productname='DeliveryFee', DateTime=contactnumberdonei[0]['DateTime'])
                deliveryfeepaid='true'
            except Sales.DoesNotExist:
                deliveryfeepaid='false'
            if contactnumberdonei[0]['DeliveryFee'] != None and deliveryfeepaid == 'true':
                devfeeassales=Sales.objects.create(
                        user=userr,
                        CusName=contactnumberdonei[0]['Customername'],
                        codecoupon=contactnumberdonei[0]['codecoupon'] or None,
                        discount=contactnumberdonei[0]['discount'] or None,
                        Province=contactnumberdonei[0]['Province'],
                        MunicipalityCity=contactnumberdonei[0]['MunicipalityCity'],
                        Barangay=contactnumberdonei[0]['Barangay'],
                        StreetPurok=contactnumberdonei[0]['StreetPurok'],
                        Housenumber=contactnumberdonei[0]['Housenumber'] or None,
                        LandmarksnNotes=contactnumberdonei[0]['LandmarksnNotes'] or None,
                        DeliveryFee=contactnumberdonei[0]['DeliveryFee'] or None,
                        contactnumber=contactnumberdonei[0]['contactnumber'],
                        productname='DeliveryFee',
                        Category='DeliveryFee',
                        Subcategory='DeliveryFee',
                        Size=None,
                        PSize=None,
                        Addons=None,
                        QtyAddons=0,
                        Price=contactnumberdonei[0]['DeliveryFee'],
                        Subtotal = contactnumberdonei[0]['DeliveryFee'],
                        GSubtotal=contactnumberdonei[0]['GSubtotal'],
                        Cost=0,
                        Qty=1,
                        Bill=contactnumberdonei[0]['Bill'] or 0,
                        Change=contactnumberdonei[0]['Change'] or 0,
                        MOP=contactnumberdonei[0]['MOP'],
                        ordertype='Online',
                        Timetodeliver=contactnumberdonei[0]['Timetodeliver'] or None,
                        ScheduleTime=contactnumberdonei[0]['ScheduleTime'] or None,
                        gpslat = contactnumberdonei[0]['gpslat'],
                        gpslng = contactnumberdonei[0]['gpslng'],
                        gpsaccuracy = contactnumberdonei[0]['gpsaccuracy'],
                        pinnedlat = contactnumberdonei[0]['pinnedlat'],
                        pinnedlng = contactnumberdonei[0]['pinnedlng'],
                            
                        tokens = contactnumberdonei[0]['tokens'] or None,
                        DateTime=contactnumberdonei[0]['DateTime'],
                )
                devfeeassales.save()
            if contactnumberdonei[0]['discount']:
                objs = [Sales(
                            user=userr,
                            CusName=Done.Customername,
                            codecoupon=Done.codecoupon,
                            discount=Done.discount or None,
                            Province=Done.Province,
                            MunicipalityCity=Done.MunicipalityCity,
                            Barangay=Done.Barangay,
                            StreetPurok=Done.StreetPurok,
                            Housenumber=Done.Housenumber or None,
                            LandmarksnNotes=Done.LandmarksnNotes or None,
                            DeliveryFee=Done.DeliveryFee or None,
                            contactnumber=Done.contactnumber,
                            productname=Done.productname,
                            Category=Done.Category,
                            Subcategory=Done.Subcategory or None,
                            Size=Done.Size  or None,
                            PSize=Done.PSize or None,
                            Addons=Done.Addons or None,
                            QtyAddons= Done.QtyAddons or 0,
                            Price=Done.Price,
                            Subtotal = Done.Subtotal-((Done.Subtotal)*(Decimal(int(Done.discount)/100))),
                            GSubtotal=Done.GSubtotal,
                            Cost=Done.Cost,
                            Qty=Done.Qty,
                            Bill=Done.Bill or 0,
                            Change=Done.Change or 0,
                            MOP=Done.MOP,
                            ordertype='Online',
                            Timetodeliver=Done.Timetodeliver,
                            ScheduleTime=Done.ScheduleTime,
                            gpslat = Done.gpslat,
                            gpslng = Done.gpslng,
                            gpsaccuracy = Done.gpsaccuracy,
                            pinnedlat = Done.pinnedlat,
                            pinnedlng = Done.pinnedlng,
                            
                            tokens = Done.tokens or None,
                            DateTime=Done.DateTime,
                    )
                    for Done in Done
                ]
            else:
                objs = [Sales(
                            user=userr,
                            CusName=Done.Customername,
                            codecoupon=Done.codecoupon,
                            discount=Done.discount or None,
                            Province=Done.Province,
                            MunicipalityCity=Done.MunicipalityCity,
                            Barangay=Done.Barangay,
                            StreetPurok=Done.StreetPurok,
                            Housenumber=Done.Housenumber or None,
                            LandmarksnNotes=Done.LandmarksnNotes or None,
                            DeliveryFee=Done.DeliveryFee or None,
                            contactnumber=Done.contactnumber,
                            productname=Done.productname,
                            Category=Done.Category,
                            Subcategory=Done.Subcategory or None,
                            Size=Done.Size  or None,
                            PSize=Done.PSize or None,
                            Addons=Done.Addons or None,
                            QtyAddons= Done.QtyAddons or 0,
                            Price=Done.Price,
                            Subtotal = Done.Subtotal,
                            GSubtotal=Done.GSubtotal,
                            Cost=Done.Cost,
                            Qty=Done.Qty,
                            Bill=Done.Bill or 0,
                            Change=Done.Change or 0,
                            MOP=Done.MOP,
                            ordertype='Online',
                            Timetodeliver=Done.Timetodeliver,
                            ScheduleTime=Done.ScheduleTime,
                            gpslat = Done.gpslat,
                            gpslng = Done.gpslng,
                            gpsaccuracy = Done.gpsaccuracy,
                            pinnedlat = Done.pinnedlat,
                            pinnedlng = Done.pinnedlng,
                            
                            tokens = Done.tokens or None,
                            DateTime=Done.DateTime,
                    )
                    for Done in Done
                ]
            Salesorders = Sales.objects.bulk_create(objs)
            Done.delete()

        ####### BASE Order from website ####
        notifyorder=acknowledgedstockorder.objects.filter(CusName="Notify",user=userr).count()
        if acknowledgedstockorder.objects.all().count()==0:
           notifyadmin=submitstockorder.objects.all().count()
        else:
           notifyadmin=0
        datetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m')
        stock = Sales.objects.all().filter(user=userr, Categoryaes__saecatchoices='Stock', DateTime__month = datetoday)
       
        expenses= Sales.objects.all().filter(user=userr, Categoryaes__saecatchoices='Expenses', DateTime__month = datetoday)
        if len(Acceptorder.objects.filter(Admin=userr, productname='Ready'))>0:
            initial=Acceptorder.objects.filter(Admin=userr, productname='Ready').values_list('contactnumber', flat=True)
            readylistcontact=list(initial)
        else:
            readylistcontact=list(Acceptorder.objects.none())
        print('readylistcontact1:',readylistcontact)
        if request.method == "POST":
            sae = stocksandexpenses(request.POST, request.FILES)
            if sae.is_valid():
                sae.save()
                return HttpResponseRedirect('/index/kgddashboard')
            else:
                return render(request, 'StocksandExp.html',{'readylistcontact':readylistcontact, 'onlineordercounter':onlineordercounter,'viewordersreject':viewordersreject,'rejectedorder':rejectedorder,'viewordersaccept':viewordersaccept,'acceptedorder':acceptedorder,'onlineorder':onlineorder,'notifyadmin':notifyadmin,'notifyorder':notifyorder,'sae':sae,'userr':userr, 'stock':stock,'expenses':expenses})
        else:
           sae = stocksandexpenses
           return render(request, 'StocksandExp.html',{'readylistcontact':readylistcontact, 'onlineordercounter':onlineordercounter,'viewordersreject':viewordersreject,'rejectedorder':rejectedorder,'viewordersaccept':viewordersaccept,'acceptedorder':acceptedorder,'onlineorder':onlineorder,'notifyadmin':notifyadmin,'notifyorder':notifyorder,'sae':sae,'userr':userr, 'stock':stock,'expenses':expenses})
        return render(request, 'StocksandExp.html')

#@login_required
#def saereceipt(request):
#       return redirect('saereceiptimage.html')





            
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, int):
            return int(obj)
        elif isinstance(obj, datetime.datetime):
            return obj.__str__()
        return json.JSONEncoder.default(self, obj)





@login_required
def postwo(request):
        
        userr=request.user.id
        #print(Acceptorder.objects.filter(Customername='Ysabelle Caluza').values_list('LocationMarker', flat=True)[0])
        if request.GET.get('acceptcontactno'):
            contactnumberaccept = request.GET.get('acceptcontactno')
            rider = request.GET.get('rider')
            getETA = request.GET.get('ETA')
            Accepted = Customer.objects.filter(Admin=userr,contactnumber=contactnumberaccept)
            
            objs = [Acceptorder(
                        Admin=Accepted.Admin,
                        Customername=Accepted.Customername,
                        codecoupon=Accepted.codecoupon,
                        discount=Accepted.discount or None,
                        Province=Accepted.Province,
                        MunicipalityCity=Accepted.MunicipalityCity,
                        Barangay=Accepted.Barangay,
                        StreetPurok=Accepted.StreetPurok,
                        Housenumber=Accepted.Housenumber or None,
                        LandmarksnNotes=Accepted.LandmarksnNotes or None,
                        DeliveryFee=Accepted.DeliveryFee or 0,
                        contactnumber=Accepted.contactnumber,
                        Rider=rider,
                        productname=Accepted.productname,
                        Category=Accepted.Category,
                        Subcategory=Accepted.Subcategory or None,
                        Size=Accepted.Size  or None,
                        PSize=Accepted.PSize or None,
                        Addons=Accepted.Addons or None,
                        QtyAddons= Accepted.QtyAddons or 0,
                        Price=Accepted.Price,
                        Subtotal = Accepted.Subtotal,
                        GSubtotal=Accepted.GSubtotal,
                        Cost=Accepted.Cost,
                        Qty=Accepted.Qty,
                        Bill=Accepted.Bill or 0,
                        Change=Accepted.Change or 0,
                        ETA=getETA,
                        MOP=Accepted.MOP,
                        ordertype='Online',
                        Timetodeliver=Accepted.Timetodeliver,
                        ScheduleTime=Accepted.ScheduleTime,
                        gpslat = Accepted.gpslat,
                        gpslng = Accepted.gpslng,
                        gpsaccuracy = Accepted.gpsaccuracy,
                        pinnedlat = Accepted.pinnedlat,
                        pinnedlng = Accepted.pinnedlng,
                        tokens = Accepted.tokens or None,
                        DateTime=Accepted.DateTime,
                )
                for Accepted in Accepted
            ]
            Acceptorders = Acceptorder.objects.bulk_create(objs)
            Accepted.delete()
            messageacknowledgetokeni=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberaccept).values_list('tokens',flat=True).first()
            messageacknowledgetoken = ["dHEGNR4YGO8a-AVQWfIE33:APA91bGkNxUcRZEHJQCkUy3k3THUEMxml9q4819bDQw1b8UkD05qThidgXq3Nnr46I1pwQikZgwiGFuBgKwUxHO6kUXI9KId3ZK0fQ0zi83QegTtVimqV18a2pDqBq5qnJf-BK74Z1nL", messageacknowledgetokeni]
            acknowledge(request, messageacknowledgetoken)
            MessageRider(request)
            return HttpResponseRedirect('/index/pos')

        if len(Acceptorder.objects.filter(Admin=userr))>0:
            acceptedorder = Acceptorder.objects.filter(Admin=userr).distinct('contactnumber')
            acceptedorderall = Acceptorder.objects.filter(Admin=userr)
        else:
            acceptedorder = Acceptorder.objects.none()
            acceptedorderall = Acceptorder.objects.none()
        viewordersacceptii={}
        arrayoneaccept=[]
        contactdistincteraccepti = Acceptorder.objects.filter(Admin=userr).distinct('contactnumber')
        contactdistincteraccept=contactdistincteraccepti.values_list('contactnumber',flat=True)
        i=0
        for cndistinctaccept in contactdistincteraccept:
            arrayseparatoracceptiii=Acceptorder.objects.filter(Admin=userr,contactnumber=cndistinctaccept).exclude(productname='Ready').values()
            arrayseparatoraccepti = list(arrayseparatoracceptiii)
            arrayseparatoraccept=json.dumps(arrayseparatoraccepti, cls=JSONEncoder)
            viewordersacceptii[contactdistincteraccept[i]]=arrayseparatoraccept
            i=i+1
        viewordersaccepti=viewordersacceptii
        viewordersaccept=json.dumps(viewordersaccepti, cls=JSONEncoder)
        

        if (request.GET.get('rider') == "") and (request.GET.get('contactnoreject') or request.GET.get('contactnoaccepted')):
            if request.GET.get('contactnoreject'):
                contactnumberreject = request.GET.get('contactnoreject')
                Rejected = Customer.objects.filter(Admin=userr,contactnumber=contactnumberreject)
            elif request.GET.get('contactnoaccepted'):
                contactnumberreject = request.GET.get('contactnoaccepted')
                if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject, productname='Ready'):
                    deletethis=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject, productname='Ready')
                    deletethis.delete()
                Rejected = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject)
            
            objs = [Rejectorder(
                        Admin=userr,
                        Customername=Rejected.Customername,
                        codecoupon=Rejected.codecoupon,
                        discount=Rejected.discount or None,
                        Province=Rejected.Province,
                        MunicipalityCity=Rejected.MunicipalityCity,
                        Barangay=Rejected.Barangay,
                        StreetPurok=Rejected.StreetPurok,
                        Housenumber=Rejected.Housenumber or None,
                        LandmarksnNotes=Rejected.LandmarksnNotes or None,
                        DeliveryFee=Rejected.DeliveryFee or 0,
                        contactnumber=Rejected.contactnumber,
                        productname=Rejected.productname,
                        Category=Rejected.Category,
                        Subcategory=Rejected.Subcategory or None,
                        Size=Rejected.Size  or None,
                        PSize=Rejected.PSize or None,
                        Addons=Rejected.Addons or None,
                        QtyAddons= Rejected.QtyAddons or 0,
                        Price=Rejected.Price,
                        Subtotal = Rejected.Subtotal,
                        GSubtotal=Rejected.GSubtotal,
                        Cost=Rejected.Cost,
                        Qty=Rejected.Qty,
                        Bill=Rejected.Bill or 0,
                        Change=Rejected.Change or 0,
                        MOP=Rejected.MOP,
                        ordertype='Online',
                        Timetodeliver=Rejected.Timetodeliver,
                        ScheduleTime=Rejected.ScheduleTime,
                        gpslat = Rejected.gpslat,
                        gpslng = Rejected.gpslng,
                        gpsaccuracy = Rejected.gpsaccuracy,
                        pinnedlat = Rejected.pinnedlat,
                        pinnedlng = Rejected.pinnedlng,
                        tokens = Rejected.tokens  or None,
                        DateTime=Rejected.DateTime,
                )
                for Rejected in Rejected
            ]
            Rejectorders = Rejectorder.objects.bulk_create(objs)
            Rejected.delete()
            return HttpResponseRedirect('/index/pos')

        if len(Rejectorder.objects.filter(Admin=userr))>0:
            rejectedorder = Rejectorder.objects.filter(Admin=userr).distinct('contactnumber')
            rejectedorderall = Rejectorder.objects.filter(Admin=userr)
        else:
            rejectedorder = Rejectorder.objects.none()
            rejectedorderall = Rejectorder.objects.none()
        viewordersrejectii={}
        arrayonereject=[]
        contactdistincterrejecti = Rejectorder.objects.filter(Admin=userr).distinct('contactnumber')
        contactdistincterreject=contactdistincterrejecti.values_list('contactnumber',flat=True)
        i=0
        for cndistinctreject in contactdistincterreject:
            arrayseparatorrejectiii=Rejectorder.objects.filter(Admin=userr,contactnumber=cndistinctreject).exclude(productname='Ready').values()
            arrayseparatorrejecti = list(arrayseparatorrejectiii)
            arrayseparatorreject=json.dumps(arrayseparatorrejecti, cls=JSONEncoder)
            viewordersrejectii[contactdistincterreject[i]]=arrayseparatorreject
            i=i+1
        viewordersrejecti=viewordersrejectii
        viewordersreject=json.dumps(viewordersrejecti, cls=JSONEncoder)

        

        if request.GET.get('contactnorestore'):
            contactnumberrestore = request.GET.get('contactnorestore')
            Restored = Rejectorder.objects.filter(Admin=userr,contactnumber=contactnumberrestore)
            
            objs = [Customer(
                        Admin=userr,
                        Customername=Restored.Customername,
                        codecoupon=Restored.codecoupon,
                        discount=Restored.discount or None,
                        Province=Restored.Province,
                        MunicipalityCity=Restored.MunicipalityCity,
                        Barangay=Restored.Barangay,
                        StreetPurok=Restored.StreetPurok,
                        Housenumber=Restored.Housenumber or None,
                        LandmarksnNotes=Restored.LandmarksnNotes or None,
                        DeliveryFee=Restored.DeliveryFee or 0,
                        contactnumber=Restored.contactnumber,
                        productname=Restored.productname,
                        Category=Restored.Category,
                        Subcategory=Restored.Subcategory or None,
                        Size=Restored.Size  or None,
                        PSize=Restored.PSize or None,
                        Addons=Restored.Addons or None,
                        QtyAddons= Restored.QtyAddons or 0,
                        Price=Restored.Price,
                        Subtotal = Restored.Subtotal,
                        GSubtotal=Restored.GSubtotal,
                        Cost=Restored.Cost,
                        Qty=Restored.Qty,
                        Bill=Restored.Bill or 0,
                        Change=Restored.Change or 0,
                        MOP=Restored.MOP,
                        ordertype='Online',
                        Timetodeliver=Restored.Timetodeliver,
                        ScheduleTime=Restored.ScheduleTime,
                        gpslat = Restored.gpslat,
                        gpslng = Restored.gpslng,
                        gpsaccuracy = Restored.gpsaccuracy,
                        pinnedlat = Restored.pinnedlat,
                        pinnedlng = Restored.pinnedlng,
                        
                        tokens = Restored.tokens  or None,
                        DateTime=Restored.DateTime,
                )
                for Restored in Restored
            ]
            Restore = Customer.objects.bulk_create(objs)
            Restored.delete()
            return HttpResponseRedirect('/index/pos')

        if len(Customer.objects.filter(Admin=userr))>0:
            onlineorder = Customer.objects.filter(Admin=userr).distinct('contactnumber')
            onlineorderall = Customer.objects.filter(Admin=userr)
        else:
            onlineorder = Customer.objects.none()
            onlineorderall = Customer.objects.none()
        viewordersii={}
        arrayone=[]
        contactdistincteri = Customer.objects.filter(Admin=userr).distinct('contactnumber')
        contactdistincter=contactdistincteri.values_list('contactnumber',flat=True)
        i=0
        for cndistinct in contactdistincter:  
            arrayseparatoriii=Customer.objects.filter(Admin=userr,contactnumber=cndistinct).values()
            arrayseparatori = list(arrayseparatoriii)
            arrayseparator=json.dumps(arrayseparatori, cls=JSONEncoder)
            viewordersii[contactdistincter[i]]=arrayseparator
            i=i+1
        viewordersi=viewordersii
        vieworders=json.dumps(viewordersi, cls=JSONEncoder)

        onlineordercounter = len(Customer.objects.filter(Admin=userr).distinct('contactnumber'))

        if is_ajax(request=request) and request.POST.get("Ready"):
            contactnumberready = request.POST.get('Ready')
            Readyadd = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).first()
            Readyacceptorder=Acceptorder.objects.create(
                        Admin=userr,
                        Customername=Readyadd.Customername,
                        codecoupon=Readyadd.codecoupon,
                        discount=Readyadd.discount or None,
                        Province=Readyadd.Province,
                        MunicipalityCity=Readyadd.MunicipalityCity,
                        Barangay=Readyadd.Barangay,
                        StreetPurok=Readyadd.StreetPurok,
                        Housenumber=Readyadd.Housenumber or None,
                        LandmarksnNotes=Readyadd.LandmarksnNotes or None,
                        DeliveryFee=0,
                        contactnumber=Readyadd.contactnumber,
                        productname='Ready',
                        Category=Readyadd.Category,
                        Subcategory=None,
                        Size=None,
                        PSize=None,
                        Addons=None,
                        QtyAddons= 0,
                        Price=0,
                        Subtotal = 0,
                        GSubtotal=Readyadd.GSubtotal,
                        Cost=0,
                        Qty=0,
                        Bill=Readyadd.Bill or 0,
                        Change=Readyadd.Change or 0,
                        MOP=Readyadd.MOP,
                        ordertype='Online',
                        Timetodeliver=Readyadd.Timetodeliver,
                        ScheduleTime=Readyadd.ScheduleTime,
                        gpslat = Readyadd.gpslat,
                        gpslng = Readyadd.gpslng,
                        gpsaccuracy = Readyadd.gpsaccuracy,
                        pinnedlat = Readyadd.pinnedlat,
                        pinnedlng = Readyadd.pinnedlng,
                        
                        tokens = Readyadd.tokens  or None,
                        DateTime=Readyadd.DateTime,
                        )
            Readyacceptorder.save()
            if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready, MOP='COD'):
                orderprepared(request)
            messageacknowledgetokeni=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('tokens',flat=True).first()
            messageacknowledgetoken = ["dHEGNR4YGO8a-AVQWfIE33:APA91bGkNxUcRZEHJQCkUy3k3THUEMxml9q4819bDQw1b8UkD05qThidgXq3Nnr46I1pwQikZgwiGFuBgKwUxHO6kUXI9KId3ZK0fQ0zi83QegTtVimqV18a2pDqBq5qnJf-BK74Z1nL", messageacknowledgetokeni]
            if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('MOP',flat=True).first() == 'COD' or Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('MOP',flat=True).first() == 'GcashDelivery':
                deliveryotwRider(request)
                deliveryotwCustomer(request , messageacknowledgetoken)
            else:
                pickupCustomer(request , messageacknowledgetoken)
            return JsonResponse({'Ready':'Ready'})
        if is_ajax(request=request) and request.GET.get("apini"):
            onlineordercounterf = onlineordercounter
            onlineorderf = [serializers.serialize('json',onlineorder, cls=JSONEncoder),vieworders]

            return JsonResponse({'onlineorderf':onlineorderf})
            
        if is_ajax(request=request) and request.POST.get('doneorders'):
            contactnumberdonei = json.loads(request.POST.get('doneorders'))
            contactnumberdone = contactnumberdonei[0]['contactnumber']
            if contactnumberdonei[0]['codecoupon']:
                if couponlist.objects.filter(code=contactnumberdonei[0]['codecoupon']):
                    codeconsumereducerii=couponlist.objects.get(code=contactnumberdonei[0]['codecoupon'])
                    if codeconsumereducerii.is_consumable == True and codeconsumereducerii.redeemlimit > 0:
                        codeconsumereduceri=int(codeconsumereducerii.redeemlimit)-1
                        codeconsumereducer=couponlist.objects.filter(code=contactnumberdonei[0]['codecoupon']).update(redeemlimit=codeconsumereduceri)
                    else:
                        pass
                else:
                    pass
            else:
                pass
            if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone, productname='Ready'):
                deletethis=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone, productname='Ready')
                deletethis.delete()
            Done = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone)
            try:
                Sales.objects.filter(contactnumber=contactnumberdonei[0]['contactnumber'], CusName=contactnumberdonei[0]['Customername'], productname='DeliveryFee', DateTime=contactnumberdonei[0]['DateTime'])
                deliveryfeepaid='true'
            except Sales.DoesNotExist:
                deliveryfeepaid='false'
            if contactnumberdonei[0]['DeliveryFee'] != None and deliveryfeepaid == 'true':
                devfeeassales=Sales.objects.create(
                        user=userr,
                        CusName=contactnumberdonei[0]['Customername'],
                        codecoupon=contactnumberdonei[0]['codecoupon'] or None,
                        discount=contactnumberdonei[0]['discount'] or None,
                        Province=contactnumberdonei[0]['Province'],
                        MunicipalityCity=contactnumberdonei[0]['MunicipalityCity'],
                        Barangay=contactnumberdonei[0]['Barangay'],
                        StreetPurok=contactnumberdonei[0]['StreetPurok'],
                        Housenumber=contactnumberdonei[0]['Housenumber'] or None,
                        LandmarksnNotes=contactnumberdonei[0]['LandmarksnNotes'] or None,
                        DeliveryFee=contactnumberdonei[0]['DeliveryFee'] or None,
                        contactnumber=contactnumberdonei[0]['contactnumber'],
                        productname='DeliveryFee',
                        Category='DeliveryFee',
                        Subcategory='DeliveryFee',
                        Size=None,
                        PSize=None,
                        Addons=None,
                        QtyAddons=0,
                        Price=contactnumberdonei[0]['DeliveryFee'],
                        Subtotal = contactnumberdonei[0]['DeliveryFee'],
                        GSubtotal=contactnumberdonei[0]['GSubtotal'],
                        Cost=0,
                        Qty=1,
                        Bill=contactnumberdonei[0]['Bill'] or 0,
                        Change=contactnumberdonei[0]['Change'] or 0,
                        MOP=contactnumberdonei[0]['MOP'],
                        ordertype='Online',
                        Timetodeliver=contactnumberdonei[0]['Timetodeliver'] or None,
                        ScheduleTime=contactnumberdonei[0]['ScheduleTime'] or None,
                        gpslat = contactnumberdonei[0]['gpslat'],
                        gpslng = contactnumberdonei[0]['gpslng'],
                        gpsaccuracy = contactnumberdonei[0]['gpsaccuracy'],
                        pinnedlat = contactnumberdonei[0]['pinnedlat'],
                        pinnedlng = contactnumberdonei[0]['pinnedlng'],
                        
                        tokens = contactnumberdonei[0]['tokens'] or None,
                        DateTime=contactnumberdonei[0]['DateTime'],
                )
                devfeeassales.save()
            if contactnumberdonei[0]['discount']:
                objs = [Sales(
                            user=userr,
                            CusName=Done.Customername,
                            codecoupon=Done.codecoupon,
                            discount=Done.discount or None,
                            Province=Done.Province,
                            MunicipalityCity=Done.MunicipalityCity,
                            Barangay=Done.Barangay,
                            StreetPurok=Done.StreetPurok,
                            Housenumber=Done.Housenumber or None,
                            LandmarksnNotes=Done.LandmarksnNotes or None,
                            DeliveryFee=Done.DeliveryFee or None,
                            contactnumber=Done.contactnumber,
                            productname=Done.productname,
                            Category=Done.Category,
                            Subcategory=Done.Subcategory or None,
                            Size=Done.Size  or None,
                            PSize=Done.PSize or None,
                            Addons=Done.Addons or None,
                            QtyAddons= Done.QtyAddons or 0,
                            Price=Done.Price,
                            Subtotal = Done.Subtotal-((Done.Subtotal)*(Decimal(int(Done.discount)/100))),
                            GSubtotal=Done.GSubtotal,
                            Cost=Done.Cost,
                            Qty=Done.Qty,
                            Bill=Done.Bill or 0,
                            Change=Done.Change or 0,
                            MOP=Done.MOP,
                            ordertype='Online',
                            Timetodeliver=Done.Timetodeliver,
                            ScheduleTime=Done.ScheduleTime,
                            gpslat = Done.gpslat,
                            gpslng = Done.gpslng,
                            gpsaccuracy = Done.gpsaccuracy,
                            pinnedlat = Done.pinnedlat,
                            pinnedlng = Done.pinnedlng,
                       
                            tokens = Done.tokens or None,
                            DateTime=Done.DateTime,
                    )
                    for Done in Done
                ]
            else:
                objs = [Sales(
                            user=userr,
                            CusName=Done.Customername,
                            codecoupon=Done.codecoupon,
                            discount=Done.discount or None,
                            Province=Done.Province,
                            MunicipalityCity=Done.MunicipalityCity,
                            Barangay=Done.Barangay,
                            StreetPurok=Done.StreetPurok,
                            Housenumber=Done.Housenumber or None,
                            LandmarksnNotes=Done.LandmarksnNotes or None,
                            DeliveryFee=Done.DeliveryFee or None,
                            contactnumber=Done.contactnumber,
                            productname=Done.productname,
                            Category=Done.Category,
                            Subcategory=Done.Subcategory or None,
                            Size=Done.Size  or None,
                            PSize=Done.PSize or None,
                            Addons=Done.Addons or None,
                            QtyAddons= Done.QtyAddons or 0,
                            Price=Done.Price,
                            Subtotal = Done.Subtotal,
                            GSubtotal=Done.GSubtotal,
                            Cost=Done.Cost,
                            Qty=Done.Qty,
                            Bill=Done.Bill or 0,
                            Change=Done.Change or 0,
                            MOP=Done.MOP,
                            ordertype='Online',
                            Timetodeliver=Done.Timetodeliver,
                            ScheduleTime=Done.ScheduleTime,
                            gpslat = Done.gpslat,
                            gpslng = Done.gpslng,
                            gpsaccuracy = Done.gpsaccuracy,
                            pinnedlat = Done.pinnedlat,
                            pinnedlng = Done.pinnedlng,
                       
                            tokens = Done.tokens or None,
                            DateTime=Done.DateTime,
                    )
                    for Done in Done
                ]
            Salesorders = Sales.objects.bulk_create(objs)
            Done.delete()
            datetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
            monthtoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m')
            yeartoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y')
            try:
                getdailysales=Dailysales.objects.filter(user=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Sales', flat=True)[0]
                timesheetupdate=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(Sales=getdailysales)
            except IndexError:
                timesheetupdate=timesheet.objects.none()
                getdailysales=0
            if getdailysales >= 2000 and timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday):
                getinitialsalarytoday=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('ISalary', flat=True)
                getASLBALANCEtodayi=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('ASLbalance', flat=True)
                addbonusornot=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Identifybonus', flat=True)
                if addbonusornot[0] == 'Added bonus':
                    pass
                else:
                    twokeysalebonus=getinitialsalarytoday[0]+30
                    if getASLBALANCEtodayi[0] >= 30:
                        getASLBALANCEtoday=getASLBALANCEtodayi[0]-30
                        timesheetupdatetwo=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(ISalary=twokeysalebonus, ASLbalance=getASLBALANCEtoday,Identifybonus='Added bonus')
                    else:
                        getASLBALANCEtoday=0
                        addtofinalsalaryi=30-getASLBALANCEtodayi[0]
                        getfinalsalarytoday=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('FSalary', flat=True)
                        addtofinalsalary=addtofinalsalaryi+getfinalsalarytoday
                        timesheetupdatetwo=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(ISalary=twokeysalebonus, ASLbalance=getASLBALANCEtoday,Identifybonus='Added bonus',FSalary=addtofinalsalary)
            return HttpResponseRedirect('/index/pos')



        notifyorder=acknowledgedstockorder.objects.filter(CusName="Notify",user=userr).count()
        if acknowledgedstockorder.objects.all().count()==0:
            notifyadmin=submitstockorder.objects.all().count()
        else:
            notifyadmin=0
        print('userr:',userr) 
        if punchedprod.objects.filter(user=userr).count()==0:
            punchedtotal=0
        else:
            punchedtotal=punchedprod.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
        
        mtbuttons = user1.objects.filter(Category__Categorychoices='Milktea',user__id=userr).distinct('productname')
        i=0
        mtpricess={}
        mtpricesii = user1.objects.filter(Category__Categorychoices='Milktea',user__id=userr).values_list('Price',flat=True).order_by('-id')
        
        mtproductnameii=mtpricesii.values_list('productname',flat=True)
        
        mtsizeii=mtpricesii.values_list('Size__Sizechoices',flat=True)
        
        while i<mtpricesii.count():
            mtpricess[mtproductnameii[i]+mtsizeii[i]]=mtpricesii[i]

            i += 1
        mtpricesss=mtpricess
        
        mtprices=json.dumps(mtpricesss)
        
        ii=0
        mtcostss={}
        mtcostsii = user1.objects.filter(Category__Categorychoices='Milktea',user__id=userr).values_list('Cost',flat=True).order_by('-id')
        
        mtproductnameii=mtcostsii.values_list('productname',flat=True)
        
        mtsizeii=mtcostsii.values_list('Size__Sizechoices',flat=True)
        
        while ii<mtcostsii.count():
            mtcostss[mtproductnameii[ii]+mtsizeii[ii]]=mtcostsii[ii]

            ii += 1
        counter=len(mtcostss)
        
        iii=0
        keys=[]
        mtcostaaai=[]
        for key, mtcostaaa in mtcostss.items():
            keys.append(key)
            mtcostaaai.append(float(mtcostaaa))
        
        
        mtcostsss=mtcostss.values()
        mtcostsi=mtcostaaai
        mtcosts=json.dumps(mtcostsi)

        mtkeyscosts=json.dumps(keys)

        mtsizes = Sizes.objects.all()
        Categoriess = Categories.objects.all()
        Subcategoriess = Subcategories.objects.all()
        frbuttons = user1.objects.filter(Category__Categorychoices='Frappe',user__id=userr).distinct('productname')
        iiii=0
        frpricess={}
        frpricesii = user1.objects.filter(Category__Categorychoices='Frappe',user__id=userr).values_list('Price',flat=True).order_by('-id')
        
        frproductnameii=frpricesii.values_list('productname',flat=True)
        
        frsizeii=frpricesii.values_list('Size__Sizechoices',flat=True)
        
        while iiii<frpricesii.count():
            frpricess[frproductnameii[iiii]+frsizeii[iiii]]=frpricesii[iiii]

            iiii += 1
        frpricesss=frpricess
        
        frprices=json.dumps(frpricesss)

        iiiii=0
        frcostss={}
        frcostsii = user1.objects.filter(Category__Categorychoices='Frappe',user__id=userr).values_list('Cost',flat=True).order_by('-id')
        
        frproductnameii=frcostsii.values_list('productname',flat=True)
        
        frsizeii=frcostsii.values_list('Size__Sizechoices',flat=True)
        
        while iiiii<frcostsii.count():
            frcostss[frproductnameii[iiiii]+frsizeii[iiiii]]=frcostsii[iiiii]

            iiiii += 1
        counterfr=len(frcostss)
        
        iiiiii=0
        keysfr=[]
        frcostaaai=[]
        for key, frcostaaa in frcostss.items():
            keysfr.append(key)
            frcostaaai.append(float(frcostaaa))
        
        
        frcostsss=frcostss.values()
        frcostsi=frcostaaai
        frcosts=json.dumps(frcostsi)
        
        frkeyscosts=json.dumps(keysfr)
        
        frsizes = Sizes.objects.all().exclude(Sizechoices__exact='Small')
        psizes = PSizes.objects.all()
        addonsbuttons = user1.objects.filter(Category__Categorychoices='Add-ons',user__id=userr).distinct('productname')
        iiiiiii=0
        aopricess={}
        aopricesii = user1.objects.filter(Category__Categorychoices='Add-ons',user__id=userr).values_list('Price',flat=True).order_by('-id')
        
        aoproductnameii=aopricesii.values_list('productname',flat=True)
        
        #aosizeii=aopricesii.values_list('Size__Sizechoices',flat=True)
        
        while iiiiiii<aopricesii.count():
            aopricess[aoproductnameii[iiiiiii]]=aopricesii[iiiiiii]

            iiiiiii += 1
        aopricesss=aopricess
        
        aoprices=json.dumps(aopricesss)
        
        iiiiiiii=0
        aocostss={}
        aocostsii = user1.objects.filter(Category__Categorychoices='Add-ons',user__id=userr).values_list('Cost',flat=True).order_by('-id')
        
        aoproductnameii=aocostsii.values_list('productname',flat=True)
        
        
        
        while iiiiiiii<aocostsii.count():
            aocostss[aoproductnameii[iiiiiiii]]=aocostsii[iiiiiiii]

            iiiiiiii += 1
        counterao=len(aocostss)
        
        iiiiiiiii=0
        keysao=[]
        aocostaaai=[]
        for key, aocostaaa in aocostss.items():
            keysao.append(key)
            aocostaaai.append(float(aocostaaa))
        
        
        aocostsss=aocostss.values()
        aocostsi=aocostaaai
        aocosts=json.dumps(aocostsi)
       
        aokeyscosts=json.dumps(keysao)
        
        freezebuttons = user1.objects.filter(Category__Categorychoices='Freeze',user__id=userr).distinct('productname')
        
        iiiiiiiiii=0
        frzpricess={}
        frzpricesii = user1.objects.filter(Category__Categorychoices='Freeze',user__id=userr).values_list('Price',flat=True).order_by('-id')
        
        frzproductnameii=frzpricesii.values_list('productname',flat=True)
        
        #frzsizeii=frzpricesii.values_list('Size__Sizechoices',flat=True)
        
        while iiiiiiiiii<frzpricesii.count():
            frzpricess[frzproductnameii[iiiiiiiiii]]=frzpricesii[iiiiiiiiii]

            iiiiiiiiii += 1
        frzpricesss=frzpricess
        
        frzprices=json.dumps(frzpricesss)
        
        iiiiiiiiiii=0
        frzcostss={}
        frzcostsii = user1.objects.filter(Category__Categorychoices='Freeze',user__id=userr).values_list('Cost',flat=True).order_by('-id')
        
        frzproductnameii=frzcostsii.values_list('productname',flat=True)
        
        
        
        while iiiiiiiiiii<frzcostsii.count():
            frzcostss[frzproductnameii[iiiiiiiiiii]]=frzcostsii[iiiiiiiiiii]

            iiiiiiiiiii += 1
        counterfrz=len(frzcostss)
        
        iiiiiiiiiiii=0
        keysfrz=[]
        frzcostaaai=[]
        for key, frzcostaaa in frzcostss.items():
            keysfrz.append(key)
            frzcostaaai.append(float(frzcostaaa))
        
        
        frzcostsss=frzcostss.values()
        frzcostsi=frzcostaaai
        frzcosts=json.dumps(frzcostsi)
        
        frzkeyscosts=json.dumps(keysfrz)
        
        cookiesbuttons = user1.objects.filter(Subcategory__Subcategorychoices='Cookies',user__id=userr).distinct('productname')

        
        
        iiiiiiiiiiiii=0
        cookiespricess={}
        cookiespricesii = user1.objects.filter(Subcategory__Subcategorychoices='Cookies',user__id=userr).values_list('Price',flat=True).order_by('-id')
        
        cookiesproductnameii=cookiespricesii.values_list('productname',flat=True)
        
        #cookiessizeii=cookiespricesii.values_list('Size__Sizechoices',flat=True)
        
        while iiiiiiiiiiiii<cookiespricesii.count():
            cookiespricess[cookiesproductnameii[iiiiiiiiiiiii]]=cookiespricesii[iiiiiiiiiiiii]

            iiiiiiiiiiiii += 1
        cookiespricesss=cookiespricess
        
        cookiesprices=json.dumps(cookiespricesss)
        
        iiiiiiiiiiiiii=0
        cookiescostss={}
        cookiescostsii = user1.objects.filter(Subcategory__Subcategorychoices='Cookies',user__id=userr).values_list('Cost',flat=True).order_by('-id')
        
        cookiesproductnameii=cookiescostsii.values_list('productname',flat=True)
        
        
        
        while iiiiiiiiiiiiii<cookiescostsii.count():
            cookiescostss[cookiesproductnameii[iiiiiiiiiiiiii]]=cookiescostsii[iiiiiiiiiiiiii]

            iiiiiiiiiiiiii += 1
        countercookies=len(cookiescostss)
        
        iiiiiiiiiiiiiii=0
        keyscookies=[]
        cookiescostaaai=[]
        for key, cookiescostaaa in cookiescostss.items():
            keyscookies.append(key)
            cookiescostaaai.append(float(cookiescostaaa))
        
        
        cookiescostsss=cookiescostss.values()
        cookiescostsi=cookiescostaaai
        cookiescosts=json.dumps(cookiescostsi)
        
        cookieskeyscosts=json.dumps(keyscookies)
        
        friesbuttons = user1.objects.filter(Subcategory__Subcategorychoices='Fries',user__id=userr).distinct('productname').exclude(productname='Free Fries')

        
        
        iiiiiiiiiiiiiiii=0
        friespricess={}
        friespricesii = user1.objects.filter(Subcategory__Subcategorychoices='Fries',user__id=userr).values_list('Price',flat=True).order_by('-id')
        
        friesproductnameii=friespricesii.values_list('productname',flat=True)
        
        #friessizeii=friespricesii.values_list('Size__Sizechoices',flat=True)
        
        while iiiiiiiiiiiiiiii<friespricesii.count():
            friespricess[friesproductnameii[iiiiiiiiiiiiiiii]]=friespricesii[iiiiiiiiiiiiiiii]

            iiiiiiiiiiiiiiii += 1
        friespricesss=friespricess
        
        friesprices=json.dumps(friespricesss)
        
        iiiiiiiiiiiiiiiii=0
        friescostss={}
        friescostsii = user1.objects.filter(Subcategory__Subcategorychoices='Fries',user__id=userr).values_list('Cost',flat=True).order_by('-id')
        
        friesproductnameii=friescostsii.values_list('productname',flat=True)
        
        
        
        while iiiiiiiiiiiiiiiii<friescostsii.count():
            friescostss[friesproductnameii[iiiiiiiiiiiiiiiii]]=friescostsii[iiiiiiiiiiiiiiiii]

            iiiiiiiiiiiiiiiii += 1
        counterfries=len(friescostss)
        
        iiiiiiiiiiiiiiiiii=0
        keysfries=[]
        friescostaaai=[]
        for key, friescostaaa in friescostss.items():
            keysfries.append(key)
            friescostaaai.append(float(friescostaaa))
        
        
        friescostsss=friescostss.values()
        friescostsi=friescostaaai
        friescosts=json.dumps(friescostsi)
        
        frieskeyscosts=json.dumps(keysfries)
        
        shawarmabuttons = user1.objects.filter(Subcategory__Subcategorychoices='Shawarma',user__id=userr).distinct('productname')
        
        
        
        iiiiiiiiiiiiiiiiiii=0
        shawarmapricess={}
        shawarmapricesii = user1.objects.filter(Subcategory__Subcategorychoices='Shawarma',user__id=userr).values_list('Price',flat=True).order_by('-id')
        
        shawarmaproductnameii=shawarmapricesii.values_list('productname',flat=True)
        
        #friessizeii=friespricesii.values_list('Size__Sizechoices',flat=True)
        
        while iiiiiiiiiiiiiiiiiii<shawarmapricesii.count():
            shawarmapricess[shawarmaproductnameii[iiiiiiiiiiiiiiiiiii]]=shawarmapricesii[iiiiiiiiiiiiiiiiiii]

            iiiiiiiiiiiiiiiiiii += 1
        shawarmapricesss=shawarmapricess
        
        shawarmaprices=json.dumps(shawarmapricesss)
        
        iiiiiiiiiiiiiiiiiiii=0
        shawarmacostss={}
        shawarmacostsii = user1.objects.filter(Subcategory__Subcategorychoices='Shawarma',user__id=userr).values_list('Cost',flat=True).order_by('-id')
        
        shawarmaproductnameii=shawarmacostsii.values_list('productname',flat=True)
        
        
        
        while iiiiiiiiiiiiiiiiiiii<shawarmacostsii.count():
            shawarmacostss[shawarmaproductnameii[iiiiiiiiiiiiiiiiiiii]]=shawarmacostsii[iiiiiiiiiiiiiiiiiiii]

            iiiiiiiiiiiiiiiiiiii += 1
        countershawarma=len(shawarmacostss)
        
        iiiiiiiiiiiiiiiiiiiii=0
        keysshawarma=[]
        shawarmacostaaai=[]
        for key, shawarmacostaaa in shawarmacostss.items():
            keysshawarma.append(key)
            shawarmacostaaai.append(float(shawarmacostaaa))
        
        
        shawarmacostsss=shawarmacostss.values()
        shawarmacostsi=shawarmacostaaai
        shawarmacosts=json.dumps(shawarmacostsi)
        
        shawarmakeyscosts=json.dumps(keysshawarma)
        
        bubwafbuttons = user1.objects.filter(Subcategory__Subcategorychoices='Bubble Waffle',user__id=userr).distinct('productname')
        
        
        
        iiiiiiiiiiiiiiiiiiiiii=0
        bubwafpricess={}
        bubwafpricesii = user1.objects.filter(Subcategory__Subcategorychoices='Bubble Waffle',user__id=userr).values_list('Price',flat=True).order_by('-id')
        
        bubwafproductnameii=bubwafpricesii.values_list('productname',flat=True)
        
        #friessizeii=friespricesii.values_list('Size__Sizechoices',flat=True)
        
        while iiiiiiiiiiiiiiiiiiiiii<bubwafpricesii.count():
            bubwafpricess[bubwafproductnameii[iiiiiiiiiiiiiiiiiiiiii]]=bubwafpricesii[iiiiiiiiiiiiiiiiiiiiii]

            iiiiiiiiiiiiiiiiiiiiii += 1
        bubwafpricesss=bubwafpricess
        
        bubwafprices=json.dumps(bubwafpricesss)
        
        iiiiiiiiiiiiiiiiiiiiiii=0
        bubwafcostss={}
        bubwafcostsii = user1.objects.filter(Subcategory__Subcategorychoices='Bubble Waffle',user__id=userr).values_list('Cost',flat=True).order_by('-id')
        
        bubwafproductnameii=bubwafcostsii.values_list('productname',flat=True)
        
        
        
        while iiiiiiiiiiiiiiiiiiiiiii<bubwafcostsii.count():
            bubwafcostss[bubwafproductnameii[iiiiiiiiiiiiiiiiiiiiiii]]=bubwafcostsii[iiiiiiiiiiiiiiiiiiiiiii]

            iiiiiiiiiiiiiiiiiiiiiii += 1
        counterbubwaf=len(bubwafcostss)
        
        iiiiiiiiiiiiiiiiiiiiiiii=0
        keysbubwaf=[]
        bubwafcostaaai=[]
        for key, bubwafcostaaa in bubwafcostss.items():
            keysbubwaf.append(key)
            bubwafcostaaai.append(float(bubwafcostaaa))
        
        
        bubwafcostsss=bubwafcostss.values()
        bubwafcostsi=bubwafcostaaai
        bubwafcosts=json.dumps(bubwafcostsi)
        
        bubwafkeyscosts=json.dumps(keysbubwaf)
        
        pizzabuttons = user1.objects.filter(Subcategory__Subcategorychoices='Pizza',user__id=userr).distinct('productname')
        
        
        
        iiiiiiiiiiiiiiiiiiiiiiiii=0
        pizzapricess={}
        pizzapricesii = user1.objects.filter(Subcategory__Subcategorychoices='Pizza',user__id=userr).values_list('Price',flat=True).order_by('-id')
        
        pizzaproductnameii=pizzapricesii.values_list('productname',flat=True)
        
        pizzasizeii=pizzapricesii.values_list('PSize__PSizechoices',flat=True)
        
        while iiiiiiiiiiiiiiiiiiiiiiiii<pizzapricesii.count():
            pizzapricess[pizzaproductnameii[iiiiiiiiiiiiiiiiiiiiiiiii]+pizzasizeii[iiiiiiiiiiiiiiiiiiiiiiiii]]=pizzapricesii[iiiiiiiiiiiiiiiiiiiiiiiii]

            iiiiiiiiiiiiiiiiiiiiiiiii += 1
        pizzapricesss=pizzapricess
        
        pizzaprices=json.dumps(pizzapricesss)
        
        iiiiiiiiiiiiiiiiiiiiiiiiii=0
        pizzacostss={}
        pizzacostsii = user1.objects.filter(Subcategory__Subcategorychoices='Pizza',user__id=userr).values_list('Cost',flat=True).order_by('-id')
        
        pizzaproductnameii=pizzacostsii.values_list('productname',flat=True)
        
        
        
        while iiiiiiiiiiiiiiiiiiiiiiiiii<pizzacostsii.count():
            pizzacostss[pizzaproductnameii[iiiiiiiiiiiiiiiiiiiiiiiiii]+pizzasizeii[iiiiiiiiiiiiiiiiiiiiiiiiii]]=pizzacostsii[iiiiiiiiiiiiiiiiiiiiiiiiii]

            iiiiiiiiiiiiiiiiiiiiiiiiii += 1
        counterpizza=len(pizzacostss)
        
        iiiiiiiiiiiiiiiiiiiiiiiiiii=0
        keyspizza=[]
        pizzacostaaai=[]
        for key, pizzacostaaa in pizzacostss.items():
            keyspizza.append(key)
            pizzacostaaai.append(float(pizzacostaaa))
        
        
        pizzacostsss=pizzacostss.values()
        pizzacostsi=pizzacostaaai
        pizzacosts=json.dumps(pizzacostsi)
        
        pizzakeyscosts=json.dumps(keyspizza)
        
        snbuttons = user1.objects.filter(Category__Categorychoices='Snacks',user__id=userr)
        #punchedla=punchedprod.objects.filter(user=userr)
        qq1=queue1.objects.all().filter(user=userr)
        qq2=queue2.objects.all().filter(user=userr)
        qq3=queue3.objects.all().filter(user=userr)
        mepunched=punched
        if request.POST.get('done1')=='done1':
            objs = [Sales(
                        user=Sales1pass.user,
                        productname=Sales1pass.productname,
                        Category=Sales1pass.Category,
                        Subcategory=Sales1pass.Subcategory,
                        Size=Sales1pass.Size,
                        PSize=Sales1pass.PSize,
                        Price=Sales1pass.Price,
                        Cost=Sales1pass.Cost,
                        Subtotal=Sales1pass.Subtotal,
                        Qty=Sales1pass.Qty,
                        Bill=Sales1pass.Bill,
                        Change=Sales1pass.Change,
                        CusName=Sales1pass.CusName,
                        DateTime=datetime.datetime.now(pytz.timezone('Asia/Singapore')),
                )
                for Sales1pass in qq1
            ]
            disablepay="disabled"
            Sales1create = Sales.objects.bulk_create(objs)
            qq1.delete()
            messages.success(request,"Orders are done, and saved the record of your transaction! ")

            return HttpResponseRedirect('/index/kgddashboard?next=/index/pos')
        elif request.POST.get('done2'):
            objs = [Sales(
                        user=Sales2pass.user,
                        productname=Sales2pass.productname,
                        Category=Sales2pass.Category,
                        Subcategory=Sales2pass.Subcategory,
                        Size=Sales2pass.Size,
                        PSize=Sales2pass.PSize,
                        Price=Sales2pass.Price,
                        Cost=Sales2pass.Cost,
                        Subtotal=Sales2pass.Subtotal,
                        Qty=Sales2pass.Qty,
                        Bill=Sales2pass.Bill,
                        Change=Sales2pass.Change,
                        CusName=Sales2pass.CusName,
                        DateTime=datetime.datetime.now(pytz.timezone('Asia/Singapore')),
                    
                )
                for Sales2pass in qq2
            ]
            disablepay="disabled"
            Sales2create = Sales.objects.bulk_create(objs)
            qq2.delete()
            messages.success(request,"Orders are done, and saved the record of your transaction! ")
            return HttpResponseRedirect('/index/kgddashboard?next=/index/pos')
        elif request.POST.get('done3')=='done3':

            objs = [Sales(
                        user=Sales3pass.user,
                        productname=Sales3pass.productname,
                        Category=Sales3pass.Category,
                        Subcategory=Sales3pass.Subcategory,
                        Size=Sales3pass.Size,
                        PSize=Sales3pass.PSize,
                        Price=Sales3pass.Price,
                        Cost=Sales3pass.Cost,
                        Subtotal=Sales3pass.Subtotal,
                        Qty=Sales3pass.Qty,
                        Bill=Sales3pass.Bill,
                        Change=Sales3pass.Change,
                        CusName=Sales3pass.CusName,
                        DateTime=datetime.datetime.now(pytz.timezone('Asia/Singapore')),
                )
                for Sales3pass in qq3
            ]
            disablepay="disabled"
            Sales3create = Sales.objects.bulk_create(objs)
            qq3.delete()
            messages.success(request,"Orders are done, and saved the record of your transaction! ")
            return HttpResponseRedirect('/index/kgddashboard?next=/index/pos')
        if request.POST.get('cancel1')=='cancel1':
            qq1.delete()
            return HttpResponseRedirect('/index/pos')
        elif request.POST.get('cancel2')=='cancel2':
            qq2.delete()
            return HttpResponseRedirect('/index/pos')
        elif request.POST.get('cancel3')=='cancel3':
            qq3.delete()
            return HttpResponseRedirect('/index/pos')
        if request.GET.get('Q1')=="Queue1":
            cuspaymentamount=int(request.GET.get('amountpay'))
            tot1=int(request.GET.get('total1'))
            changei=cuspaymentamount-tot1
            arraypunchedi=json.loads(request.GET.get('arrayname'))
            arraypunched=arraypunchedi
            for obj in arraypunched:
                object2=obj['productname']
            arraypunchedcounter=len(arraypunchedi)
            objs = [queue1(
                        user=userr,
                        productname=obj['productname'],
                        Category=obj['Category'],
                        Subcategory=obj['Subcategory'],
                        Size=obj['Size'],
                        Price=obj['Price'],
                        PSize=obj['PSize'],
                        Subtotal=obj['Subtotal'],
                        Qty=obj['Qty'],
                        Cost=obj['Cost'],
                        Bill=cuspaymentamount,
                        Change=changei,
                        CusName=request.GET.get('Cusname1'),
                        DateTime=datetime.datetime.now(pytz.timezone('Asia/Singapore')),

                )
                for obj in arraypunched
            ]
            Sales1create = queue1.objects.bulk_create(objs)
            q1=queue1.objects.all().filter(user=userr)
            q11=queue1.objects.all().filter(user=userr).values_list('CusName','Bill','Change').distinct()
            q111=queue1.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
            
            return HttpResponseRedirect('/index/pos')
        elif request.GET.get('Q2')=="Queue2": 
            cuspaymentamount2=int(request.GET.get('amountpay2'))
            tot2=int(request.GET.get('total2'))
            changei2=cuspaymentamount2-tot2
            arraypunchedi2=json.loads(request.GET.get('arrayname2'))
            arraypunched2=arraypunchedi2
            for obj2 in arraypunched2:
                object2=obj2['productname']
            
            arraypunchedcounter2=len(arraypunchedi2)
            objs2 = [queue2(
                        user=userr,
                        productname=obj2['productname'],
                        Category=obj2['Category'],
                        Subcategory=obj2['Subcategory'],
                        Size=obj2['Size'],
                        Price=obj2['Price'],
                        PSize=obj2['PSize'],
                        Subtotal=obj2['Subtotal'],
                        Qty=obj2['Qty'],
                        Cost=obj2['Cost'],
                        Bill=cuspaymentamount2,
                        Change=changei2,
                        CusName=request.GET.get('Cusname2'),
                        DateTime=datetime.datetime.now(pytz.timezone('Asia/Singapore')),

                )
                for obj2 in arraypunched2
            ]
            Sales2create = queue2.objects.bulk_create(objs2)
            q2=queue2.objects.all().filter(user=userr)
            q22=queue2.objects.all().filter(user=userr).values_list('CusName','Bill','Change').distinct()
            q222=queue2.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
            
            return HttpResponseRedirect('/index/pos')
        elif request.GET.get('Q3') =="Queue3": 
            cuspaymentamount3=int(request.GET.get('amountpay3'))
            tot3=int(request.GET.get('total3'))
            changei3=cuspaymentamount3-tot3
            arraypunchedi3=json.loads(request.GET.get('arrayname3'))
            arraypunched3=arraypunchedi3
            for obj3 in arraypunched3:
                object3=obj3['productname']
            arraypunchedcounter3=len(arraypunchedi3)
            objs3 = [queue3(
                        user=userr,
                        productname=obj3['productname'],
                        Category=obj3['Category'],
                        Subcategory=obj3['Subcategory'],
                        Size=obj3['Size'],
                        Price=obj3['Price'],
                        PSize=obj3['PSize'],
                        Subtotal=obj3['Subtotal'],
                        Qty=obj3['Qty'],
                        Cost=obj3['Cost'],
                        Bill=cuspaymentamount3,
                        Change=changei3,
                        CusName=request.GET.get('Cusname3'),
                        DateTime=datetime.datetime.now(pytz.timezone('Asia/Singapore')),

                )
                for obj3 in arraypunched3
            ]
            Sales3create = queue3.objects.bulk_create(objs3)
            q3=queue3.objects.all().filter(user=userr)
            q33=queue3.objects.all().filter(user=userr).values_list('CusName','Bill','Change').distinct()
            q333=queue3.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
            
            return HttpResponseRedirect('/index/pos')
        else:
            disable="disabled"
            q1=queue1.objects.all().filter(user=userr)
            q11=queue1.objects.all().filter(user=userr).values_list('CusName','Bill','Change').distinct()
            q111=queue1.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
            q2=queue2.objects.all().filter(user=userr)
            q22=queue2.objects.all().filter(user=userr).values_list('CusName','Bill','Change').distinct()
            q222=queue2.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
            q3=queue3.objects.all().filter(user=userr)
            q33=queue3.objects.all().filter(user=userr).values_list('CusName','Bill','Change').distinct()
            q333=queue3.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
            if len(Acceptorder.objects.filter(Admin=userr, productname='Ready'))>0:
                initial=Acceptorder.objects.filter(Admin=userr, productname='Ready').values_list('contactnumber', flat=True)
                readylistcontact=list(initial)
            else:
                readylistcontact=list(Acceptorder.objects.none())
            print('readylistcontact1:',readylistcontact)
            return render(request, 'postwo.html',{'readylistcontact':readylistcontact, 'onlineordercounter':onlineordercounter,'viewordersreject':viewordersreject,'rejectedorder':rejectedorder,'viewordersaccept':viewordersaccept,'acceptedorder':acceptedorder,'onlineorder':onlineorder,'mepunched':mepunched,'pizzakeyscosts':pizzakeyscosts,'pizzacosts':pizzacosts,'pizzaprices':pizzaprices,'bubwafkeyscosts':bubwafkeyscosts,'bubwafcosts':bubwafcosts,'bubwafprices':bubwafprices,'shawarmakeyscosts':shawarmakeyscosts,'shawarmacosts':shawarmacosts,'shawarmaprices':shawarmaprices,'frieskeyscosts':frieskeyscosts,'friescosts':friescosts,'friesprices':friesprices,'cookieskeyscosts':cookieskeyscosts,'cookiescosts':cookiescosts,'cookiesprices':cookiesprices,'aokeyscosts':aokeyscosts,'aocosts':aocosts,'aoprices':aoprices,'frkeyscosts':frkeyscosts,'frzkeyscosts':frzkeyscosts,'frzcosts':frzcosts,'frzprices':frzprices,'frcosts':frcosts,'frprices':frprices,'mtkeyscosts':mtkeyscosts,'mtcosts':mtcosts,'mtprices':mtprices,'notifyadmin':notifyadmin,'notifyorder':notifyorder,'punchedtotal':punchedtotal,'userr':userr,'disable':disable,'psizes':psizes,'q1':q1,'q11':q11,'q111':q111,'q2':q2,'q22':q22,'q222':q222,'q3':q3,'q33':q33,'q333':q333,'pizzabuttons':pizzabuttons,'bubwafbuttons':bubwafbuttons,'shawarmabuttons':shawarmabuttons,'friesbuttons':friesbuttons,'cookiesbuttons':cookiesbuttons,'addonsbuttons':addonsbuttons,'freezebuttons':freezebuttons,'Subcategoriess':Subcategoriess,'mtbuttons':mtbuttons,'frbuttons':frbuttons,'snbuttons':snbuttons,'psizes':psizes,'frsizes':frsizes,'mtsizes':mtsizes,'Categoriess':Categoriess})


    

@login_required
def index(request):
            return render(request, 'index.html')
            
@login_required
def inventory(request):

        return render(request, 'inventory.html')



def Onlineordersystem(request, admin_id):
        #'domain/search/?q=haha', you would use request.GET.get('q', '')
        #theurl+?anykeyhere=anyvalue
        #request.query_params['anykeyhere']
        #then the result will be ="anyvalue"
        #?prmcd=<code>
        
        promocodegeti=request.GET.get('prmcd', '')
        if promocodegeti:
            settings.LOGIN_REDIRECT_URL='/index/onlineorder/'+str(admin_id)+'?prmcd='+promocodegeti
            settings.LOGIN_URL='/index/onlineorder/'+str(admin_id)+'?prmcd='+promocodegeti
            settings.LOGOUT_URL='/index/onlineorder/'+str(admin_id)+'?prmcd='+promocodegeti
        #without minimum amount #withoutredeemlimit
            if couponlist.objects.filter(code=promocodegeti, is_consumable=False, is_active=True, is_withMinimumAmount=False): 
                if couponlist.objects.filter(couponname='KGDDeliveryFree', code=promocodegeti, is_consumable=False, is_active=True, is_withMinimumAmount=False):
                #if promocodegeti == "KGDDeliveryFree":
                    couponvalidity='KGDDeliveryFree'
                    couponvaliditymessage='Valid Coupon.'
                    discount='0'
                    rqrd_minimumamnt=0
                    prmcd='KGDDeliveryFree'
                else:
                    couponvalidity='Valid'
                    couponvaliditymessage='Valid'
                    discounti=couponlist.objects.get(code=promocodegeti)
                    discount=discounti.discountamount
                    rqrd_minimumamnt=0
                    prmcd=promocodegeti
            #without minimum amount #withredeemlimit
            elif couponlist.objects.filter(code=promocodegeti, is_consumable=True, is_active=True, is_withMinimumAmount=False).exclude(redeemlimit=0): 
                if couponlist.objects.filter(couponname='KGDDeliveryFree', code=promocodegeti, is_consumable=True, is_active=True, is_withMinimumAmount=False).exclude(redeemlimit=0):
                #if promocodegeti == "KGDDeliveryFree":
                    couponvalidity='KGDDeliveryFree'
                    couponvaliditymessage='Valid Coupon.'
                    discount='0'
                    rqrd_minimumamnt=0
                    prmcd=promocodegeti
                else:
                    couponvalidity='Valid'
                    couponvaliditymessage='Valid'
                    discounti=couponlist.objects.get(code=promocodegeti)
                    discount=discounti.discountamount
                    rqrd_minimumamnt=0
                    prmcd=promocodegeti
            #this coupon code has been consumed. #without minimum amount #withredeemlimit
            elif couponlist.objects.filter(code=promocodegeti, is_consumable=True, redeemlimit=0,is_active=True, is_withMinimumAmount=False): 
                couponvalidity='Invalid'
                couponvaliditymessage='This coupon code has reached maximum redeem limit.'
                discount='0'
                rqrd_minimumamnt=0
                prmcd=promocodegeti
            #this coupon code is inactive at this moment. #without minimum amount #withoutredeemlimit
            elif couponlist.objects.filter(code=promocodegeti, is_consumable=False, is_active=False, is_withMinimumAmount=False): 
                couponvalidity='Invalid'
                couponvaliditymessage='This coupon code is inactive at this moment.'
                discount='0'
                rqrd_minimumamnt=0
                prmcd=promocodegeti
            #this coupon code is inactive at this moment. #without minimum amount #withredeemlimit
            elif couponlist.objects.filter(code=promocodegeti, is_consumable=True, is_active=False, is_withMinimumAmount=False): 
                couponvalidity='Invalid'
                couponvaliditymessage='This coupon code is inactive at this moment.'
                discount='0'
                rqrd_minimumamnt=0
                prmcd=promocodegeti
            #with minimum amount #withoutredeemlimit
            elif couponlist.objects.filter(code=promocodegeti, is_consumable=False, is_active=True, is_withMinimumAmount=True): 
                if couponlist.objects.filter(couponname='KGDDeliveryFree', code=promocodegeti, is_consumable=False, is_active=True, is_withMinimumAmount=True):
                #if promocodegeti == "KGDDeliveryFree":
                    couponvalidity='KGDDeliveryFree'
                    couponvaliditymessage='Valid Coupon.'
                    discount='0'
                    rqrd_minimumamnti=couponlist.objects.get(code=promocodegeti)
                    rqrd_minimumamnt=rqrd_minimumamnti.MinimumAmount
                    prmcd=promocodegeti
                else:
                    couponvalidity='Valid'
                    couponvaliditymessage='Valid Coupon'
                    discounti=couponlist.objects.get(code=promocodegeti)
                    discount=discounti.discountamount
                    rqrd_minimumamnti=couponlist.objects.get(code=promocodegeti)
                    rqrd_minimumamnt=rqrd_minimumamnti.MinimumAmount
                    prmcd=promocodegeti
            #with minimum amount #withredeemlimit
            elif couponlist.objects.filter(code=promocodegeti, is_consumable=True, is_active=True, is_withMinimumAmount=True).exclude(redeemlimit=0): 
                if couponlist.objects.filter(couponname='KGDDeliveryFree', code=promocodegeti, is_consumable=True, is_active=True, is_withMinimumAmount=True).exclude(redeemlimit=0):
                #if promocodegeti == "KGDDeliveryFree":
                    couponvalidity='KGDDeliveryFree'
                    couponvaliditymessage='Valid Coupon.'
                    discount='0'
                    rqrd_minimumamnti=couponlist.objects.get(code=promocodegeti)
                    rqrd_minimumamnt=rqrd_minimumamnti.MinimumAmount
                    prmcd=promocodegeti
                else:
                    couponvalidity='Valid'
                    couponvaliditymessage='Valid Coupon'
                    discounti=couponlist.objects.get(code=promocodegeti)
                    discount=discounti.discountamount
                    rqrd_minimumamnti=couponlist.objects.get(code=promocodegeti)
                    rqrd_minimumamnt=rqrd_minimumamnti.MinimumAmount
                    prmcd=promocodegeti
            #this coupon code has been consumed. #with minimum amount
            elif couponlist.objects.filter(code=promocodegeti, is_consumable=True, redeemlimit=0, is_active=True, is_withMinimumAmount=True): 
                couponvalidity='Invalid'
                couponvaliditymessage='This coupon code has reached maximum redeem limit.'
                discount='0'
                rqrd_minimumamnt=0
                prmcd=promocodegeti
            #this coupon code is inactive at this moment. #with minimum amount #withoutredeemlimit
            elif couponlist.objects.filter(code=promocodegeti, is_consumable=False, is_active=False, is_withMinimumAmount=True): 
                couponvalidity='Invalid'
                couponvaliditymessage='This coupon code is inactive at this moment.'
                discount='0'
                rqrd_minimumamnt=0
                prmcd=promocodegeti
            #this coupon code is inactive at this moment. #with minimum amount #withredeemlimit
            elif couponlist.objects.filter(code=promocodegeti, is_consumable=True, is_active=False, is_withMinimumAmount=True): 
                couponvalidity='Invalid'
                couponvaliditymessage='This coupon code is inactive at this moment.'
                discount='0'
                rqrd_minimumamnt=0
                prmcd=promocodegeti

            #This coupon code is for testing.
            elif promocodegeti == "Testing123": 
                couponvalidity='Valid'
                couponvaliditymessage='This coupon code is for testing.'
                discount='0'
                rqrd_minimumamnt=0
                prmcd=promocodegeti
            #This coupon code is for testing.

            #this coupon code is invalid.
            else:
                couponvalidity='Invalid'
                couponvaliditymessage='This coupon code is invalid.'
                discount='0'
                rqrd_minimumamnt=0
                prmcd=promocodegeti
            print('couponvalidity:  ',couponvalidity)
        else:
            settings.LOGIN_REDIRECT_URL='/index/onlineorder/'+str(admin_id)
            settings.LOGIN_URL='/index/onlineorder/'+str(admin_id)
            settings.LOGOUT_URL='/index/onlineorder/'+str(admin_id)
            couponvalidity='No Coupon'
            couponvaliditymessage='No Coupon'
            discount='0'
            rqrd_minimumamnt=0
            prmcd='No Coupon'
            print('couponvalidity:  ',couponvalidity)
        print('QTY Sold for five months: ',Sales.objects.filter(user=4).aggregate(Sum('Qty')).get('Qty__sum'))
        userr=request.user.id
        username=request.user.username

        if request.user.is_anonymous:
            promoidentifier=''
        elif datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%A') == 'Friday' and user1.objects.filter(user__id=admin_id, Promo='Special Promo'):
            promoidentifier='FreeFriesDayandSpecialPromo'
        elif datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%A') == 'Friday':
            promoidentifier='FreeFriesDay'
        elif user1.objects.filter(user__id=admin_id, Promo='Special Promo'):
            promoidentifier='Special Promo'
        else:
            promoidentifier=''
        if is_ajax(request=request) and request.POST.get('username'):
            usernamess=json.loads(request.POST.get('username'))
            passwordss=json.loads(request.POST.get('password'))
            
            userss = authenticate(request, username=usernamess, password=passwordss)
            if userss is not None:
                login(request, userss)
            # Redirect to a success page.
                return JsonResponse({'reload':'success'})
            else:
                if User.objects.filter(username=usernamess):
                    usernamechecki='usernamechecktrue'
                else:
                    usernamechecki='usernamecheckfalse'
                usernamecheck=json.dumps(usernamechecki)
                # Return an 'invalid login' error message.
                return JsonResponse({'reload':usernamechecki})    
        
        if is_ajax(request=request) and request.POST.get('firstnameid'):
            firstnameid=json.loads(request.POST.get('firstnameid'))
            lastnameid=json.loads(request.POST.get('lastnameid'))
            emailid=json.loads(request.POST.get('emailid'))
            usernamesu=json.loads(request.POST.get('usernamesuid'))
            passwordsu=make_password(json.loads(request.POST.get('passwordsuid')))
            if User.objects.filter(first_name=firstnameid):
                firstnamechecker = 'notpass'
            else:
                firstnamechecker = 'pass'
            if User.objects.filter(last_name=lastnameid):
                lastnamechecker = 'pass'
            else:
                lastnamechecker = 'pass'
            if User.objects.filter(email=emailid):
                emailchecker = 'notpass'
            else:
                emailchecker = 'pass'
            if User.objects.filter(username=usernamesu):
                usernamesuchecker = 'notpass'
            else:
                usernamesuchecker = 'pass'
            if User.objects.filter(password=json.loads(request.POST.get('passwordsuid'))):
                passwordsuchecker = 'notpass'
            else:
                passwordsuchecker = 'pass'
            if firstnamechecker == 'pass' and lastnamechecker == 'pass' and emailchecker == 'pass' and usernamesuchecker == 'pass' and passwordsuchecker == 'pass':
                createnewaccount = User.objects.create(first_name=firstnameid,last_name=lastnameid,username=usernamesu,email=emailid,password=passwordsu)
                usersu = User.objects.get(first_name=firstnameid,last_name=lastnameid,username=usernamesu,email=emailid,password=passwordsu)
                login(request, usersu)
                print('usernamesu: ',usernamesu)
            # Redirect to a success page.
            context={
            'firstnameid':json.dumps(firstnamechecker),
            'lastnameid':json.dumps(lastnamechecker),
            'emailid':json.dumps(emailchecker),
            'usernamesu':json.dumps(usernamesuchecker),
            'passwordsu':json.dumps(passwordsuchecker)
            }
            return JsonResponse(context)

        if is_ajax(request=request) and request.POST.get('response.first_name'):
            first = json.loads(request.POST.get('response.first_name'))
            print(first)
            last = json.loads(request.POST.get('response.last_name'))
            print(last)
            short = json.loads((request.POST.get('response.short_name')).lower())
            print(short)
            uids=json.loads(request.POST.get('response.id'))
            responseresponse=json.loads(request.POST.get('response.response'))
            try:
                email=responseresponse.email
            except AttributeError:
                email=''
            if User.objects.filter(first_name=first, last_name=last):
                print('meron')
                createsocialaccounttwo = User.objects.filter(first_name=first,last_name=last,username=short)
                user=User.objects.get(first_name=first,last_name=last,username=short)
                socialaccountsslogin=login(request, user)
                if promocodegeti:
                    settings.LOGIN_REDIRECT_URL='/index/onlineorder/'+str(admin_id)+'?prmcd='+promocodegeti
                    settings.LOGIN_URL='/index/onlineorder/'+str(admin_id)+'?prmcd='+promocodegeti
                    settings.LOGOUT_URL='/index/onlineorder/'+str(admin_id)+'?prmcd='+promocodegeti
                else:
                    settings.LOGIN_URL='/index/onlineorder/'+str(admin_id)
                    settings.LOGOUT_URL='/index/onlineorder/'+str(admin_id)
                    settings.LOGIN_REDIRECT_URL='/index/onlineorder/'+str(admin_id)
                return JsonResponse({'reload':'reload'})
            else:
                print('none')
                if responseresponse['email']:
                    createsocialaccounttwo = User.objects.create(first_name=first,last_name=last,username=short,email=email)
                else:
                    createsocialaccounttwo = User.objects.create(first_name=first,last_name=last,username=short)
                user=User.objects.get(id=createsocialaccounttwo.id)
                createsocialaccount = SocialAccount.objects.create(user=user, provider='facebook', uid=uids, extra_data=responseresponse)
                authcreatedsocialaccount=login(request, user)

                if promocodegeti:
                    settings.LOGIN_REDIRECT_URL='/index/onlineorder/'+str(admin_id)+'?prmcd='+promocodegeti
                    settings.LOGIN_URL='/index/onlineorder/'+str(admin_id)+'?prmcd='+promocodegeti
                    settings.LOGOUT_URL='/index/onlineorder/'+str(admin_id)+'?prmcd='+promocodegeti
                else:
                    settings.LOGIN_URL='/index/onlineorder/'+str(admin_id)
                    settings.LOGOUT_URL='/index/onlineorder/'+str(admin_id)
                    settings.LOGIN_REDIRECT_URL='/index/onlineorder/'+str(admin_id)
                return JsonResponse({'reload':'reload'})
        if is_ajax(request=request) and request.GET.get('addressss'):
            userr=request.user.id
            username=request.user.username
            if request.user.first_name:
                firstname=request.user.first_name
                lastname=request.user.last_name
            elif request.user.is_anonymous:
                print('AnonymousUser')
                firstname=''
                lastname=''
            else:
                firstname=''
                lastname=''
            print(firstname)
            print(lastname)

            if Sales.objects.filter(CusName=firstname+' '+lastname).exclude(productname='DeliveryFee').exclude(MOP="Pickup").values_list('pinnedlat').distinct():
                counteruser=Sales.objects.filter(CusName=firstname+' '+lastname).exclude(productname='DeliveryFee').exclude(MOP="Pickup").distinct('pinnedlat').values_list('pinnedlat', flat=True)
                if len(counteruser) == 1 and counteruser[0] != None:
                    addressuseri = []
                    addressuserii = Sales.objects.filter(CusName=firstname+' '+lastname, pinnedlat__in=counteruser).exclude(productname='DeliveryFee').exclude(MOP="Pickup").first()
                    #addressuseri[0] = addressuserii
                    addressuseri.append(addressuserii)
                    addressuser = serializers.serialize('json',addressuseri, cls=JSONEncoder)
                    #addressuser=json.dumps(addressuseri, cls=JSONEncoder)
                    print('addressuser1:',addressuser)
                else:
                    addressuseri = []
                    i=0
                    while i<len(counteruser):
                        addressuserii=Sales.objects.filter(CusName=firstname+' '+lastname,pinnedlat=counteruser[i]).exclude(productname='DeliveryFee').exclude(MOP="Pickup").distinct().first()
                        addressuseri.append(addressuserii)
                    
                        i += 1
                    addressuser=serializers.serialize('json',addressuseri, cls=JSONEncoder)
                    #addressuser=json.dumps(addressuseri, cls=JSONEncoder)
                    print('addressuser2:',addressuser)
            else:
                addressuseri = Sales.objects.none()
                addressuser = serializers.serialize('json',addressuseri, cls=JSONEncoder)
                #addressuser=json.dumps(addressuseri, cls=JSONEncoder)
                print('addressuser3:',addressuser)
            return JsonResponse({'addressuser':addressuser})
        mtbuttons = user1.objects.filter(Category__Categorychoices='Milktea',user__id=admin_id).distinct('productname')
        mtsizes = Sizes.objects.all()
        Categoriess = Categories.objects.all()
        Subcategoriess = Subcategories.objects.all()
        frbuttons = user1.objects.filter(Category__Categorychoices='Frappe',user__id=admin_id).distinct('productname')
        frsizes = Sizes.objects.all().exclude(Sizechoices__exact='Small')
        psizes = PSizes.objects.all()
        freezebuttons = user1.objects.filter(Category__Categorychoices='Freeze',user__id=admin_id).distinct('productname')
        addonsbuttons = user1.objects.filter(Category__Categorychoices='Add-ons',user__id=admin_id).distinct('productname')
        cookiesbuttons = user1.objects.filter(Subcategory__Subcategorychoices='Cookies',user__id=admin_id).distinct('productname')
        friesbuttons = user1.objects.filter(Subcategory__Subcategorychoices='Fries',user__id=admin_id).distinct('productname')
        shawarmabuttons = user1.objects.filter(Subcategory__Subcategorychoices='Shawarma',user__id=admin_id).distinct('productname')
        bubwafbuttons = user1.objects.filter(Subcategory__Subcategorychoices='Bubble Waffle',user__id=admin_id).distinct('productname')
        pizzabuttons = user1.objects.filter(Subcategory__Subcategorychoices='Pizza',user__id=admin_id).distinct('productname')
        specialpromobuttons = user1.objects.filter(Category__Categorychoices='Promo',user__id=admin_id,Promo='Special Promo').distinct('productname')
        FreeFriespromobuttons = user1.objects.filter(Category__Categorychoices='Promo',user__id=admin_id,Promo='FreeFriesDay').distinct('productname')
        i=0
        pizzapricess={}
        pizzapricesii = user1.objects.filter(Subcategory__Subcategorychoices='Pizza',user__id=admin_id).values_list('Price',flat=True).order_by('-id')
        
        pizzaproductnameii=pizzapricesii.values_list('productname',flat=True)
        
        pizzasizeii=pizzapricesii.values_list('PSize__PSizechoices',flat=True)
        
        while i<pizzapricesii.count():
            pizzapricess[pizzaproductnameii[i]+pizzasizeii[i]]=pizzapricesii[i]

            i += 1
        pizzapricesss=pizzapricess
        
        pizzaall=json.dumps(pizzapricesss)
        snbuttons = user1.objects.filter(Category__Categorychoices='Snacks',user__id=admin_id)

        if request.GET.get('payment'):
            #arraypunchedii=json.dumps(request.GET.get('array'))
            arraypunchedi=json.loads(request.GET.get('array'))
            arraypunched=arraypunchedi
            changeefor=int(json.loads(request.GET.get('changefor') or '0'))
            print('arraypunched:',arraypunched)
            try:
                intorfloat = int(request.GET.get('totalwithdevfeename'))
                
            except ValueError:
                pass
            try:
                intorfloat = float(request.GET.get('totalwithdevfeename'))
                
            except ValueError:
                pass
            objs = [Customer(
                        Admin=admin_id,
                        Customername=request.GET.get('fullname'),
                        codecoupon=request.GET.get('getpromocodename') or None,
                        discount=request.GET.get('discount') or None,
                        Province=request.GET.get('Province'),
                        MunicipalityCity=request.GET.get('Municipality') or None,
                        Barangay=request.GET.get('barangay') or None,
                        StreetPurok=request.GET.get('street') or None,
                        Housenumber=request.GET.get('houseno') or None,
                        LandmarksnNotes=request.GET.get('notesmark') or None,
                        DeliveryFee=request.GET.get('devfeename') or 0,
                        contactnumber=request.GET.get('contactno'),
                        Bill=request.GET.get('changefor') or 0,
                        Change=(changeefor-(intorfloat or 0)),
                        productname=obj['productname'],
                        Category=obj['Category'],
                        Subcategory=obj['Subcategory'] or None,
                        Size=obj['Size'] or None,
                        PSize=obj['PSize'] or None,
                        Addons=obj['Addonsname'] or None,
                        QtyAddons=obj['Addonsqty'] or 0,
                        Price=user1.objects.filter(user__id=admin_id, productname=obj['productname'], PSize__PSizechoices=obj['PSize'] or None, Size__Sizechoices=obj['Size'] or None).values('Price')[0]['Price'] or 0,
                        Cost=user1.objects.filter(user__id=admin_id, productname=obj['productname'], PSize__PSizechoices=obj['PSize'] or None, Size__Sizechoices=obj['Size'] or None).values('Cost')[0]['Cost'] or 0,
                        Subtotal = obj['Subtotal'],
                        GSubtotal=intorfloat or 0,
                        Qty=obj['Qty'],
                        MOP=request.GET.get('payment'),
                        ordertype='Online',
                        Timetodeliver=request.GET.get('deliverytime') or None,
                        ScheduleTime=request.GET.get('schedtimename') or None,
                        gpslat = request.GET.get('gpslat') or None,
                        gpslng = request.GET.get('gpslng') or None,
                        gpsaccuracy = request.GET.get('gpsaccuracy') or None,
                        pinnedlat = request.GET.get('latitude') or None,
                        pinnedlng = request.GET.get('longitude') or None,
                        tokens = request.GET.get('tokens') or None,
                        DateTime=datetime.datetime.now(pytz.timezone('Asia/Singapore')),
                )
                for obj in arraypunched
            ]
            customerandorder = Customer.objects.bulk_create(objs)
            arraypunchedcounter=len(customerandorder)

            messages.success(request, "Your order has been submitted!")
            onlineorder = Customer.objects.filter(Admin=admin_id).distinct('contactnumber')
            submitted(request)
            if promocodegeti:
                return HttpResponseRedirect('/index/onlineorder/'+str(admin_id)+'/OrderProgress/?prmcd='+promocodegeti)
            else:
                return HttpResponseRedirect('/index/onlineorder/'+str(admin_id)+'/OrderProgress/')
        else:
            onlineorder = Customer.objects.none()
        viewordersi={}
        arrayone=[]
        contactdistincteri = Customer.objects.filter(Admin=userr).distinct('contactnumber')
        contactdistincter=contactdistincteri.values_list('contactnumber',flat=True)
        i=0
        for cndistinct in contactdistincter:
            arrayseparatoriii=Customer.objects.filter(Admin=userr,contactnumber=cndistinct)
            arrayseparator = list(arrayseparatoriii)
            arrayone.append(arrayseparator)
            viewordersi[contactdistincter[i]]=arrayone[i]
            i=i+1
        if promocodegeti:
            settings.LOGIN_REDIRECT_URL='/index/onlineorder/'+str(admin_id)+'?prmcd='+promocodegeti
            settings.LOGIN_URL='/index/onlineorder/'+str(admin_id)+'?prmcd='+promocodegeti
            settings.LOGOUT_URL='/index/onlineorder/'+str(admin_id)+'?prmcd='+promocodegeti
        else:
            settings.LOGIN_URL='/index/onlineorder/'+str(admin_id)
            settings.LOGOUT_URL='/index/onlineorder/'+str(admin_id)
            settings.LOGIN_REDIRECT_URL='/index/onlineorder/'+str(admin_id)
        #vieworders=json.dumps(viewordersi)
        #print('vieworders: ',vieworders)
        return render(request, 'Onlineorder.html',{'prmcd':prmcd,'rqrd_minimumamnt':rqrd_minimumamnt,'discount':discount,'couponvaliditymessage':couponvaliditymessage,'couponvalidity':couponvalidity,'promoidentifier':promoidentifier,'FreeFriespromobuttons':FreeFriespromobuttons,'admin_id':admin_id,'onlineorder':onlineorder,'pizzaall':pizzaall,'snbuttons':snbuttons,'pizzabuttons':pizzabuttons,'bubwafbuttons':bubwafbuttons,'shawarmabuttons':shawarmabuttons,'friesbuttons':friesbuttons,'cookiesbuttons':cookiesbuttons,'addonsbuttons':addonsbuttons,'freezebuttons':freezebuttons,'specialpromobuttons':specialpromobuttons,'frsizes':frsizes,'frbuttons':frbuttons,'Subcategoriess':Subcategoriess,'Categoriess':Categoriess,'mtsizes':mtsizes,'mtbuttons':mtbuttons})

def orderprogress(request, admin_id):
        promocodegeti=request.GET.get('prmcd', '')
        completenamei=request.GET.get('progressuser', '')
        userr=request.user.id
        print('userr:',userr)
        print('completenamei:',completenamei)
        if userr:
            #firstname=request.user.first_name
            #lastname=request.user.last_name
            completename=request.user.first_name+' '+request.user.last_name
        elif completenamei:
            completename=completenamei
        else:
            completename=''
            #firstname=''
            #lastname=''
        
        if is_ajax(request=request) and request.GET.get('progressETA'):
            completenamefinali=json.loads(request.GET.get('completename') or '')
            completenamefinal=completenamefinali.replace('_', ' ')
            print('completenamefinal:',completenamefinal)
            if Acceptorder.objects.filter(Admin=admin_id, Customername=completenamefinal):
                ETAi=Acceptorder.objects.filter(Admin=admin_id, Customername=completenamefinal).values_list('ETA', flat=True).first()
            else:
                ETAi=list(Acceptorder.objects.none())

            ETA=json.dumps(ETAi, cls=JSONEncoder)
            datetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
            monthtoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m')
            yeartoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y')
            if Acceptorder.objects.filter(Admin=admin_id, Customername=completenamefinal).exclude(productname='Ready'):
                vieworderscustomeri = Acceptorder.objects.filter(Admin=admin_id, Customername=completenamefinal).exclude(productname='Ready')
            elif Customer.objects.filter(Admin=admin_id, Customername=completenamefinal).exclude(productname='Ready'):
                vieworderscustomeri = Customer.objects.filter(Admin=admin_id, Customername=completenamefinal)
            elif Sales.objects.filter(DateTime__day=datetoday, DateTime__month=monthtoday, DateTime__year=yeartoday, CusName=completenamefinal):
                vieworderscustomeri = Sales.objects.filter(DateTime__day=datetoday, DateTime__month=monthtoday, DateTime__year=yeartoday, CusName=completenamefinal).exclude(productname='DeliveryFee')
            else:
                vieworderscustomeri = Customer.objects.none()
            vieworderscustomer=serializers.serialize('json',vieworderscustomeri, cls=JSONEncoder)
            print('admin_id: ', admin_id)
            if Customer.objects.filter(Admin=admin_id, Customername=completenamefinal):
                progressi='zero'
            elif Acceptorder.objects.filter(Admin=admin_id, Customername=completenamefinal):
                if Acceptorder.objects.filter(Admin=admin_id, Customername=completenamefinal, productname='Ready'):
                    progressi='seventyfive'
                else:
                    progressi='twentyfive'
            elif Sales.objects.filter(DateTime__day=datetoday, DateTime__month=monthtoday, DateTime__year=yeartoday, CusName=completenamefinal):
                progressi='onehundred'
            else:
                progressi='wala'
            print(progressi)
            progress=json.dumps(progressi, cls=JSONEncoder )
            if Rejectorder.objects.filter(Admin=admin_id,DateTime__day=datetoday, DateTime__month=monthtoday, DateTime__year=yeartoday, Customername=completenamefinal):
                TrueFalsei='Rejected'
            else:
                TrueFalsei='NotRejected'
            TrueFalse=json.dumps(TrueFalsei, cls=JSONEncoder )
            context={
            'progress':progress,
            'ETA':ETA,
            'vieworderscustomer':vieworderscustomer,
            'Reject':TrueFalse,
            }
            return JsonResponse(context)
        return render(request, 'orderprogress.html',{'completename':completename,'promocodegeti':promocodegeti,'admin_id':admin_id})

@login_required
def saletoday(request):
    userr=request.user.id
    if request.GET.get('acceptcontactno'):
        contactnumberaccept = request.GET.get('acceptcontactno')
        rider = request.GET.get('rider')
        getETA = request.GET.get('ETA')
        Accepted = Customer.objects.filter(Admin=userr,contactnumber=contactnumberaccept)
            
        objs = [Acceptorder(
                    Admin=Accepted.Admin,
                    Customername=Accepted.Customername,
                    codecoupon=Accepted.codecoupon,
                    discount=Accepted.discount or None,
                    Province=Accepted.Province,
                    MunicipalityCity=Accepted.MunicipalityCity,
                    Barangay=Accepted.Barangay,
                    StreetPurok=Accepted.StreetPurok,
                    Housenumber=Accepted.Housenumber or None,
                    LandmarksnNotes=Accepted.LandmarksnNotes or None,
                    DeliveryFee=Accepted.DeliveryFee or 0,
                    contactnumber=Accepted.contactnumber,
                    Rider=rider,
                    productname=Accepted.productname,
                    Category=Accepted.Category,
                    Subcategory=Accepted.Subcategory or None,
                    Size=Accepted.Size  or None,
                    PSize=Accepted.PSize or None,
                    Addons=Accepted.Addons or None,
                    QtyAddons= Accepted.QtyAddons or 0,
                    Price=Accepted.Price,
                    Subtotal = Accepted.Subtotal,
                    GSubtotal=Accepted.GSubtotal,
                    Cost=Accepted.Cost,
                    Qty=Accepted.Qty,
                    Bill=Accepted.Bill or 0,
                    Change=Accepted.Change or 0,
                    ETA=getETA,
                    MOP=Accepted.MOP,
                    ordertype='Online',
                    Timetodeliver=Accepted.Timetodeliver,
                    ScheduleTime=Accepted.ScheduleTime,
                    gpslat = Accepted.gpslat,
                    gpslng = Accepted.gpslng,
                    gpsaccuracy = Accepted.gpsaccuracy,
                    pinnedlat = Accepted.pinnedlat,
                    pinnedlng = Accepted.pinnedlng,
                            
                    tokens = Accepted.tokens or None,
                    DateTime=Accepted.DateTime,
            )
            for Accepted in Accepted
        ]
        Acceptorders = Acceptorder.objects.bulk_create(objs)
        Accepted.delete()
        messageacknowledgetokeni=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberaccept).values_list('tokens',flat=True).first()
        messageacknowledgetoken = ["dHEGNR4YGO8a-AVQWfIE33:APA91bGkNxUcRZEHJQCkUy3k3THUEMxml9q4819bDQw1b8UkD05qThidgXq3Nnr46I1pwQikZgwiGFuBgKwUxHO6kUXI9KId3ZK0fQ0zi83QegTtVimqV18a2pDqBq5qnJf-BK74Z1nL", messageacknowledgetokeni]
        acknowledge(request, messageacknowledgetoken)
        MessageRider(request)
        return HttpResponseRedirect('/index/pos')

    if len(Acceptorder.objects.filter(Admin=userr))>0:
        acceptedorder = Acceptorder.objects.filter(Admin=userr).distinct('contactnumber')
        acceptedorderall = Acceptorder.objects.filter(Admin=userr)
    else:
        acceptedorder = Acceptorder.objects.none()
        acceptedorderall = Acceptorder.objects.none()
    viewordersacceptii={}
    arrayoneaccept=[]
    contactdistincteraccepti = Acceptorder.objects.filter(Admin=userr).distinct('contactnumber')
    contactdistincteraccept=contactdistincteraccepti.values_list('contactnumber',flat=True)
    i=0
    for cndistinctaccept in contactdistincteraccept:
        arrayseparatoracceptiii=Acceptorder.objects.filter(Admin=userr,contactnumber=cndistinctaccept).exclude(productname='Ready').values()
        arrayseparatoraccepti = list(arrayseparatoracceptiii)
        arrayseparatoraccept=json.dumps(arrayseparatoraccepti, cls=JSONEncoder)
        viewordersacceptii[contactdistincteraccept[i]]=arrayseparatoraccept
        i=i+1
    viewordersaccepti=viewordersacceptii
    viewordersaccept=json.dumps(viewordersaccepti, cls=JSONEncoder)
        

    if (request.GET.get('rider') == "") and (request.GET.get('contactnoreject') or request.GET.get('contactnoaccepted')):
        if request.GET.get('contactnoreject'):
            contactnumberreject = request.GET.get('contactnoreject')
            Rejected = Customer.objects.filter(Admin=userr,contactnumber=contactnumberreject)
        elif request.GET.get('contactnoaccepted'):
            contactnumberreject = request.GET.get('contactnoaccepted')
            if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject, productname='Ready'):
                deletethis=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject, productname='Ready')
                deletethis.delete()
            Rejected = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject)
            
        objs = [Rejectorder(
                    Admin=userr,
                    Customername=Rejected.Customername,
                    codecoupon=Rejected.codecoupon,
                    discount=Rejected.discount or None,
                    Province=Rejected.Province,
                    MunicipalityCity=Rejected.MunicipalityCity,
                    Barangay=Rejected.Barangay,
                    StreetPurok=Rejected.StreetPurok,
                    Housenumber=Rejected.Housenumber or None,
                    LandmarksnNotes=Rejected.LandmarksnNotes or None,
                    DeliveryFee=Rejected.DeliveryFee or 0,
                    contactnumber=Rejected.contactnumber,
                    productname=Rejected.productname,
                    Category=Rejected.Category,
                    Subcategory=Rejected.Subcategory or None,
                    Size=Rejected.Size  or None,
                    PSize=Rejected.PSize or None,
                    Addons=Rejected.Addons or None,
                    QtyAddons= Rejected.QtyAddons or 0,
                    Price=Rejected.Price,
                    Subtotal = Rejected.Subtotal,
                    GSubtotal=Rejected.GSubtotal,
                    Cost=Rejected.Cost,
                    Qty=Rejected.Qty,
                    Bill=Rejected.Bill or 0,
                    Change=Rejected.Change or 0,
                    MOP=Rejected.MOP,
                    ordertype='Online',
                    Timetodeliver=Rejected.Timetodeliver,
                    ScheduleTime=Rejected.ScheduleTime,
                    gpslat = Rejected.gpslat,
                    gpslng = Rejected.gpslng,
                    gpsaccuracy = Rejected.gpsaccuracy,
                    pinnedlat = Rejected.pinnedlat,
                    pinnedlng = Rejected.pinnedlng,
                            
                    tokens = Rejected.tokens  or None,
                    DateTime=Rejected.DateTime,
            )
            for Rejected in Rejected
        ]
        Rejectorders = Rejectorder.objects.bulk_create(objs)
        Rejected.delete()
        return HttpResponseRedirect('/index/pos')

    if len(Rejectorder.objects.filter(Admin=userr))>0:
        rejectedorder = Rejectorder.objects.filter(Admin=userr).distinct('contactnumber')
        rejectedorderall = Rejectorder.objects.filter(Admin=userr)
    else:
        rejectedorder = Rejectorder.objects.none()
        rejectedorderall = Rejectorder.objects.none()
    viewordersrejectii={}
    arrayonereject=[]
    contactdistincterrejecti = Rejectorder.objects.filter(Admin=userr).distinct('contactnumber')
    contactdistincterreject=contactdistincterrejecti.values_list('contactnumber',flat=True)
    i=0
    for cndistinctreject in contactdistincterreject:
        arrayseparatorrejectiii=Rejectorder.objects.filter(Admin=userr,contactnumber=cndistinctreject).exclude(productname='Ready').values()
        arrayseparatorrejecti = list(arrayseparatorrejectiii)
        arrayseparatorreject=json.dumps(arrayseparatorrejecti, cls=JSONEncoder)
        viewordersrejectii[contactdistincterreject[i]]=arrayseparatorreject
        i=i+1
    viewordersrejecti=viewordersrejectii
    viewordersreject=json.dumps(viewordersrejecti, cls=JSONEncoder)

        

    if request.GET.get('contactnorestore'):
        contactnumberrestore = request.GET.get('contactnorestore')
        Restored = Rejectorder.objects.filter(Admin=userr,contactnumber=contactnumberrestore)
            
        objs = [Customer(
                    Admin=userr,
                    Customername=Restored.Customername,
                    codecoupon=Restored.codecoupon,
                    discount=Restored.discount or None,
                    Province=Restored.Province,
                    MunicipalityCity=Restored.MunicipalityCity,
                    Barangay=Restored.Barangay,
                    StreetPurok=Restored.StreetPurok,
                    Housenumber=Restored.Housenumber or None,
                    LandmarksnNotes=Restored.LandmarksnNotes or None,
                    DeliveryFee=Restored.DeliveryFee or 0,
                    contactnumber=Restored.contactnumber,
                    productname=Restored.productname,
                    Category=Restored.Category,
                    Subcategory=Restored.Subcategory or None,
                    Size=Restored.Size  or None,
                    PSize=Restored.PSize or None,
                    Addons=Restored.Addons or None,
                    QtyAddons= Restored.QtyAddons or 0,
                    Price=Restored.Price,
                    Subtotal = Restored.Subtotal,
                    GSubtotal=Restored.GSubtotal,
                    Cost=Restored.Cost,
                    Qty=Restored.Qty,
                    Bill=Restored.Bill or 0,
                    Change=Restored.Change or 0,
                    MOP=Restored.MOP,
                    ordertype='Online',
                    Timetodeliver=Restored.Timetodeliver,
                    ScheduleTime=Restored.ScheduleTime,
                    gpslat = Restored.gpslat,
                    gpslng = Restored.gpslng,
                    gpsaccuracy = Restored.gpsaccuracy,
                    pinnedlat = Restored.pinnedlat,
                    pinnedlng = Restored.pinnedlng,
                          
                    tokens = Restored.tokens  or None,
                    DateTime=Restored.DateTime,
            )
            for Restored in Restored
        ]
        Restore = Customer.objects.bulk_create(objs)
        Restored.delete()
        return HttpResponseRedirect('/index/pos')

    if len(Customer.objects.filter(Admin=userr))>0:
        onlineorder = Customer.objects.filter(Admin=userr).distinct('contactnumber')
        onlineorderall = Customer.objects.filter(Admin=userr)
    else:
        onlineorder = Customer.objects.none()
        onlineorderall = Customer.objects.none()
    viewordersii={}
    arrayone=[]
    contactdistincteri = Customer.objects.filter(Admin=userr).distinct('contactnumber')
    contactdistincter=contactdistincteri.values_list('contactnumber',flat=True)
    i=0
    for cndistinct in contactdistincter:  
        arrayseparatoriii=Customer.objects.filter(Admin=userr,contactnumber=cndistinct).values()
        arrayseparatori = list(arrayseparatoriii)
        arrayseparator=json.dumps(arrayseparatori, cls=JSONEncoder)
        viewordersii[contactdistincter[i]]=arrayseparator
        i=i+1
    viewordersi=viewordersii
    vieworders=json.dumps(viewordersi, cls=JSONEncoder)

    onlineordercounter = len(Customer.objects.filter(Admin=userr).distinct('contactnumber'))

    if is_ajax(request=request) and request.POST.get("Ready"):
        contactnumberready = request.POST.get('Ready')
        Readyadd = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).first()
        Readyacceptorder=Acceptorder.objects.create(
                    Admin=userr,
                    Customername=Readyadd.Customername,
                    codecoupon=Readyadd.codecoupon,
                    discount=Readyadd.discount or None,
                    Province=Readyadd.Province,
                    MunicipalityCity=Readyadd.MunicipalityCity,
                    Barangay=Readyadd.Barangay,
                    StreetPurok=Readyadd.StreetPurok,
                    Housenumber=Readyadd.Housenumber or None,
                    LandmarksnNotes=Readyadd.LandmarksnNotes or None,
                    DeliveryFee=0,
                    contactnumber=Readyadd.contactnumber,
                    productname='Ready',
                    Category=Readyadd.Category,
                    Subcategory=None,
                    Size=None,
                    PSize=None,
                    Addons=None,
                    QtyAddons= 0,
                    Price=0,
                    Subtotal = 0,
                    GSubtotal=Readyadd.GSubtotal,
                    Cost=0,
                    Qty=0,
                    Bill=Readyadd.Bill or 0,
                    Change=Readyadd.Change or 0,
                    MOP=Readyadd.MOP,
                    ordertype='Online',
                    Timetodeliver=Readyadd.Timetodeliver,
                    ScheduleTime=Readyadd.ScheduleTime,
                    gpslat = Readyadd.gpslat,
                    gpslng = Readyadd.gpslng,
                    gpsaccuracy = Readyadd.gpsaccuracy,
                    pinnedlat = Readyadd.pinnedlat,
                    pinnedlng = Readyadd.pinnedlng,
                            
                    tokens = Readyadd.tokens  or None,
                    DateTime=Readyadd.DateTime,
                    )
        Readyacceptorder.save()
        if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready, MOP='COD'):
            orderprepared(request)
        messageacknowledgetokeni=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('tokens',flat=True).first()
        messageacknowledgetoken = ["dHEGNR4YGO8a-AVQWfIE33:APA91bGkNxUcRZEHJQCkUy3k3THUEMxml9q4819bDQw1b8UkD05qThidgXq3Nnr46I1pwQikZgwiGFuBgKwUxHO6kUXI9KId3ZK0fQ0zi83QegTtVimqV18a2pDqBq5qnJf-BK74Z1nL", messageacknowledgetokeni]
        if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('MOP',flat=True).first() == 'COD' or Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('MOP',flat=True).first() == 'GcashDelivery':
            deliveryotwRider(request)
            deliveryotwCustomer(request , messageacknowledgetoken)
        else:
            pickupCustomer(request , messageacknowledgetoken)
        return JsonResponse({'Ready':'Ready'})
    if is_ajax(request=request) and request.GET.get("apini"):
        onlineordercounterf = onlineordercounter
        onlineorderf = [serializers.serialize('json',onlineorder, cls=JSONEncoder),vieworders]
        return JsonResponse({'onlineorderf':onlineorderf})
            
    if is_ajax(request=request) and request.POST.get('doneorders'):
        contactnumberdonei = json.loads(request.POST.get('doneorders'))
        contactnumberdone = contactnumberdonei[0]['contactnumber']
        if contactnumberdonei[0]['codecoupon']:
            if couponlist.objects.filter(code=contactnumberdonei[0]['codecoupon']):
                codeconsumereducerii=couponlist.objects.get(code=contactnumberdonei[0]['codecoupon'])
                if codeconsumereducerii.is_consumable == True and codeconsumereducerii.redeemlimit>0:
                    codeconsumereduceri=int(codeconsumereducerii.redeemlimit)-1
                    codeconsumereducer=couponlist.objects.filter(code=contactnumberdonei[0]['codecoupon']).update(redeemlimit=codeconsumereduceri)
                else:
                    pass
            else:
                pass
        else:
            pass
        if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone, productname='Ready'):
            deletethis=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone, productname='Ready')
            deletethis.delete()
        Done = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone)
        try:
            Sales.objects.filter(contactnumber=contactnumberdonei[0]['contactnumber'], CusName=contactnumberdonei[0]['Customername'], productname='DeliveryFee', DateTime=contactnumberdonei[0]['DateTime'])
            deliveryfeepaid='true'
        except Sales.DoesNotExist:
            deliveryfeepaid='false'
        if contactnumberdonei[0]['DeliveryFee'] != None and deliveryfeepaid == 'true':
            devfeeassales=Sales.objects.create(
                    user=userr,
                    CusName=contactnumberdonei[0]['Customername'],
                    codecoupon=contactnumberdonei[0]['codecoupon'] or None,
                    discount=contactnumberdonei[0]['discount'] or None,
                    Province=contactnumberdonei[0]['Province'],
                    MunicipalityCity=contactnumberdonei[0]['MunicipalityCity'],
                    Barangay=contactnumberdonei[0]['Barangay'],
                    StreetPurok=contactnumberdonei[0]['StreetPurok'],
                    Housenumber=contactnumberdonei[0]['Housenumber'] or None,
                    LandmarksnNotes=contactnumberdonei[0]['LandmarksnNotes'] or None,
                    DeliveryFee=contactnumberdonei[0]['DeliveryFee'] or None,
                    contactnumber=contactnumberdonei[0]['contactnumber'],
                    productname='DeliveryFee',
                    Category='DeliveryFee',
                    Subcategory='DeliveryFee',
                    Size=None,
                    PSize=None,
                    Addons=None,
                    QtyAddons=0,
                    Price=contactnumberdonei[0]['DeliveryFee'],
                    Subtotal = contactnumberdonei[0]['DeliveryFee'],
                    GSubtotal=contactnumberdonei[0]['GSubtotal'],
                    Cost=0,
                    Qty=1,
                    Bill=contactnumberdonei[0]['Bill'] or 0,
                    Change=contactnumberdonei[0]['Change'] or 0,
                    MOP=contactnumberdonei[0]['MOP'],
                    ordertype='Online',
                    Timetodeliver=contactnumberdonei[0]['Timetodeliver'] or None,
                    ScheduleTime=contactnumberdonei[0]['ScheduleTime'] or None,
                    gpslat = contactnumberdonei[0]['gpslat'],
                    gpslng = contactnumberdonei[0]['gpslng'],
                    gpsaccuracy = contactnumberdonei[0]['gpsaccuracy'],
                    pinnedlat = contactnumberdonei[0]['pinnedlat'],
                    pinnedlng = contactnumberdonei[0]['pinnedlng'],    
                    tokens = contactnumberdonei[0]['tokens'] or None,
                    DateTime=contactnumberdonei[0]['DateTime'],
            )
            devfeeassales.save()
        if contactnumberdonei[0]['discount']:
            objs = [Sales(
                        user=userr,
                        CusName=Done.Customername,
                        codecoupon=Done.codecoupon,
                        discount=Done.discount or None,
                        Province=Done.Province,
                        MunicipalityCity=Done.MunicipalityCity,
                        Barangay=Done.Barangay,
                        StreetPurok=Done.StreetPurok,
                        Housenumber=Done.Housenumber or None,
                        LandmarksnNotes=Done.LandmarksnNotes or None,
                        DeliveryFee=Done.DeliveryFee or None,
                        contactnumber=Done.contactnumber,
                        productname=Done.productname,
                        Category=Done.Category,
                        Subcategory=Done.Subcategory or None,
                        Size=Done.Size  or None,
                        PSize=Done.PSize or None,
                        Addons=Done.Addons or None,
                        QtyAddons= Done.QtyAddons or 0,
                        Price=Done.Price,
                        Subtotal = Done.Subtotal-((Done.Subtotal)*(Decimal(int(Done.discount)/100))),
                        GSubtotal=Done.GSubtotal,
                        Cost=Done.Cost,
                        Qty=Done.Qty,
                        Bill=Done.Bill or 0,
                        Change=Done.Change or 0,
                        MOP=Done.MOP,
                        ordertype='Online',
                        Timetodeliver=Done.Timetodeliver,
                        ScheduleTime=Done.ScheduleTime,
                        gpslat = Done.gpslat,
                        gpslng = Done.gpslng,
                        gpsaccuracy = Done.gpsaccuracy,
                        pinnedlat = Done.pinnedlat,
                        pinnedlng = Done.pinnedlng,
                        tokens = Done.tokens or None,
                        DateTime=Done.DateTime,
                )
                for Done in Done
            ]
        else:
            objs = [Sales(
                        user=userr,
                        CusName=Done.Customername,
                        codecoupon=Done.codecoupon,
                        discount=Done.discount or None,
                        Province=Done.Province,
                        MunicipalityCity=Done.MunicipalityCity,
                        Barangay=Done.Barangay,
                        StreetPurok=Done.StreetPurok,
                        Housenumber=Done.Housenumber or None,
                        LandmarksnNotes=Done.LandmarksnNotes or None,
                        DeliveryFee=Done.DeliveryFee or None,
                        contactnumber=Done.contactnumber,
                        productname=Done.productname,
                        Category=Done.Category,
                        Subcategory=Done.Subcategory or None,
                        Size=Done.Size  or None,
                        PSize=Done.PSize or None,
                        Addons=Done.Addons or None,
                        QtyAddons= Done.QtyAddons or 0,
                        Price=Done.Price,
                        Subtotal = Done.Subtotal,
                        GSubtotal=Done.GSubtotal,
                        Cost=Done.Cost,
                        Qty=Done.Qty,
                        Bill=Done.Bill or 0,
                        Change=Done.Change or 0,
                        MOP=Done.MOP,
                        ordertype='Online',
                        Timetodeliver=Done.Timetodeliver,
                        ScheduleTime=Done.ScheduleTime,
                        gpslat = Done.gpslat,
                        gpslng = Done.gpslng,
                        gpsaccuracy = Done.gpsaccuracy,
                        pinnedlat = Done.pinnedlat,
                        pinnedlng = Done.pinnedlng,
                        tokens = Done.tokens or None,
                        DateTime=Done.DateTime,
                )
                for Done in Done
            ]
        Salesorders = Sales.objects.bulk_create(objs)
        Done.delete()

    ####### BASE Order from website ####
    notifyorder=acknowledgedstockorder.objects.filter(CusName="Notify",user=userr).count()
    if acknowledgedstockorder.objects.all().count()==0:
        notifyadmin=submitstockorder.objects.all().count()
    else:
        notifyadmin=0
    print('userr:',userr) 
    if punchedprod.objects.filter(user=userr).count()==0:
        punchedtotal=0
    else:
        punchedtotal=punchedprod.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
    if acknowledgedstockorder.objects.all().count()==0:
        notifyadmin=submitstockorder.objects.all().count()
    else:
        notifyadmin=0
    if is_ajax(request=request) and request.POST.get("list"):
        datetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
        monthtoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m')
        yeartoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y')
        print('timezone: ',timezone.now())
        print('datetime: ',datetime.datetime.now(pytz.timezone('Asia/Singapore')))
        try:
            saletodayi=Sales.objects.filter(user=userr,DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).exclude(Categoryaes__saecatchoices="Expenses").exclude(Categoryaes__saecatchoices="Stock").order_by('DateTime')
            saletoday=serializers.serialize('json',saletodayi, cls=JSONEncoder)
        except Sales.DoesNotExist:
            saletodayi=Sales.objects.none()
            saletoday=serializers.serialize('json',saletodayi, cls=JSONEncoder)
        milkteaRegproductnames=user1.objects.filter(user__id=userr,Category__Categorychoices='Milktea',Size__Sizechoices='Reg').values_list('productname',flat=True)
        i=0
        milkteaRegbd={}
        while i<milkteaRegproductnames.count():
            try:
                milkteaRegbdcount=0
                milkteaRegbdcountii=Sales.objects.filter(user=userr,productname=milkteaRegproductnames[i],Category='Milktea',Size='Reg',DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Qty').aggregate(Sum('Qty')).get('Qty__sum')
                if milkteaRegbdcountii:
                    milkteaRegbdcounti=milkteaRegbdcountii
                else:
                    milkteaRegbdcounti=0
                milkteaRegbdcount=milkteaRegbdcount+milkteaRegbdcounti
            except Sales.DoesNotExist:
                milkteaRegbdcount=0
            milkteaRegbd[str(milkteaRegproductnames[i])]=str(milkteaRegbdcount)
            i+=1


        milkteaFullproductnames=user1.objects.filter(user__id=userr,Category__Categorychoices='Milktea',Size__Sizechoices='Full').values_list('productname',flat=True)
        ii=0
        milkteaFullbd={}
        while ii<milkteaFullproductnames.count():
            try:
                milkteaFullbdcount=0
                milkteaFullbdcountii=Sales.objects.filter(user=userr,productname=milkteaFullproductnames[ii],Category='Milktea',Size='Full',DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Qty').aggregate(Sum('Qty')).get('Qty__sum')
                if milkteaFullbdcountii:
                    milkteaFullbdcounti=milkteaFullbdcountii
                else:
                    milkteaFullbdcounti=0

                milkteaFullbdcount=milkteaFullbdcount+milkteaFullbdcounti
            except Sales.DoesNotExist:
                milkteaFullbdcount=0
            milkteaFullbd[str(milkteaFullproductnames[ii])]=str(milkteaFullbdcount)
            ii+=1


        milkteaSmallproductnames=user1.objects.filter(user__id=userr,Category__Categorychoices='Milktea',Size__Sizechoices='Small').values_list('productname',flat=True)
        iii=0
        milkteaSmallbd={}
        while iii<milkteaSmallproductnames.count():
            try:
                milkteaSmallbdcount=0
                milkteaSmallbdcountii=Sales.objects.filter(user=userr,productname=milkteaSmallproductnames[iii],Category='Milktea',Size='Small',DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Qty').aggregate(Sum('Qty')).get('Qty__sum')
                if milkteaSmallbdcountii:
                    milkteaSmallbdcounti=milkteaSmallbdcountii
                else:
                    milkteaSmallbdcounti=0

                milkteaSmallbdcount=milkteaSmallbdcount+milkteaSmallbdcounti
            except Sales.DoesNotExist:
                milkteaSmallbdcount=0
            milkteaSmallbd[str(milkteaSmallproductnames[iii])]=str(milkteaSmallbdcount)
            iii+=1
        print('milkteaSmallbd:',milkteaSmallbd)
        print('milkteaSmallproductnames: ',list(milkteaSmallproductnames))

        MilkteaFinalBD={}
        MilkteaFinalBD['milkteaSmallbd']=milkteaSmallbd
        MilkteaFinalBD['milkteaFullproductnames']=list(milkteaFullproductnames)
        MilkteaFinalBD['milkteaRegbd']=milkteaRegbd
        MilkteaFinalBD['milkteaFullbd']=milkteaFullbd




        frappeRegproductnames=user1.objects.filter(user__id=userr,Category__Categorychoices='Frappe',Size__Sizechoices='Reg').values_list('productname',flat=True)
        ifr=0
        frappeRegbd={}
        while ifr<frappeRegproductnames.count():
            try:
                frappeRegbdcount=0
                frappeRegbdcountii=Sales.objects.filter(user=userr,productname=frappeRegproductnames[ifr],Category='Frappe',Size='Reg',DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Qty').aggregate(Sum('Qty')).get('Qty__sum')
                if frappeRegbdcountii:
                    frappeRegbdcounti=frappeRegbdcountii
                else:
                    frappeRegbdcounti=0
                frappeRegbdcount=frappeRegbdcount+frappeRegbdcounti
            except Sales.DoesNotExist:
                frappeRegbdcount=0
            frappeRegbd[str(frappeRegproductnames[ifr])]=str(frappeRegbdcount)
            ifr+=1


        frappeFullproductnames=user1.objects.filter(user__id=userr,Category__Categorychoices='Frappe',Size__Sizechoices='Full').values_list('productname',flat=True)
        iifr=0
        frappeFullbd={}
        while iifr<frappeFullproductnames.count():
            try:
                frappeFullbdcount=0
                frappeFullbdcountii=Sales.objects.filter(user=userr,productname=frappeFullproductnames[iifr],Category='Frappe',Size='Full',DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Qty').aggregate(Sum('Qty')).get('Qty__sum')
                if frappeFullbdcountii:
                    frappeFullbdcounti=frappeFullbdcountii
                else:
                    frappeFullbdcounti=0

                frappeFullbdcount=frappeFullbdcount+frappeFullbdcounti
            except Sales.DoesNotExist:
                frappeFullbdcount=0
            frappeFullbd[str(frappeFullproductnames[iifr])]=str(frappeFullbdcount)
            iifr+=1



        FrappeFinalBD={}
        FrappeFinalBD['frappeFullproductnames']=list(frappeFullproductnames)
        FrappeFinalBD['frappeRegbd']=frappeRegbd
        FrappeFinalBD['frappeFullbd']=frappeFullbd




        pizzaBarkadaproductnames=user1.objects.filter(user__id=userr,Subcategory__Subcategorychoices='Pizza',PSize__PSizechoices='Barkada(10")').values_list('productname',flat=True)
        ip=0
        pizzaBarkadabd={}
        while ip<pizzaBarkadaproductnames.count():
            try:
                pizzaBarkadabdcount=0
                pizzaBarkadabdcountii=Sales.objects.filter(user=userr,productname=pizzaBarkadaproductnames[ip],Subcategory='Pizza',PSize='Barkada(10")',DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Qty').aggregate(Sum('Qty')).get('Qty__sum')
                if pizzaBarkadabdcountii:
                    pizzaBarkadabdcounti=pizzaBarkadabdcountii
                else:
                    pizzaBarkadabdcounti=0
                pizzaBarkadabdcount=pizzaBarkadabdcount+pizzaBarkadabdcounti
            except Sales.DoesNotExist:
                pizzaBarkadabdcount=0
            pizzaBarkadabd[str(pizzaBarkadaproductnames[ip])]=str(pizzaBarkadabdcount)
            ip+=1


        pizzaPamilyaproductnames=user1.objects.filter(user__id=userr,Subcategory__Subcategorychoices='Pizza',PSize__PSizechoices='Pamilya(12")').values_list('productname',flat=True)
        iip=0
        pizzaPamilyabd={}
        while iip<pizzaPamilyaproductnames.count():
            try:
                pizzaPamilyabdcount=0
                pizzaPamilyabdcountii=Sales.objects.filter(user=userr,productname=pizzaPamilyaproductnames[iip],Subcategory='Pizza',PSize='Pamilya(12")',DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Qty').aggregate(Sum('Qty')).get('Qty__sum')
                if pizzaPamilyabdcountii:
                    pizzaPamilyabdcounti=pizzaPamilyabdcountii
                else:
                    pizzaPamilyabdcounti=0

                pizzaPamilyabdcount=pizzaPamilyabdcount+pizzaPamilyabdcounti
            except Sales.DoesNotExist:
                pizzaPamilyabdcount=0
            pizzaPamilyabd[str(pizzaPamilyaproductnames[iip])]=str(pizzaPamilyabdcount)
            iip+=1



        PizzaFinalBD={}
        PizzaFinalBD['pizzaPamilyaproductnames']=list(pizzaPamilyaproductnames)
        PizzaFinalBD['pizzaBarkadabd']=pizzaBarkadabd
        PizzaFinalBD['pizzaPamilyabd']=pizzaPamilyabd






        frzproductnames=user1.objects.filter(user__id=userr,Category__Categorychoices='Freeze').values_list('productname',flat=True)
        iifrz=0
        frzbd={}
        while iifrz<frzproductnames.count():
            try:
                frzbdcount=0
                frzbdcountii=Sales.objects.filter(user=userr,productname=frzproductnames[iifrz],Category='Freeze',DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Qty').aggregate(Sum('Qty')).get('Qty__sum')
                if frzbdcountii:
                    frzbdcounti=frzbdcountii
                else:
                    frzbdcounti=0

                frzbdcount=frzbdcount+frzbdcounti
            except Sales.DoesNotExist:
                frzbdcount=0
            frzbd[str(frzproductnames[iifrz])]=str(frzbdcount)
            iifrz+=1



        FreezeFinalBD={}
        FreezeFinalBD['frzproductnames']=list(frzproductnames)
        FreezeFinalBD['frzbd']=frzbd




        cookiesproductnames=user1.objects.filter(user__id=userr,Subcategory__Subcategorychoices='Cookies').values_list('productname',flat=True)
        iicks=0
        cookiesbd={}
        while iicks<cookiesproductnames.count():
            try:
                cookiesbdcount=0
                cookiesbdcountii=Sales.objects.filter(user=userr,productname=cookiesproductnames[iicks],Subcategory='Cookies',DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Qty').aggregate(Sum('Qty')).get('Qty__sum')
                if cookiesbdcountii:
                    cookiesbdcounti=cookiesbdcountii
                else:
                    cookiesbdcounti=0

                cookiesbdcount=cookiesbdcount+cookiesbdcounti
            except Sales.DoesNotExist:
                cookiesbdcount=0
            cookiesbd[str(cookiesproductnames[iicks])]=str(cookiesbdcount)
            iicks+=1



        CookiesFinalBD={}
        CookiesFinalBD['cookiesproductnames']=list(cookiesproductnames)
        CookiesFinalBD['cookiesbd']=cookiesbd





        shawarmaproductnames=user1.objects.filter(user__id=userr,Subcategory__Subcategorychoices='Shawarma').values_list('productname',flat=True)
        iishaw=0
        shawarmabd={}
        while iishaw<shawarmaproductnames.count():
            try:
                shawarmabdcount=0
                shawarmabdcountii=Sales.objects.filter(user=userr,productname=shawarmaproductnames[iishaw],Subcategory='Shawarma',DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Qty').aggregate(Sum('Qty')).get('Qty__sum')
                if shawarmabdcountii:
                    shawarmabdcounti=shawarmabdcountii
                else:
                    shawarmabdcounti=0

                shawarmabdcount=shawarmabdcount+shawarmabdcounti
            except Sales.DoesNotExist:
                shawarmabdcount=0
            shawarmabd[str(shawarmaproductnames[iishaw])]=str(shawarmabdcount)
            iishaw+=1



        ShawarmaFinalBD={}
        ShawarmaFinalBD['shawarmaproductnames']=list(shawarmaproductnames)
        ShawarmaFinalBD['shawarmabd']=shawarmabd






        friesproductnames=user1.objects.filter(user__id=userr,Subcategory__Subcategorychoices='Fries').values_list('productname',flat=True)
        iifries=0
        friesbd={}
        while iifries<friesproductnames.count():
            try:
                friesbdcount=0
                friesbdcountii=Sales.objects.filter(user=userr,productname=friesproductnames[iifries],Subcategory='Fries',DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Qty').aggregate(Sum('Qty')).get('Qty__sum')
                if friesbdcountii:
                    friesbdcounti=friesbdcountii
                else:
                    friesbdcounti=0

                friesbdcount=friesbdcount+friesbdcounti
            except Sales.DoesNotExist:
                friesbdcount=0
            friesbd[str(friesproductnames[iifries])]=str(friesbdcount)
            iifries+=1



        FriesFinalBD={}
        FriesFinalBD['friesproductnames']=list(friesproductnames)
        FriesFinalBD['friesbd']=friesbd




        bubwafproductnames=user1.objects.filter(user__id=userr,Subcategory__Subcategorychoices='Bubble Waffle').values_list('productname',flat=True)
        iibubwaf=0
        bubwafbd={}
        while iibubwaf<bubwafproductnames.count():
            try:
                bubwafbdcount=0
                bubwafbdcountii=Sales.objects.filter(user=userr,productname=bubwafproductnames[iibubwaf],Subcategory='Bubble Waffle',DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Qty').aggregate(Sum('Qty')).get('Qty__sum')
                if bubwafbdcountii:
                    bubwafbdcounti=bubwafbdcountii
                else:
                    bubwafbdcounti=0

                bubwafbdcount=bubwafbdcount+bubwafbdcounti
            except Sales.DoesNotExist:
                bubwafbdcount=0
            bubwafbd[str(bubwafproductnames[iibubwaf])]=str(bubwafbdcount)
            iibubwaf+=1

            

        BubwafFinalBD={}
        BubwafFinalBD['bubwafproductnames']=list(bubwafproductnames)
        BubwafFinalBD['bubwafbd']=bubwafbd




        aoproductnames=user1.objects.filter(user__id=userr,Category__Categorychoices='Add-ons').values_list('productname',flat=True)
        iiao=0
        aobd={}
        while iiao<aoproductnames.count():
            try:
                aobdcount=0
                aobdcountii=Sales.objects.filter(user=userr,productname=aoproductnames[iiao],Category='Add-ons',DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Qty').aggregate(Sum('Qty')).get('Qty__sum')
                if aobdcountii:
                    aobdcounti=aobdcountii
                else:
                    aobdcounti=0

                aobdcount=aobdcount+aobdcounti
            except Sales.DoesNotExist:
                aobdcount=0
            aobd[str(aoproductnames[iiao])]=str(aobdcount)
            iiao+=1



        AoFinalBD={}
        AoFinalBD['aoproductnames']=list(aoproductnames)
        AoFinalBD['aobd']=aobd

        context={
        'saletodaylist':saletoday,
        'MilkteaFinalBD':json.dumps(MilkteaFinalBD, cls=JSONEncoder),
        'FrappeFinalBD':json.dumps(FrappeFinalBD, cls=JSONEncoder),
        'PizzaFinalBD':json.dumps(PizzaFinalBD, cls=JSONEncoder),
        'FreezeFinalBD':json.dumps(FreezeFinalBD, cls=JSONEncoder),
        'CookiesFinalBD':json.dumps(CookiesFinalBD, cls=JSONEncoder),
        'ShawarmaFinalBD':json.dumps(ShawarmaFinalBD, cls=JSONEncoder),
        'FriesFinalBD':json.dumps(FriesFinalBD, cls=JSONEncoder),
        'BubwafFinalBD':json.dumps(BubwafFinalBD, cls=JSONEncoder),
        'AoFinalBD':json.dumps(AoFinalBD, cls=JSONEncoder),
        
        }
        return JsonResponse(context)
    if len(Acceptorder.objects.filter(Admin=userr, productname='Ready'))>0:
        initial=Acceptorder.objects.filter(Admin=userr, productname='Ready').values_list('contactnumber', flat=True)
        readylistcontact=list(initial)
    else:
        readylistcontact=list(Acceptorder.objects.none())
    print('readylistcontact1:',readylistcontact)
    return render(request, 'saletoday.html',{'readylistcontact':readylistcontact,'onlineordercounter':onlineordercounter,'viewordersreject':viewordersreject,'rejectedorder':rejectedorder,'viewordersaccept':viewordersaccept,'acceptedorder':acceptedorder,'onlineorder':onlineorder,'notifyadmin':notifyadmin,'notifyorder':notifyorder,'punchedtotal':punchedtotal})


@login_required
def staff(request):
    userr=request.user.id
    notifyorder=acknowledgedstockorder.objects.filter(CusName="Notify",user=userr).count()
    if acknowledgedstockorder.objects.all().count()==0:
        notifyadmin=submitstockorder.objects.all().count()
    else:
        notifyadmin=0
    print('userr:',userr) 
    if punchedprod.objects.filter(user=userr).count()==0:
        punchedtotal=0
    else:
        punchedtotal=punchedprod.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
    if acknowledgedstockorder.objects.all().count()==0:
        notifyadmin=submitstockorder.objects.all().count()
    else:
        notifyadmin=0
    if is_ajax(request=request) and request.POST.get("timeinfirst"):
            day=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%A')
            datetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
            monthtoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m')
            yeartoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y')
            try:
                getdailysales=Dailysales.objects.filter(user=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Sales', flat=True)[0]
                timesheetupdate=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(Sales=getdailysales)
            except IndexError:
                timesheetupdate=timesheet.objects.none()
                getdailysales=0
            if getdailysales >= 2000 and timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday):
                getinitialsalarytoday=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('ISalary', flat=True)
                getASLBALANCEtodayi=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('ASLbalance', flat=True)
                addbonusornot=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Identifybonus', flat=True)
                if addbonusornot[0] == 'Added bonus':
                    pass
                else:
                    twokeysalebonus=getinitialsalarytoday[0]+30
                    if getASLBALANCEtodayi[0] >= 30:
                        getASLBALANCEtoday=getASLBALANCEtodayi[0]-30
                        timesheetupdatetwo=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(ISalary=twokeysalebonus, ASLbalance=getASLBALANCEtoday,Identifybonus='Added bonus')
                    else:
                        getASLBALANCEtoday=0
                        addtofinalsalaryi=30-getASLBALANCEtodayi[0]
                        getfinalsalarytoday=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('FSalary', flat=True)
                        addtofinalsalary=addtofinalsalaryi+getfinalsalarytoday
                        timesheetupdatetwo=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(ISalary=twokeysalebonus, ASLbalance=getASLBALANCEtoday,Identifybonus='Added bonus',FSalary=addtofinalsalary)
            timesheets = timesheet.objects.filter(Admin=userr, DateTime__month=monthtoday,DateTime__year=yeartoday).order_by('DateTime')
            if timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday):
                removeappearbutton='removebutton'
            else:
                removeappearbutton='appearbutton'
            context={
            'timesheets':serializers.serialize('json',timesheets, cls=JSONEncoder),
            'removeappearbutton':json.dumps(removeappearbutton, cls=JSONEncoder)
            }
            return JsonResponse(context)

    if is_ajax(request=request) and request.POST.get('usernameusername'):
        day=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%A')
        datetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
        monthtoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m')
        yeartoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y')
        usernamess=request.POST.get('usernameusername')
        passwordss=request.POST.get('passwordusername')
        imagess=request.FILES.get('imagename')
        if usernamess == 'malouKGD01' and passwordss == 'KGDmalou01':
        # Redirect to a success page.
            if int(datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%H')) < 11 :
                timeinhourstart='11:30AM'
            elif int(datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%H')) == 11 and int(datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%M')) < 30:
                timeinhourstart='11:30AM'
            elif int(datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%H')) == 19 and int(datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%M')) > 30:
                timeinhourstart='8:29PM'
            elif int(datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%H')) > 19:
                timeinhourstart='8:29PM'
            else:
                timeinhourstart=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%I:%M%p')
            onehourtomini=int(datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%H'))*60
            onehourtomin=onehourtomini
            onetotalminutesi=onehourtomin+int(datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%M'))
            if onetotalminutesi <690:
                onetotalminutes = 690
            elif onetotalminutesi>1230:
                onetotalminutes = 1229
            else:
                onetotalminutes=onetotalminutesi
            Totalminsi=((20*60)+30)-onetotalminutes
            ISalaryi=(170/(9*60))*Totalminsi
            print('Salary',ISalaryi)
            if Dailysales.objects.filter(user=userr,DateTime__day=datetoday, DateTime__month=monthtoday,DateTime__year=yeartoday):
                Salesii=Dailysales.objects.filter(user=userr,DateTime__day=datetoday, DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Sales', flat=True)
                Salesi=int(Salesii[0])
            else:
                Salesi=0
            Productimgi=imagess
            #with advance salary loan part
            if timesheet.objects.filter(Admin=userr):
                getlastobject=timesheet.objects.filter(Admin=userr).values_list('ASLbalance', flat=True).latest('DateTime')
                if getlastobject == 0:
                    FSalaryi=ISalaryi
                    varASLbalance=0
                elif getlastobject >= ISalaryi:
                    FSalaryi=0
                    varASLbalance=getlastobject-ISalaryi
                elif getlastobject < ISalaryi:
                    FSalaryi=ISalaryi-getlastobject
                    varASLbalance=0
            else:
                FSalaryi=ISalaryi
                varASLbalance=0
            #end
            timesheetsi = timesheet.objects.create(Admin=userr, Day=day,Timeout='8:30PM', Employeename='Ate Malou',Timein=timeinhourstart,Productimg=Productimgi,Totalmins=Totalminsi,Sales=Salesi,ASLbalance=varASLbalance,ISalary=ISalaryi, FSalary=FSalaryi)
            print('timesheetsi',timesheetsi)
            return JsonResponse({'reload':'success'})
        else:
            usernamechecki='usernamecheckfalse'
            usernamecheck=json.dumps(usernamechecki)
            # Return an 'invalid login' error message.
            return JsonResponse({'reload':usernamechecki}) 
            
    if is_ajax(request=request) and request.POST.get('usernameadminname'):
        day=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%A')
        datetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
        monthtoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m')
        yeartoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y')
        usernamess=request.POST.get('usernameadminname')
        passwordss=request.POST.get('passwordadminname')
        if usernamess == 'monethKGD01!' and passwordss == 'monethKGD01!':
        # Redirect to a success page.
            return JsonResponse({'reload':'success'})
        else:
            usernamechecki='usernamecheckfalse'
            usernamecheck=json.dumps(usernamechecki)
            # Return an 'invalid login' error message.
            return JsonResponse({'reload':usernamechecki})  
    if is_ajax(request=request) and request.POST.get('inputASL'):
        day=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%A')
        datetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
        monthtoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m')
        yeartoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y')
        inputASLamount=request.POST.get('inputASL')
        getlatest=timesheet.objects.filter(Admin=userr,DateTime__day=datetoday, DateTime__month=monthtoday,DateTime__year=yeartoday).update(ASLbalance=inputASLamount)
        return JsonResponse({'reload':'success'})  
            
    return render(request, 'staff.html',{'notifyadmin':notifyadmin,'notifyorder':notifyorder,'punchedtotal':punchedtotal})

#FIREBASE AREA



def send_notification(registration_ids , message_title , message_desc):
    fcm_api = "AAAAQSsusMo:APA91bGkutQBb4fQm2KvLjipFBV-rUGoCnGVRrtZdYTknKNoG3FRgM38jhC4CME0iJLv3EEllegDHmKIWwfcIdn0kFmProcp6luB3s6WyNaGmOvagnLoJD-IUxFsuX1W7Cy1od_Ueksr"
    url = "https://fcm.googleapis.com/fcm/send"
    
    headers = {
    "Content-Type":"application/json",
    "Authorization": 'key='+fcm_api}

    payload = {
        "registration_ids" : registration_ids,
        "priority" : "high",
        "notification" : {
            "body" : message_desc,
            "title" : message_title,
            
        }
    }

    result = requests.post(url,  data=json.dumps(payload), headers=headers )
    print(result.json())

 #FIREBASE MESSAGING AREA

def submitted(request):
    registration  = [
    'eLx-9ug215d4GAGtBPZq6X:APA91bF9w9HkeHaJzS6NZ0zuMSGNbm_Da_yfR5PPrKSvxbVd8a2t00_mHtqv9UxOqAX3zOrpfaPCCjHqVk2C_ZvcF9VkaYCeZMuZJnwCbfmw-aU3uHMHW_hF_4Fo5G7Mx2JLNiV8v2Fu', 
    'dqwRgSL6T2A0A2KL2Wplym:APA91bEfnHBl1g-a8Jo4FYobCqArH356pJWz5-aBmscXxCz10WfX7rj0TEqk3hJ2n6Yoea-uqZ_Jr8TauvcIH4Am9-NWKY-cTjeY62-iZCsB5WVrunICeglSd5EG6JVhwztD1aYMxcQr',
    'cRYcvuVFlENHjU9Pb1Km3q:APA91bHPi5N-I4w8yq4Wks-EfxJv2rSMQadZs2I-22EfSbisEzIqkd6ju-xTqxWNlFVQNAF9saNsWbYyu7h_fbzIk45xs1Ix7N-7cH7yLnrS2a8IXI8T5WSRZPcLk_0AJEwcaA_h2OqT'
    ]
    send_notification(registration , 'KGD Cafe Online Order' , 'Someone has ordered')
    #return HttpResponse('sent') 
    #return HttpResponseRedirect('/index/onlineorder/'+str(admin_id))

def acknowledge(request, messageacknowledgetoken):
    registration  = messageacknowledgetoken
    print('messageacknowledgetokenpassed: ', registration)
    send_notification(registration , 'KGD Cafe updates to your order' , 'KGD Cafe has been acknowledged your order. We will let you know once our rider is on his way to you.')

def orderprepared(request):
    registration  = [
    'cRYcvuVFlENHjU9Pb1Km3q:APA91bHPi5N-I4w8yq4Wks-EfxJv2rSMQadZs2I-22EfSbisEzIqkd6ju-xTqxWNlFVQNAF9saNsWbYyu7h_fbzIk45xs1Ix7N-7cH7yLnrS2a8IXI8T5WSRZPcLk_0AJEwcaA_h2OqT'
    ]
    send_notification(registration , 'KGD Cafe Rider' , 'Order is prepared. You have to go!')


def deliveryotwCustomer(request, messageacknowledgetoken):
    registration = messageacknowledgetoken
    send_notification(registration , 'KGD Cafe updates to your order' , 'Your KGD Order is on the way. Enjoy!')

def pickupCustomer(request, messageacknowledgetoken):
    registration = messageacknowledgetoken
    send_notification(registration , 'KGD Cafe updates to your order' , 'Your KGD Order is now ready to pick-up. Enjoy!')

def deliveryotwRider(request):
    registration = [
    'cRYcvuVFlENHjU9Pb1Km3q:APA91bHPi5N-I4w8yq4Wks-EfxJv2rSMQadZs2I-22EfSbisEzIqkd6ju-xTqxWNlFVQNAF9saNsWbYyu7h_fbzIk45xs1Ix7N-7cH7yLnrS2a8IXI8T5WSRZPcLk_0AJEwcaA_h2OqT'
    ]
    send_notification(registration , 'KGD Cafe Rider' , 'Order is prepared. You have to go!')

def MessageRider(request):
    registration  = [
    'cRYcvuVFlENHjU9Pb1Km3q:APA91bHPi5N-I4w8yq4Wks-EfxJv2rSMQadZs2I-22EfSbisEzIqkd6ju-xTqxWNlFVQNAF9saNsWbYyu7h_fbzIk45xs1Ix7N-7cH7yLnrS2a8IXI8T5WSRZPcLk_0AJEwcaA_h2OqT'
    ]
    send_notification(registration , 'KGD Cafe Rider' , 'KGD has been delegated an order to you')

def OTWMessage(request):
    registration  = [
    'cRYcvuVFlENHjU9Pb1Km3q:APA91bHPi5N-I4w8yq4Wks-EfxJv2rSMQadZs2I-22EfSbisEzIqkd6ju-xTqxWNlFVQNAF9saNsWbYyu7h_fbzIk45xs1Ix7N-7cH7yLnrS2a8IXI8T5WSRZPcLk_0AJEwcaA_h2OqT'
    
    ]
    send_notification(registration , 'KGD Cafe updates to your order' , 'Our Rider is OTW, please prepare your payment')
    
def showFirebaseJS(request):
    data='importScripts("https://www.gstatic.com/firebasejs/9.6.8/firebase-app-compat.js");' \
         'importScripts("https://www.gstatic.com/firebasejs/9.6.8/firebase-analytics-compat.js");' \
         'importScripts("https://www.gstatic.com/firebasejs/9.6.8/firebase-messaging-compat.js");' \
         'var firebaseConfig = {' \
         '        apiKey: "AIzaSyAQ5SNfrKB73oHMgMfIiZnfIXTzvnY_5IA",' \
         '        authDomain: "kgd-cafe.firebaseapp.com",' \
         '        projectId: "kgd-cafe",' \
         '        storageBucket: "kgd-cafe.appspot.com",' \
         '        messagingSenderId: "279897354442",' \
         '        appId: "1:279897354442:web:022b31ee613f3eea7bc433",' \
         '        measurementId: "G-GWT5VVJXBK"' \
         ' };' \
         'firebase.initializeApp(firebaseConfig);' \
         'const messaging=firebase.messaging();' \
         'messaging.onBackgroundMessage(function (payload) {' \
         '    console.log(payload);' \
         '    const notification=JSON.parse(payload);' \
         '    const notificationOption={' \
         '        body:notification.body,' \
         '        title:notification.title,' \
         '    };' \
         '    return self.registration.showNotification(payload.notification.title,notificationOption);' \
         '});'\

    return HttpResponse(data,content_type="text/javascript")




@login_required
def kgddashboard(request):
     if request.GET.get('next'):
            
            userr=request.user.id
            if request.GET.get('acceptcontactno'):
                contactnumberaccept = request.GET.get('acceptcontactno')
                rider = request.GET.get('rider')
                getETA = request.GET.get('ETA')
                Accepted = Customer.objects.filter(Admin=userr,contactnumber=contactnumberaccept)
            
                objs = [Acceptorder(
                            Admin=Accepted.Admin,
                            Customername=Accepted.Customername,
                            codecoupon=Accepted.codecoupon,
                            discount=Accepted.discount or None,
                            Province=Accepted.Province,
                            MunicipalityCity=Accepted.MunicipalityCity,
                            Barangay=Accepted.Barangay,
                            StreetPurok=Accepted.StreetPurok,
                            Housenumber=Accepted.Housenumber or None,
                            LandmarksnNotes=Accepted.LandmarksnNotes or None,
                            DeliveryFee=Accepted.DeliveryFee or 0,
                            contactnumber=Accepted.contactnumber,
                            Rider=rider,
                            productname=Accepted.productname,
                            Category=Accepted.Category,
                            Subcategory=Accepted.Subcategory or None,
                            Size=Accepted.Size  or None,
                            PSize=Accepted.PSize or None,
                            Addons=Accepted.Addons or None,
                            QtyAddons= Accepted.QtyAddons or 0,
                            Price=Accepted.Price,
                            Subtotal = Accepted.Subtotal,
                            GSubtotal=Accepted.GSubtotal,
                            Cost=Accepted.Cost,
                            Qty=Accepted.Qty,
                            Bill=Accepted.Bill or 0,
                            Change=Accepted.Change or 0,
                            ETA=getETA,
                            MOP=Accepted.MOP,
                            ordertype='Online',
                            Timetodeliver=Accepted.Timetodeliver,
                            ScheduleTime=Accepted.ScheduleTime,
                            gpslat = Accepted.gpslat,
                            gpslng = Accepted.gpslng,
                            gpsaccuracy = Accepted.gpsaccuracy,
                            pinnedlat = Accepted.pinnedlat,
                            pinnedlng = Accepted.pinnedlng,
                            
                            tokens = Accepted.tokens or None,
                            DateTime=Accepted.DateTime,
                    )
                    for Accepted in Accepted
                ]
                Acceptorders = Acceptorder.objects.bulk_create(objs)
                Accepted.delete()
                messageacknowledgetokeni=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberaccept).values_list('tokens',flat=True).first()
                messageacknowledgetoken = ["dHEGNR4YGO8a-AVQWfIE33:APA91bGkNxUcRZEHJQCkUy3k3THUEMxml9q4819bDQw1b8UkD05qThidgXq3Nnr46I1pwQikZgwiGFuBgKwUxHO6kUXI9KId3ZK0fQ0zi83QegTtVimqV18a2pDqBq5qnJf-BK74Z1nL", messageacknowledgetokeni]
                acknowledge(request, messageacknowledgetoken)
                MessageRider(request)
                return HttpResponseRedirect('/index/pos')

            if len(Acceptorder.objects.filter(Admin=userr))>0:
                acceptedorder = Acceptorder.objects.filter(Admin=userr).distinct('contactnumber')
                acceptedorderall = Acceptorder.objects.filter(Admin=userr)
            else:
                acceptedorder = Acceptorder.objects.none()
                acceptedorderall = Acceptorder.objects.none()
            viewordersacceptii={}
            arrayoneaccept=[]
            contactdistincteraccepti = Acceptorder.objects.filter(Admin=userr).distinct('contactnumber')
            contactdistincteraccept=contactdistincteraccepti.values_list('contactnumber',flat=True)
            i=0
            for cndistinctaccept in contactdistincteraccept:
                arrayseparatoracceptiii=Acceptorder.objects.filter(Admin=userr,contactnumber=cndistinctaccept).exclude(productname='Ready').values()
                arrayseparatoraccepti = list(arrayseparatoracceptiii)
                arrayseparatoraccept=json.dumps(arrayseparatoraccepti, cls=JSONEncoder)
                viewordersacceptii[contactdistincteraccept[i]]=arrayseparatoraccept
                i=i+1
            viewordersaccepti=viewordersacceptii
            viewordersaccept=json.dumps(viewordersaccepti, cls=JSONEncoder)
        

            if (request.GET.get('rider') == "") and (request.GET.get('contactnoreject') or request.GET.get('contactnoaccepted')):
                if request.GET.get('contactnoreject'):
                    contactnumberreject = request.GET.get('contactnoreject')
                    Rejected = Customer.objects.filter(Admin=userr,contactnumber=contactnumberreject)
                elif request.GET.get('contactnoaccepted'):
                    contactnumberreject = request.GET.get('contactnoaccepted')
                    if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject, productname='Ready'):
                        deletethis=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject, productname='Ready')
                        deletethis.delete()
                    Rejected = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject)
            
                objs = [Rejectorder(
                            Admin=userr,
                            Customername=Rejected.Customername,
                            codecoupon=Rejected.codecoupon,
                            discount=Rejected.discount or None,
                            Province=Rejected.Province,
                            MunicipalityCity=Rejected.MunicipalityCity,
                            Barangay=Rejected.Barangay,
                            StreetPurok=Rejected.StreetPurok,
                            Housenumber=Rejected.Housenumber or None,
                            LandmarksnNotes=Rejected.LandmarksnNotes or None,
                            DeliveryFee=Rejected.DeliveryFee or 0,
                            contactnumber=Rejected.contactnumber,
                            productname=Rejected.productname,
                            Category=Rejected.Category,
                            Subcategory=Rejected.Subcategory or None,
                            Size=Rejected.Size  or None,
                            PSize=Rejected.PSize or None,
                            Addons=Rejected.Addons or None,
                            QtyAddons= Rejected.QtyAddons or 0,
                            Price=Rejected.Price,
                            Subtotal = Rejected.Subtotal,
                            GSubtotal=Rejected.GSubtotal,
                            Cost=Rejected.Cost,
                            Qty=Rejected.Qty,
                            Bill=Rejected.Bill or 0,
                            Change=Rejected.Change or 0,
                            MOP=Rejected.MOP,
                            ordertype='Online',
                            Timetodeliver=Rejected.Timetodeliver,
                            ScheduleTime=Rejected.ScheduleTime,
                            gpslat = Rejected.gpslat,
                            gpslng = Rejected.gpslng,
                            gpsaccuracy = Rejected.gpsaccuracy,
                            pinnedlat = Rejected.pinnedlat,
                            pinnedlng = Rejected.pinnedlng,
                            
                            tokens = Rejected.tokens  or None,
                            DateTime=Rejected.DateTime,
                    )
                    for Rejected in Rejected
                ]
                Rejectorders = Rejectorder.objects.bulk_create(objs)
                Rejected.delete()
                return HttpResponseRedirect('/index/pos')

            if len(Rejectorder.objects.filter(Admin=userr))>0:
                rejectedorder = Rejectorder.objects.filter(Admin=userr).distinct('contactnumber')
                rejectedorderall = Rejectorder.objects.filter(Admin=userr)
            else:
                rejectedorder = Rejectorder.objects.none()
                rejectedorderall = Rejectorder.objects.none()
            viewordersrejectii={}
            arrayonereject=[]
            contactdistincterrejecti = Rejectorder.objects.filter(Admin=userr).distinct('contactnumber')
            contactdistincterreject=contactdistincterrejecti.values_list('contactnumber',flat=True)
            i=0
            for cndistinctreject in contactdistincterreject:
                arrayseparatorrejectiii=Rejectorder.objects.filter(Admin=userr,contactnumber=cndistinctreject).exclude(productname='Ready').values()
                arrayseparatorrejecti = list(arrayseparatorrejectiii)
                arrayseparatorreject=json.dumps(arrayseparatorrejecti, cls=JSONEncoder)
                viewordersrejectii[contactdistincterreject[i]]=arrayseparatorreject
                i=i+1
            viewordersrejecti=viewordersrejectii
            viewordersreject=json.dumps(viewordersrejecti, cls=JSONEncoder)

        

            if request.GET.get('contactnorestore'):
                contactnumberrestore = request.GET.get('contactnorestore')
                Restored = Rejectorder.objects.filter(Admin=userr,contactnumber=contactnumberrestore)
            
                objs = [Customer(
                            Admin=userr,
                            Customername=Restored.Customername,
                            codecoupon=Restored.codecoupon,
                            discount=Restored.discount or None,
                            Province=Restored.Province,
                            MunicipalityCity=Restored.MunicipalityCity,
                            Barangay=Restored.Barangay,
                            StreetPurok=Restored.StreetPurok,
                            Housenumber=Restored.Housenumber or None,
                            LandmarksnNotes=Restored.LandmarksnNotes or None,
                            DeliveryFee=Restored.DeliveryFee or 0,
                            contactnumber=Restored.contactnumber,
                            productname=Restored.productname,
                            Category=Restored.Category,
                            Subcategory=Restored.Subcategory or None,
                            Size=Restored.Size  or None,
                            PSize=Restored.PSize or None,
                            Addons=Restored.Addons or None,
                            QtyAddons= Restored.QtyAddons or 0,
                            Price=Restored.Price,
                            Subtotal = Restored.Subtotal,
                            GSubtotal=Restored.GSubtotal,
                            Cost=Restored.Cost,
                            Qty=Restored.Qty,
                            Bill=Restored.Bill or 0,
                            Change=Restored.Change or 0,
                            MOP=Restored.MOP,
                            ordertype='Online',
                            Timetodeliver=Restored.Timetodeliver,
                            ScheduleTime=Restored.ScheduleTime,
                            gpslat = Restored.gpslat,
                            gpslng = Restored.gpslng,
                            gpsaccuracy = Restored.gpsaccuracy,
                            pinnedlat = Restored.pinnedlat,
                            pinnedlng = Restored.pinnedlng,
                          
                            tokens = Restored.tokens  or None,
                            DateTime=Restored.DateTime,
                    )
                    for Restored in Restored
                ]
                Restore = Customer.objects.bulk_create(objs)
                Restored.delete()
                return HttpResponseRedirect('/index/pos')

            if len(Customer.objects.filter(Admin=userr))>0:
                onlineorder = Customer.objects.filter(Admin=userr).distinct('contactnumber')
                onlineorderall = Customer.objects.filter(Admin=userr)
            else:
                onlineorder = Customer.objects.none()
                onlineorderall = Customer.objects.none()
            viewordersii={}
            arrayone=[]
            contactdistincteri = Customer.objects.filter(Admin=userr).distinct('contactnumber')
            contactdistincter=contactdistincteri.values_list('contactnumber',flat=True)
            i=0
            for cndistinct in contactdistincter:  
                arrayseparatoriii=Customer.objects.filter(Admin=userr,contactnumber=cndistinct).values()
                arrayseparatori = list(arrayseparatoriii)
                arrayseparator=json.dumps(arrayseparatori, cls=JSONEncoder)
                viewordersii[contactdistincter[i]]=arrayseparator
                i=i+1
            viewordersi=viewordersii
            vieworders=json.dumps(viewordersi, cls=JSONEncoder)

            onlineordercounter = len(Customer.objects.filter(Admin=userr).distinct('contactnumber'))

            if is_ajax(request=request) and request.POST.get("Ready"):
                contactnumberready = request.POST.get('Ready')
                Readyadd = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).first()
                Readyacceptorder=Acceptorder.objects.create(
                            Admin=userr,
                            Customername=Readyadd.Customername,
                            codecoupon=Readyadd.codecoupon,
                            discount=Readyadd.discount or None,
                            Province=Readyadd.Province,
                            MunicipalityCity=Readyadd.MunicipalityCity,
                            Barangay=Readyadd.Barangay,
                            StreetPurok=Readyadd.StreetPurok,
                            Housenumber=Readyadd.Housenumber or None,
                            LandmarksnNotes=Readyadd.LandmarksnNotes or None,
                            DeliveryFee=0,
                            contactnumber=Readyadd.contactnumber,
                            productname='Ready',
                            Category=Readyadd.Category,
                            Subcategory=None,
                            Size=None,
                            PSize=None,
                            Addons=None,
                            QtyAddons= 0,
                            Price=0,
                            Subtotal = 0,
                            GSubtotal=Readyadd.GSubtotal,
                            Cost=0,
                            Qty=0,
                            Bill=Readyadd.Bill or 0,
                            Change=Readyadd.Change or 0,
                            MOP=Readyadd.MOP,
                            ordertype='Online',
                            Timetodeliver=Readyadd.Timetodeliver,
                            ScheduleTime=Readyadd.ScheduleTime,
                            gpslat = Readyadd.gpslat,
                            gpslng = Readyadd.gpslng,
                            gpsaccuracy = Readyadd.gpsaccuracy,
                            pinnedlat = Readyadd.pinnedlat,
                            pinnedlng = Readyadd.pinnedlng,
                            
                            tokens = Readyadd.tokens  or None,
                            DateTime=Readyadd.DateTime,
                            )
                Readyacceptorder.save()
                if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready, MOP='COD'):
                    orderprepared(request)
                messageacknowledgetokeni=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('tokens',flat=True).first()
                messageacknowledgetoken = ["dHEGNR4YGO8a-AVQWfIE33:APA91bGkNxUcRZEHJQCkUy3k3THUEMxml9q4819bDQw1b8UkD05qThidgXq3Nnr46I1pwQikZgwiGFuBgKwUxHO6kUXI9KId3ZK0fQ0zi83QegTtVimqV18a2pDqBq5qnJf-BK74Z1nL", messageacknowledgetokeni]
                if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('MOP',flat=True).first() == 'COD' or Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('MOP',flat=True).first() == 'GcashDelivery':
                    deliveryotwRider(request)
                    deliveryotwCustomer(request , messageacknowledgetoken)
                else:
                    pickupCustomer(request , messageacknowledgetoken)
                return JsonResponse({'Ready':'Ready'})
            if is_ajax(request=request) and request.GET.get("apini"):
                onlineordercounterf = onlineordercounter
                onlineorderf = [serializers.serialize('json',onlineorder, cls=JSONEncoder),vieworders]
                return JsonResponse({'onlineorderf':onlineorderf})
            
            if is_ajax(request=request) and request.POST.get('doneorders'):
                contactnumberdonei = json.loads(request.POST.get('doneorders'))
                contactnumberdone = contactnumberdonei[0]['contactnumber']
                if contactnumberdonei[0]['codecoupon']:
                    if couponlist.objects.filter(code=contactnumberdonei[0]['codecoupon']):
                        codeconsumereducerii=couponlist.objects.get(code=contactnumberdonei[0]['codecoupon'])
                        if codeconsumereducerii.is_consumable == True and codeconsumereducerii.redeemlimit>0:
                            codeconsumereduceri=int(codeconsumereducerii.redeemlimit)-1
                            codeconsumereducer=couponlist.objects.filter(code=contactnumberdonei[0]['codecoupon']).update(redeemlimit=codeconsumereduceri)
                        else:
                            pass
                    else:
                        pass
                else:
                    pass
                if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone, productname='Ready'):
                    deletethis=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone, productname='Ready')
                    deletethis.delete()
                Done = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone)
                try:
                    Sales.objects.filter(contactnumber=contactnumberdonei[0]['contactnumber'], CusName=contactnumberdonei[0]['Customername'], productname='DeliveryFee', DateTime=contactnumberdonei[0]['DateTime'])
                    deliveryfeepaid='true'
                except Sales.DoesNotExist:
                    deliveryfeepaid='false'
                if contactnumberdonei[0]['DeliveryFee'] != None and deliveryfeepaid == 'true':
                    devfeeassales=Sales.objects.create(
                            user=userr,
                            CusName=contactnumberdonei[0]['Customername'],
                            codecoupon=contactnumberdonei[0]['codecoupon'] or None,
                            discount=contactnumberdonei[0]['discount'] or None,
                            Province=contactnumberdonei[0]['Province'],
                            MunicipalityCity=contactnumberdonei[0]['MunicipalityCity'],
                            Barangay=contactnumberdonei[0]['Barangay'],
                            StreetPurok=contactnumberdonei[0]['StreetPurok'],
                            Housenumber=contactnumberdonei[0]['Housenumber'] or None,
                            LandmarksnNotes=contactnumberdonei[0]['LandmarksnNotes'] or None,
                            DeliveryFee=contactnumberdonei[0]['DeliveryFee'] or None,
                            contactnumber=contactnumberdonei[0]['contactnumber'],
                            productname='DeliveryFee',
                            Category='DeliveryFee',
                            Subcategory='DeliveryFee',
                            Size=None,
                            PSize=None,
                            Addons=None,
                            QtyAddons=0,
                            Price=contactnumberdonei[0]['DeliveryFee'],
                            Subtotal = contactnumberdonei[0]['DeliveryFee'],
                            GSubtotal=contactnumberdonei[0]['GSubtotal'],
                            Cost=0,
                            Qty=1,
                            Bill=contactnumberdonei[0]['Bill'] or 0,
                            Change=contactnumberdonei[0]['Change'] or 0,
                            MOP=contactnumberdonei[0]['MOP'],
                            ordertype='Online',
                            Timetodeliver=contactnumberdonei[0]['Timetodeliver'] or None,
                            ScheduleTime=contactnumberdonei[0]['ScheduleTime'] or None,
                            gpslat = contactnumberdonei[0]['gpslat'],
                            gpslng = contactnumberdonei[0]['gpslng'],
                            gpsaccuracy = contactnumberdonei[0]['gpsaccuracy'],
                            pinnedlat = contactnumberdonei[0]['pinnedlat'],
                            pinnedlng = contactnumberdonei[0]['pinnedlng'],
                            
                            tokens = contactnumberdonei[0]['tokens'] or None,
                            DateTime=contactnumberdonei[0]['DateTime'],
                    )
                    devfeeassales.save()
                if contactnumberdonei[0]['discount']:
                    objs = [Sales(
                                user=userr,
                                CusName=Done.Customername,
                                codecoupon=Done.codecoupon,
                                discount=Done.discount or None,
                                Province=Done.Province,
                                MunicipalityCity=Done.MunicipalityCity,
                                Barangay=Done.Barangay,
                                StreetPurok=Done.StreetPurok,
                                Housenumber=Done.Housenumber or None,
                                LandmarksnNotes=Done.LandmarksnNotes or None,
                                DeliveryFee=Done.DeliveryFee or None,
                                contactnumber=Done.contactnumber,
                                productname=Done.productname,
                                Category=Done.Category,
                                Subcategory=Done.Subcategory or None,
                                Size=Done.Size  or None,
                                PSize=Done.PSize or None,
                                Addons=Done.Addons or None,
                                QtyAddons= Done.QtyAddons or 0,
                                Price=Done.Price,
                                Subtotal = Done.Subtotal-((Done.Subtotal)*(Decimal(int(Done.discount)/100))),
                                GSubtotal=Done.GSubtotal,
                                Cost=Done.Cost,
                                Qty=Done.Qty,
                                Bill=Done.Bill or 0,
                                Change=Done.Change or 0,
                                MOP=Done.MOP,
                                ordertype='Online',
                                Timetodeliver=Done.Timetodeliver,
                                ScheduleTime=Done.ScheduleTime,
                                gpslat = Done.gpslat,
                                gpslng = Done.gpslng,
                                gpsaccuracy = Done.gpsaccuracy,
                                pinnedlat = Done.pinnedlat,
                                pinnedlng = Done.pinnedlng,
                            
                                tokens = Done.tokens or None,
                                DateTime=Done.DateTime,
                        )
                        for Done in Done
                    ]
                else:
                    objs = [Sales(
                                user=userr,
                                CusName=Done.Customername,
                                codecoupon=Done.codecoupon,
                                discount=Done.discount or None,
                                Province=Done.Province,
                                MunicipalityCity=Done.MunicipalityCity,
                                Barangay=Done.Barangay,
                                StreetPurok=Done.StreetPurok,
                                Housenumber=Done.Housenumber or None,
                                LandmarksnNotes=Done.LandmarksnNotes or None,
                                DeliveryFee=Done.DeliveryFee or None,
                                contactnumber=Done.contactnumber,
                                productname=Done.productname,
                                Category=Done.Category,
                                Subcategory=Done.Subcategory or None,
                                Size=Done.Size  or None,
                                PSize=Done.PSize or None,
                                Addons=Done.Addons or None,
                                QtyAddons= Done.QtyAddons or 0,
                                Price=Done.Price,
                                Subtotal = Done.Subtotal,
                                GSubtotal=Done.GSubtotal,
                                Cost=Done.Cost,
                                Qty=Done.Qty,
                                Bill=Done.Bill or 0,
                                Change=Done.Change or 0,
                                MOP=Done.MOP,
                                ordertype='Online',
                                Timetodeliver=Done.Timetodeliver,
                                ScheduleTime=Done.ScheduleTime,
                                gpslat = Done.gpslat,
                                gpslng = Done.gpslng,
                                gpsaccuracy = Done.gpsaccuracy,
                                pinnedlat = Done.pinnedlat,
                                pinnedlng = Done.pinnedlng,
                            
                                tokens = Done.tokens or None,
                                DateTime=Done.DateTime,
                        )
                        for Done in Done
                    ]
                Salesorders = Sales.objects.bulk_create(objs)
                Done.delete()
                datetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
                monthtoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m')
                yeartoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y')
                try:
                    getdailysales=Dailysales.objects.filter(user=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Sales', flat=True)[0]
                    timesheetupdate=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(Sales=getdailysales)
                except IndexError:
                    timesheetupdate=timesheet.objects.none()
                    getdailysales=0
                if getdailysales >= 2000 and timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday):
                    getinitialsalarytoday=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('ISalary', flat=True)
                    getASLBALANCEtodayi=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('ASLbalance', flat=True)
                    addbonusornot=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Identifybonus', flat=True)
                    if addbonusornot[0] == 'Added bonus':
                        pass
                    else:
                        twokeysalebonus=getinitialsalarytoday[0]+30
                        if getASLBALANCEtodayi[0] >= 30:
                            getASLBALANCEtoday=getASLBALANCEtodayi[0]-30
                            timesheetupdatetwo=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(ISalary=twokeysalebonus, ASLbalance=getASLBALANCEtoday,Identifybonus='Added bonus')
                        else:
                            getASLBALANCEtoday=0
                            addtofinalsalaryi=30-getASLBALANCEtodayi[0]
                            getfinalsalarytoday=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('FSalary', flat=True)
                            addtofinalsalary=addtofinalsalaryi+getfinalsalarytoday
                            timesheetupdatetwo=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(ISalary=twokeysalebonus, ASLbalance=getASLBALANCEtoday,Identifybonus='Added bonus',FSalary=addtofinalsalary)
                return HttpResponseRedirect('/index/pos')



            notifyorder=acknowledgedstockorder.objects.filter(CusName="Notify",user=userr).count()
            if acknowledgedstockorder.objects.all().count()==0:
                notifyadmin=submitstockorder.objects.all().count()
            else:
                notifyadmin=0
            print('userr:',userr) 
            if punchedprod.objects.filter(user=userr).count()==0:
                punchedtotal=0
            else:
                punchedtotal=punchedprod.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
            notifyorder=acknowledgedstockorder.objects.filter(CusName="Notify",user=userr).count()
            if acknowledgedstockorder.objects.all().count()==0:
                notifyadmin=submitstockorder.objects.all().count()
            else:
                notifyadmin=0
            datetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
            monthtoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m')
            yeartoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y')
            countsalestoday=Sales.objects.filter(user=userr,DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).count()
            
            da1daily=Sales.objects.filter(user=userr,DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday)
            if Sales.objects.filter(user=userr).count()==0:
                 dd=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
                 daydaily={'user':userr,'Qty':0,'Subtotal':0,'Cost':0,'Price':0,'Amount':0}
                 
                 
            elif Sales.objects.filter(user=userr,DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).count()==0:
                 dd=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
                 daydaily={'user':userr,'Qty':0,'Subtotal':0,'Cost':0,'Price':0,'Amount':0}
                 
                 

            elif Sales.objects.filter(user=userr).values('DateTime__day').count()==1:
                daydistinct1=Sales.objects.filter(user=userr).values('DateTime__day').distinct().first()
                for DateTime__day,dd in daydistinct1.items():
                    daydaily=Sales.objects.filter(user=userr,DateTime__day=dd)
                    
                    
            else:
                daydistinct0=Sales.objects.filter(user=userr).values('DateTime__day').distinct()
                daydistinct1=Sales.objects.filter(user=userr).values('DateTime__day').distinct().first()
                for daydistinct in daydistinct0:
                    for DateTime__day, dd in daydistinct.items():
                        daydaily=Sales.objects.filter(user=userr,DateTime__day=dd)
                        
                        
            
            if Sales.objects.filter(user=userr).count()==0:
                daydistinct11=datetime.datetime.now(pytz.timezone('Asia/Singapore'))
                daydaily['subtotalCosti']=(daydaily['Qty']*daydaily['Cost'])
                subtotalcost=daydaily['subtotalCosti']
                salescalc=daydaily['Subtotal']
                Neto=salescalc-subtotalcost
                starts=daydaily['Amount']
                ends=daydaily['Amount']
                values=daydaily['Amount']
                expenses=daydaily['Amount']

            else:
                if Sales.objects.filter(user=userr,DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).count()==0:
                    daydistinct11=datetime.datetime.now(pytz.timezone('Asia/Singapore'))
                    daydaily['subtotalCosti']=(daydaily['Qty']*daydaily['Cost'])
                    subtotalcost=daydaily['subtotalCosti']
                    salescalc=daydaily['Subtotal']
                    Neto=salescalc-subtotalcost
                    starts=daydaily['Amount']
                    ends=daydaily['Amount']
                    values=daydaily['Amount']
                    expenses=daydaily['Amount']
                else:
                    daydistinct11=Sales.objects.filter(user=userr,DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).latest('DateTime__day')
                    
                    subtotalcosti=Sales.objects.filter(user=userr,DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values('DateTime__day').annotate(subtotalCosti=F('Qty')*F('Cost'))
                    subtotalcost=subtotalcosti.aggregate(Sum('subtotalCosti')).get('subtotalCosti__sum')
                    
                    salescalc=da1daily.aggregate(Sum('Subtotal')).get("Subtotal__sum",0.00)
                    
                    Neto=salescalc-subtotalcost
                    
                    endsi=da1daily.filter(Subcategorys__saesubcatchoices="End Stock").aggregate(Sum('Amount')).get("Amount__sum")
                    valuesi=da1daily.filter(Subcategorys__saesubcatchoices="Value Stock").aggregate(Sum('Amount')).get("Amount__sum")
                    
                    startsi=da1daily.filter(Subcategorys__saesubcatchoices="Start Stock").aggregate(Sum('Amount')).get("Amount__sum")
                    expensesi=da1daily.filter(Categoryaes__saecatchoices="Expenses").aggregate(Sum('Amount')).get("Amount__sum")
                    if expensesi==None:
                        expenses=0
                    else:
                        expenses=expensesi
                    if startsi==None:
                        starts=0
                    else:
                        starts=startsi
                    if endsi==None:
                        ends=0
                    else:
                        ends=endsi
                    if valuesi==None:
                        values=0
                    else:
                        values=valuesi

            if Dailysales.objects.filter(user=userr).count()==0:
                if Sales.objects.filter(user=userr).count()==0:
                    objs = [Dailysales(
                        user=userr,
                        DateTime=daydistinct11,
                        Sales=salescalc,
                        Expenses=expenses,
                        Startstocks = starts,
                        Endstocks = ends,
                        Valuestocks = values,
                        Net=Neto,
                    )
                    ]
                else:

                    objs = [Dailysales(
                        user=userr,
                        DateTime=daydistinct11.DateTime,
                        Sales=salescalc,
                        Expenses=expenses,
                        Startstocks =starts,
                        Endstocks =ends,
                        Valuestocks =values,
                        Net=Neto,
                    )
                    ]
                ddailyi = Dailysales.objects.bulk_create(objs)
                ddaily = Dailysales.objects.filter(user=userr).order_by('DateTime')
                totalsales = ddaily.aggregate(Sum('Sales')).get('Sales__sum',0.00)
                totalnet = ddaily.aggregate(Sum('Net')).get('Net__sum')
                #FOR MONTH
                monthly={}
                monthlysales=Dailysales.objects.filter(user=userr).order_by('DateTime')
                monthtotalsalesi = ddaily.aggregate(Sum('Sales')).get('Sales__sum')
                monthExpensesi= ddaily.aggregate(Sum('Expenses')).get('Expenses__sum')
                monthvalues=ddaily.aggregate(Sum('Valuestocks')).get('Valuestocks__sum')
                monthstarts=ddaily.aggregate(Sum('Startstocks')).get('Startstocks__sum')
                monthends=ddaily.aggregate(Sum('Endstocks')).get('Endstocks__sum')
                monthly['monthCOGS']=monthstarts+monthvalues-monthends
                monthly['monthtotalsales']=monthtotalsalesi
                monthly['monthExpenses']=monthExpensesi
                monthly['monthtotalnet']=monthly['monthtotalsales']-monthly['monthCOGS']-monthly['monthExpenses']
                if len(Acceptorder.objects.filter(Admin=userr, productname='Ready'))>0:
                    initial=Acceptorder.objects.filter(Admin=userr, productname='Ready').values_list('contactnumber', flat=True)
                    readylistcontact=list(initial)
                else:
                    readylistcontact=list(Acceptorder.objects.none())
                print('readylistcontact1:',readylistcontact)
                #END FOR MONTH
                datetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
                monthtoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m')
                yeartoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y')
                try:
                    getdailysales=Dailysales.objects.filter(user=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Sales', flat=True)[0]
                    timesheetupdate=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(Sales=getdailysales)
                except IndexError:
                    timesheetupdate=timesheet.objects.none()
                    getdailysales=0
                if getdailysales >= 2000 and timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday):
                    getinitialsalarytoday=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('ISalary', flat=True)
                    getASLBALANCEtodayi[0]=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('ASLbalance', flat=True)
                    addbonusornot=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Identifybonus', flat=True)
                    if addbonusornot[0] == 'Added bonus':
                        pass
                    else:
                        twokeysalebonus=getinitialsalarytoday[0]+30
                        if getASLBALANCEtodayi[0] >= 30:
                            getASLBALANCEtoday=getASLBALANCEtodayi[0]-30
                            timesheetupdatetwo=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(ISalary=twokeysalebonus, ASLbalance=getASLBALANCEtoday,Identifybonus='Added bonus')
                        else:
                            getASLBALANCEtoday=0
                            addtofinalsalaryi=30-getASLBALANCEtodayi[0]
                            getfinalsalarytoday=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('FSalary', flat=True)
                            addtofinalsalary=addtofinalsalaryi+getfinalsalarytoday
                            timesheetupdatetwo=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(ISalary=twokeysalebonus, ASLbalance=getASLBALANCEtoday,Identifybonus='Added bonus',FSalary=addtofinalsalary)
                return HttpResponseRedirect(str(request.GET.get('next')))
            else:
                getobjdate=Dailysales.objects.filter(user=userr).latest('DateTime')
                subuk=getobjdate.DateTime
                gettimeobj = localtime(subuk).strftime('%b:%d')
                print('gettimeobj:  ',gettimeobj)
                checkdatetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%b:%d')
                print('checkdatetoday:  ',checkdatetoday)
                if checkdatetoday!=gettimeobj:
                    if Sales.objects.filter(user=userr,DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).count()==0:
                        objs = [Dailysales(
                            user=userr,
                            DateTime=daydistinct11,
                            Sales=salescalc,
                            Expenses=expenses,
                            Startstocks =starts,
                            Endstocks =ends,
                            Valuestocks =values,
                            Net=Neto,
                        )
                        ]
                    else:
                        objs = [Dailysales(
                            user=userr,
                            DateTime=daydistinct11.DateTime,
                            Sales=salescalc,
                            Expenses=expenses,
                            Startstocks =starts,
                            Endstocks =ends,
                            Valuestocks =values,
                            Net=Neto,
                        )
                        ]
                    ddailyi = Dailysales.objects.bulk_create(objs)
                    ddaily = Dailysales.objects.filter(user=userr).order_by('DateTime')
                    totalsales = ddaily.aggregate(Sum('Sales')).get('Sales__sum',0.00)
                    totalnet = ddaily.aggregate(Sum('Net')).get('Net__sum')
                    #for month 2 Dailysales
                    monthdistinct0=Dailysales.objects.filter(user=userr).values('DateTime__month').distinct()
                    monthdistinct1=Dailysales.objects.filter(user=userr).values_list('DateTime__month',flat=True).distinct()
                    i = 0
                    monthdistinct11=monthdistinct1.count()
                    

                    monthh={}
                    while i < monthdistinct11:
                        sample=monthdistinct1[i]
                        sample2=Dailysales.objects.filter(user=userr,DateTime__month=sample)

                        
                        monthlysales=sample2
                        
                        getmonth=monthlysales.values_list('DateTime__month',flat=True).first()
                    
                        if getmonth==1:
                            finalmonth='January'
                        elif getmonth==2:
                            finalmonth='February'
                        elif getmonth==3:
                            finalmonth='March'
                        elif getmonth==4:
                            finalmonth='April'
                        elif getmonth==5:
                            finalmonth='May'
                        elif getmonth==6:
                            finalmonth='June'
                        elif getmonth==7:
                            finalmonth='July'
                        elif getmonth==8:
                            finalmonth='August'
                        elif getmonth==9:
                            finalmonth='September'
                        elif getmonth==10:
                            finalmonth='October'
                        elif getmonth==11:
                            finalmonth='November'
                        elif getmonth==12:
                            finalmonth='December'
                        finalyear=str(monthlysales.values_list('DateTime__year',flat=True).first())
                        
                        month={}
                        
                        monthtotalsalesi = monthlysales.aggregate(Sum('Sales')).get('Sales__sum')
                        
                        monthExpensesi= monthlysales.aggregate(Sum('Expenses')).get('Expenses__sum')
                        monthvalues=monthlysales.aggregate(Sum('Valuestocks')).get('Valuestocks__sum')
                        monthstarts=monthlysales.aggregate(Sum('Startstocks')).get('Startstocks__sum')
                        monthends=monthlysales.aggregate(Sum('Endstocks')).get('Endstocks__sum')
                        month['monthdate']=finalmonth+", "+finalyear
                        month['monthtotalsales']='₱'+str(monthtotalsalesi)
                        month['monthExpenses']='₱'+(str(monthExpensesi))
                        calculate=monthtotalsalesi-(monthstarts+monthvalues-monthends)-monthExpensesi
                        if calculate<0:
                            month['monthCOGS']='₱0.00'
                            month['monthtotalnet']='₱0.00'
                        else:
                            month['monthCOGS']='₱'+(str(monthstarts+monthvalues-monthends))
                            month['monthtotalnet']='₱'+(str(monthtotalsalesi-(monthstarts+monthvalues-monthends)-monthExpensesi))
                        monthh[i]=month.values()
                        
                        i += 1
                    
                    monthly=monthh.values()
                    cogsss=(monthstarts+monthvalues-monthends)
                    print('cogsss2:',cogsss)
                    identifier=Dailysales.objects.filter(user=userr,DateTime__month=3)
                    monthExpensesiu= identifier.aggregate(Sum('Expenses')).get('Expenses__sum')
                    monthvaluesu=identifier.aggregate(Sum('Valuestocks')).get('Valuestocks__sum')
                    monthstartsu=identifier.aggregate(Sum('Startstocks')).get('Startstocks__sum')
                    monthendsu=identifier.aggregate(Sum('Endstocks')).get('Endstocks__sum')
                    expen='₱'+(str(monthExpensesiu))
                    monthtotalsalesiu = identifier.aggregate(Sum('Sales')).get('Sales__sum')
                    cogs='₱'+(str(monthstartsu+monthvaluesu-monthendsu))
                    net='₱'+(str(monthtotalsalesiu-(monthstartsu+monthvaluesu-monthendsu)-monthExpensesiu))
                    print('monthstarts: ',monthstartsu,'    monthvalues: ',monthvaluesu,'   monthends:',monthendsu,'    cogs:  ',cogs)
                    #endfor month 2 Dailysales
                    if len(Acceptorder.objects.filter(Admin=userr, productname='Ready'))>0:
                        initial=Acceptorder.objects.filter(Admin=userr, productname='Ready').values_list('contactnumber', flat=True)
                        readylistcontact=list(initial)
                    else:
                        readylistcontact=list(Acceptorder.objects.none())
                    print('readylistcontact1:',readylistcontact)
                    datetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
                    monthtoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m')
                    yeartoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y')
                    try:
                        getdailysales=Dailysales.objects.filter(user=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Sales', flat=True)[0]
                        timesheetupdate=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(Sales=getdailysales)
                    except IndexError:
                        timesheetupdate=timesheet.objects.none()
                        getdailysales=0
                    if getdailysales >= 2000 and timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday):
                        getinitialsalarytoday=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('ISalary', flat=True)
                        getASLBALANCEtodayi=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('ASLbalance', flat=True)
                        addbonusornot=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Identifybonus', flat=True)
                        if addbonusornot[0] == 'Added bonus':
                            pass
                        else:
                            twokeysalebonus=getinitialsalarytoday[0]+30
                            if getASLBALANCEtodayi[0] >= 30:
                                getASLBALANCEtoday=getASLBALANCEtodayi[0]-30
                                timesheetupdatetwo=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(ISalary=twokeysalebonus, ASLbalance=getASLBALANCEtoday,Identifybonus='Added bonus')
                            else:
                                getASLBALANCEtoday=0
                                addtofinalsalaryi=30-getASLBALANCEtodayi[0]
                                getfinalsalarytoday=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('FSalary', flat=True)
                                addtofinalsalary=addtofinalsalaryi+getfinalsalarytoday
                                timesheetupdatetwo=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(ISalary=twokeysalebonus, ASLbalance=getASLBALANCEtoday,Identifybonus='Added bonus',FSalary=addtofinalsalary)
                    return HttpResponseRedirect(str(request.GET.get('next')))
                elif checkdatetoday==gettimeobj:
                    
                    if Sales.objects.filter(user=userr,DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).count()==0:
                        objs = [Dailysales(
                            user=userr,
                            DateTime=daydistinct11,
                            Sales=salescalc,
                            Expenses=expenses,
                            Startstocks =starts,
                            Endstocks =ends,
                            Valuestocks =values,
                            Net=Neto,
                        )
                        ]
                    else:
                        objs = [Dailysales(
                            user=userr,
                            DateTime=daydistinct11.DateTime,
                            Sales=salescalc,
                            Expenses=expenses,
                            Startstocks =starts,
                            Endstocks =ends,
                            Valuestocks =values,
                            Net=Neto,
                        )
                        ]
                    deletelatest=getobjdate.delete()
                    ddailyi = Dailysales.objects.bulk_create(objs)
                    ddaily = Dailysales.objects.filter(user=userr).order_by('DateTime')
                    totalsales = ddaily.aggregate(Sum('Sales')).get('Sales__sum',0.00)
                    totalnet = ddaily.aggregate(Sum('Net')).get('Net__sum')
                    #for month 2 Dailysales
                    monthdistinct0=Dailysales.objects.filter(user=userr).values('DateTime__month').distinct()
                    monthdistinct1=Dailysales.objects.filter(user=userr).values_list('DateTime__month',flat=True).distinct()
                    i = 0
                    monthdistinct11=monthdistinct1.count()
                    

                    monthh={}
                    while i < monthdistinct11:
                        sample=monthdistinct1[i]
                        sample2=Dailysales.objects.filter(user=userr,DateTime__month=sample)

                        
                        monthlysales=sample2
                        
                        getmonth=monthlysales.values_list('DateTime__month',flat=True).first()
                    
                        if getmonth==1:
                            finalmonth='January'
                        elif getmonth==2:
                            finalmonth='February'
                        elif getmonth==3:
                            finalmonth='March'
                        elif getmonth==4:
                            finalmonth='April'
                        elif getmonth==5:
                            finalmonth='May'
                        elif getmonth==6:
                            finalmonth='June'
                        elif getmonth==7:
                            finalmonth='July'
                        elif getmonth==8:
                            finalmonth='August'
                        elif getmonth==9:
                            finalmonth='September'
                        elif getmonth==10:
                            finalmonth='October'
                        elif getmonth==11:
                            finalmonth='November'
                        elif getmonth==12:
                            finalmonth='December'
                        finalyear=str(monthlysales.values_list('DateTime__year',flat=True).first())
                        
                        month={}
                        monthtotalsalesi = monthlysales.aggregate(Sum('Sales')).get('Sales__sum')
                        
                        monthExpensesi= monthlysales.aggregate(Sum('Expenses')).get('Expenses__sum')
                        monthvalues=monthlysales.aggregate(Sum('Valuestocks')).get('Valuestocks__sum')
                        monthstarts=monthlysales.aggregate(Sum('Startstocks')).get('Startstocks__sum')
                        monthends=monthlysales.aggregate(Sum('Endstocks')).get('Endstocks__sum')
                        print('monthstarts: ',monthstarts,'monthvalues: ',monthvalues,'monthends: ',monthends)
                        month['monthdate']=finalmonth+", "+finalyear
                        month['monthtotalsales']='₱'+str(monthtotalsalesi)
                        month['monthExpenses']='₱'+(str(monthExpensesi))
                        calculate=monthtotalsalesi-(monthstarts+monthvalues-monthends)-monthExpensesi
                        if calculate<0:

                            month['monthCOGS']='₱0.00'
                            month['monthtotalnet']='₱0.00'
                        else:
                            month['monthCOGS']='₱'+(str(monthstarts+monthvalues-monthends))
                            month['monthtotalnet']='₱'+(str(monthtotalsalesi-(monthstarts+monthvalues-monthends)-monthExpensesi))
                        monthh[i]=month.values()
                        
                        i += 1
                    cogsss=(monthstarts+monthvalues-monthends)
                    print('cogsss1:',cogsss)
                    print('monthvalues1:',monthvalues)
                    monthly=monthh.values()
                    
                    #endfor month 2 Dailysales
                    if len(Acceptorder.objects.filter(Admin=userr, productname='Ready'))>0:
                        initial=Acceptorder.objects.filter(Admin=userr, productname='Ready').values_list('contactnumber', flat=True)
                        readylistcontact=list(initial)
                    else:
                        readylistcontact=list(Acceptorder.objects.none())
                    print('readylistcontact1:',readylistcontact)
                    datetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
                    monthtoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m')
                    yeartoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y')
                    try:
                        getdailysales=Dailysales.objects.filter(user=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Sales', flat=True)[0]
                        timesheetupdate=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(Sales=getdailysales)
                    except IndexError:
                        timesheetupdate=timesheet.objects.none()
                        getdailysales=0
                    if getdailysales >= 2000 and timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday):
                        getinitialsalarytoday=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('ISalary', flat=True)
                        getASLBALANCEtodayi=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('ASLbalance', flat=True)
                        addbonusornot=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Identifybonus', flat=True)
                        if addbonusornot[0] == 'Added bonus':
                            pass
                        else:
                            twokeysalebonus=getinitialsalarytoday[0]+30
                            if getASLBALANCEtodayi[0] >= 30:
                                getASLBALANCEtoday=getASLBALANCEtodayi[0]-30
                                timesheetupdatetwo=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(ISalary=twokeysalebonus, ASLbalance=getASLBALANCEtoday,Identifybonus='Added bonus')
                            else:
                                getASLBALANCEtoday=0
                                addtofinalsalaryi=30-getASLBALANCEtodayi[0]
                                getfinalsalarytoday=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('FSalary', flat=True)
                                addtofinalsalary=addtofinalsalaryi+getfinalsalarytoday
                                timesheetupdatetwo=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(ISalary=twokeysalebonus, ASLbalance=getASLBALANCEtoday,Identifybonus='Added bonus',FSalary=addtofinalsalary)
                    return HttpResponseRedirect(str(request.GET.get('next')))
                else:
                    ddaily = Dailysales.objects.filter(user=userr).order_by('DateTime')
                    totalsales = ddaily.aggregate(Sum('Sales')).get('Sales__sum',0.00)
                    totalnet = ddaily.aggregate(Sum('Net')).get('Net__sum')
                    #FOR MONTH
                    monthlysales=Dailysales.objects.filter(user=userr).order_by('DateTime')
                    monthtotalsales = ddaily.aggregate(Sum('Sales')).get('Sales__sum')
                    monthExpenses= ddaily.aggregate(Sum('Expenses')).get('Expenses__sum')
                    monthvalues=ddaily.aggregate(Sum('Valuestocks')).get('Valuestocks__sum')
                    monthstarts=ddaily.aggregate(Sum('Startstocks')).get('Startstocks__sum')
                    monthends=ddaily.aggregate(Sum('Endstocks')).get('Endstocks__sum')
                    monthCOGS=monthstarts+monthvalues-monthends
                    monthtotalnet=monthtotalsales-monthCOGS-monthExpenses
                    #END FOR MONTH)
                    if len(Acceptorder.objects.filter(Admin=userr, productname='Ready'))>0:
                        initial=Acceptorder.objects.filter(Admin=userr, productname='Ready').values_list('contactnumber', flat=True)
                        readylistcontact=list(initial)
                    else:
                        readylistcontact=list(Acceptorder.objects.none())
                    print('readylistcontact1:',readylistcontact)
                    return HttpResponseRedirect(str(request.GET.get('next')))
     else:
            userr=request.user.id
            if request.GET.get('acceptcontactno'):
                contactnumberaccept = request.GET.get('acceptcontactno')
                rider = request.GET.get('rider')
                getETA = request.GET.get('ETA')
                Accepted = Customer.objects.filter(Admin=userr,contactnumber=contactnumberaccept)
            
                objs = [Acceptorder(
                            Admin=Accepted.Admin,
                            Customername=Accepted.Customername,
                            codecoupon=Accepted.codecoupon,
                            discount=Accepted.discount or None,
                            Province=Accepted.Province,
                            MunicipalityCity=Accepted.MunicipalityCity,
                            Barangay=Accepted.Barangay,
                            StreetPurok=Accepted.StreetPurok,
                            Housenumber=Accepted.Housenumber or None,
                            LandmarksnNotes=Accepted.LandmarksnNotes or None,
                            DeliveryFee=Accepted.DeliveryFee or 0,
                            contactnumber=Accepted.contactnumber,
                            Rider=rider,
                            productname=Accepted.productname,
                            Category=Accepted.Category,
                            Subcategory=Accepted.Subcategory or None,
                            Size=Accepted.Size  or None,
                            PSize=Accepted.PSize or None,
                            Addons=Accepted.Addons or None,
                            QtyAddons= Accepted.QtyAddons or 0,
                            Price=Accepted.Price,
                            Subtotal = Accepted.Subtotal,
                            GSubtotal=Accepted.GSubtotal,
                            Cost=Accepted.Cost,
                            Qty=Accepted.Qty,
                            Bill=Accepted.Bill or 0,
                            Change=Accepted.Change or 0,
                            ETA=getETA,
                            MOP=Accepted.MOP,
                            ordertype='Online',
                            Timetodeliver=Accepted.Timetodeliver,
                            ScheduleTime=Accepted.ScheduleTime,
                            gpslat = Accepted.gpslat,
                            gpslng = Accepted.gpslng,
                            gpsaccuracy = Accepted.gpsaccuracy,
                            pinnedlat = Accepted.pinnedlat,
                            pinnedlng = Accepted.pinnedlng,
                            tokens = Accepted.tokens or None,
                            DateTime=Accepted.DateTime,
                    )
                    for Accepted in Accepted
                ]
                Acceptorders = Acceptorder.objects.bulk_create(objs)
                Accepted.delete()
                messageacknowledgetokeni=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberaccept).values_list('tokens',flat=True).first()
                messageacknowledgetoken = ["dHEGNR4YGO8a-AVQWfIE33:APA91bGkNxUcRZEHJQCkUy3k3THUEMxml9q4819bDQw1b8UkD05qThidgXq3Nnr46I1pwQikZgwiGFuBgKwUxHO6kUXI9KId3ZK0fQ0zi83QegTtVimqV18a2pDqBq5qnJf-BK74Z1nL", messageacknowledgetokeni]
                acknowledge(request, messageacknowledgetoken)
                MessageRider(request)

                return HttpResponseRedirect('/index/pos')

            if len(Acceptorder.objects.filter(Admin=userr))>0:
                acceptedorder = Acceptorder.objects.filter(Admin=userr).distinct('contactnumber')
                acceptedorderall = Acceptorder.objects.filter(Admin=userr)
            else:
                acceptedorder = Acceptorder.objects.none()
                acceptedorderall = Acceptorder.objects.none()
            viewordersacceptii={}
            arrayoneaccept=[]
            contactdistincteraccepti = Acceptorder.objects.filter(Admin=userr).distinct('contactnumber')
            contactdistincteraccept=contactdistincteraccepti.values_list('contactnumber',flat=True)
            i=0
            for cndistinctaccept in contactdistincteraccept:
                arrayseparatoracceptiii=Acceptorder.objects.filter(Admin=userr,contactnumber=cndistinctaccept).exclude(productname='Ready').values()
                arrayseparatoraccepti = list(arrayseparatoracceptiii)
                arrayseparatoraccept=json.dumps(arrayseparatoraccepti, cls=JSONEncoder)
                viewordersacceptii[contactdistincteraccept[i]]=arrayseparatoraccept
                i=i+1
            viewordersaccepti=viewordersacceptii
            viewordersaccept=json.dumps(viewordersaccepti, cls=JSONEncoder)
        

            if (request.GET.get('rider') == "") and (request.GET.get('contactnoreject') or request.GET.get('contactnoaccepted')):
                if request.GET.get('contactnoreject'):
                    contactnumberreject = request.GET.get('contactnoreject')
                    Rejected = Customer.objects.filter(Admin=userr,contactnumber=contactnumberreject)
                elif request.GET.get('contactnoaccepted'):
                    contactnumberreject = request.GET.get('contactnoaccepted')
                    if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject, productname='Ready'):
                        deletethis=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject, productname='Ready')
                        deletethis.delete()
                    Rejected = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberreject)
            
                objs = [Rejectorder(
                            Admin=userr,
                            Customername=Rejected.Customername,
                            codecoupon=Rejected.codecoupon,
                            discount=Rejected.discount or None,
                            Province=Rejected.Province,
                            MunicipalityCity=Rejected.MunicipalityCity,
                            Barangay=Rejected.Barangay,
                            StreetPurok=Rejected.StreetPurok,
                            Housenumber=Rejected.Housenumber or None,
                            LandmarksnNotes=Rejected.LandmarksnNotes or None,
                            DeliveryFee=Rejected.DeliveryFee or 0,
                            contactnumber=Rejected.contactnumber,
                            productname=Rejected.productname,
                            Category=Rejected.Category,
                            Subcategory=Rejected.Subcategory or None,
                            Size=Rejected.Size  or None,
                            PSize=Rejected.PSize or None,
                            Addons=Rejected.Addons or None,
                            QtyAddons= Rejected.QtyAddons or 0,
                            Price=Rejected.Price,
                            Subtotal = Rejected.Subtotal,
                            GSubtotal=Rejected.GSubtotal,
                            Cost=Rejected.Cost,
                            Qty=Rejected.Qty,
                            Bill=Rejected.Bill or 0,
                            Change=Rejected.Change or 0,
                            MOP=Rejected.MOP,
                            ordertype='Online',
                            Timetodeliver=Rejected.Timetodeliver,
                            ScheduleTime=Rejected.ScheduleTime,
                            gpslat = Rejected.gpslat,
                            gpslng = Rejected.gpslng,
                            gpsaccuracy = Rejected.gpsaccuracy,
                            pinnedlat = Rejected.pinnedlat,
                            pinnedlng = Rejected.pinnedlng,
                            tokens = Rejected.tokens  or None,
                            DateTime=Rejected.DateTime,
                    )
                    for Rejected in Rejected
                ]
                Rejectorders = Rejectorder.objects.bulk_create(objs)
                Rejected.delete()
                return HttpResponseRedirect('/index/pos')

            if len(Rejectorder.objects.filter(Admin=userr))>0:
                rejectedorder = Rejectorder.objects.filter(Admin=userr).distinct('contactnumber')
                rejectedorderall = Rejectorder.objects.filter(Admin=userr)
            else:
                rejectedorder = Rejectorder.objects.none()
                rejectedorderall = Rejectorder.objects.none()
            viewordersrejectii={}
            arrayonereject=[]
            contactdistincterrejecti = Rejectorder.objects.filter(Admin=userr).distinct('contactnumber')
            contactdistincterreject=contactdistincterrejecti.values_list('contactnumber',flat=True)
            i=0
            for cndistinctreject in contactdistincterreject:
                arrayseparatorrejectiii=Rejectorder.objects.filter(Admin=userr,contactnumber=cndistinctreject).exclude(productname='Ready').values()
                arrayseparatorrejecti = list(arrayseparatorrejectiii)
                arrayseparatorreject=json.dumps(arrayseparatorrejecti, cls=JSONEncoder)
                viewordersrejectii[contactdistincterreject[i]]=arrayseparatorreject
                i=i+1
            viewordersrejecti=viewordersrejectii
            viewordersreject=json.dumps(viewordersrejecti, cls=JSONEncoder)

        

            if request.GET.get('contactnorestore'):
                contactnumberrestore = request.GET.get('contactnorestore')
                Restored = Rejectorder.objects.filter(Admin=userr,contactnumber=contactnumberrestore)
            
                objs = [Customer(
                            Admin=userr,
                            Customername=Restored.Customername,
                            codecoupon=Restored.codecoupon,
                            discount=Restored.discount or None,
                            Province=Restored.Province,
                            MunicipalityCity=Restored.MunicipalityCity,
                            Barangay=Restored.Barangay,
                            StreetPurok=Restored.StreetPurok,
                            Housenumber=Restored.Housenumber or None,
                            LandmarksnNotes=Restored.LandmarksnNotes or None,
                            DeliveryFee=Restored.DeliveryFee or 0,
                            contactnumber=Restored.contactnumber,
                            productname=Restored.productname,
                            Category=Restored.Category,
                            Subcategory=Restored.Subcategory or None,
                            Size=Restored.Size  or None,
                            PSize=Restored.PSize or None,
                            Addons=Restored.Addons or None,
                            QtyAddons= Restored.QtyAddons or 0,
                            Price=Restored.Price,
                            Subtotal = Restored.Subtotal,
                            GSubtotal=Restored.GSubtotal,
                            Cost=Restored.Cost,
                            Qty=Restored.Qty,
                            Bill=Restored.Bill or 0,
                            Change=Restored.Change or 0,
                            MOP=Restored.MOP,
                            ordertype='Online',
                            Timetodeliver=Restored.Timetodeliver,
                            ScheduleTime=Restored.ScheduleTime,
                            gpslat = Restored.gpslat,
                            gpslng = Restored.gpslng,
                            gpsaccuracy = Restored.gpsaccuracy,
                            pinnedlat = Restored.pinnedlat,
                            pinnedlng = Restored.pinnedlng,
                            tokens = Restored.tokens  or None,
                            DateTime=Restored.DateTime,
                    )
                    for Restored in Restored
                ]
                Restore = Customer.objects.bulk_create(objs)
                Restored.delete()
                return HttpResponseRedirect('/index/pos')

            if len(Customer.objects.filter(Admin=userr))>0:
                onlineorder = Customer.objects.filter(Admin=userr).distinct('contactnumber')
                onlineorderall = Customer.objects.filter(Admin=userr)
            else:
                onlineorder = Customer.objects.none()
                onlineorderall = Customer.objects.none()
            viewordersii={}
            arrayone=[]
            contactdistincteri = Customer.objects.filter(Admin=userr).distinct('contactnumber')
            contactdistincter=contactdistincteri.values_list('contactnumber',flat=True)
            i=0
            for cndistinct in contactdistincter:  
                arrayseparatoriii=Customer.objects.filter(Admin=userr,contactnumber=cndistinct).values()
                arrayseparatori = list(arrayseparatoriii)
                arrayseparator=json.dumps(arrayseparatori, cls=JSONEncoder)
                viewordersii[contactdistincter[i]]=arrayseparator
                i=i+1
            viewordersi=viewordersii
            vieworders=json.dumps(viewordersi, cls=JSONEncoder)

            onlineordercounter = len(Customer.objects.filter(Admin=userr).distinct('contactnumber'))

            if is_ajax(request=request) and request.POST.get("Ready"):
                contactnumberready = request.POST.get('Ready')
                Readyadd = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).first()
                Readyacceptorder=Acceptorder.objects.create(
                            Admin=userr,
                            Customername=Readyadd.Customername,
                            codecoupon=Readyadd.codecoupon,
                            discount=Readyadd.discount or None,
                            Province=Readyadd.Province,
                            MunicipalityCity=Readyadd.MunicipalityCity,
                            Barangay=Readyadd.Barangay,
                            StreetPurok=Readyadd.StreetPurok,
                            Housenumber=Readyadd.Housenumber or None,
                            LandmarksnNotes=Readyadd.LandmarksnNotes or None,
                            DeliveryFee=0,
                            contactnumber=Readyadd.contactnumber,
                            productname='Ready',
                            Category=Readyadd.Category,
                            Subcategory=None,
                            Size=None,
                            PSize=None,
                            Addons=None,
                            QtyAddons= 0,
                            Price=0,
                            Subtotal = 0,
                            GSubtotal=Readyadd.GSubtotal,
                            Cost=0,
                            Qty=0,
                            Bill=Readyadd.Bill or 0,
                            Change=Readyadd.Change or 0,
                            MOP=Readyadd.MOP,
                            ordertype='Online',
                            Timetodeliver=Readyadd.Timetodeliver,
                            ScheduleTime=Readyadd.ScheduleTime,
                            gpslat = Readyadd.gpslat,
                            gpslng = Readyadd.gpslng,
                            gpsaccuracy = Readyadd.gpsaccuracy,
                            pinnedlat = Readyadd.pinnedlat,
                            pinnedlng = Readyadd.pinnedlng,
                            tokens = Readyadd.tokens  or None,
                            DateTime=Readyadd.DateTime,
                            )
                Readyacceptorder.save()
                if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready, MOP='COD'):
                    orderprepared(request)
                messageacknowledgetokeni=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('tokens',flat=True).first()
                messageacknowledgetoken = ["dHEGNR4YGO8a-AVQWfIE33:APA91bGkNxUcRZEHJQCkUy3k3THUEMxml9q4819bDQw1b8UkD05qThidgXq3Nnr46I1pwQikZgwiGFuBgKwUxHO6kUXI9KId3ZK0fQ0zi83QegTtVimqV18a2pDqBq5qnJf-BK74Z1nL", messageacknowledgetokeni]
                if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('MOP',flat=True).first() == 'COD' or Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberready).values_list('MOP',flat=True).first() == 'GcashDelivery':
                    deliveryotwRider(request)
                    deliveryotwCustomer(request , messageacknowledgetoken)
                else:
                    pickupCustomer(request , messageacknowledgetoken)
                return JsonResponse({'Ready':'Ready'})
            if is_ajax(request=request) and request.GET.get("apini"):
                onlineordercounterf = onlineordercounter
                onlineorderf = [serializers.serialize('json',onlineorder, cls=JSONEncoder),vieworders]
                return JsonResponse({'onlineorderf':onlineorderf})
            
            if is_ajax(request=request) and request.POST.get('doneorders'):
                contactnumberdonei = json.loads(request.POST.get('doneorders'))
                contactnumberdone = contactnumberdonei[0]['contactnumber']
                if contactnumberdonei[0]['codecoupon']:
                    if couponlist.objects.filter(code=contactnumberdonei[0]['codecoupon']):
                        codeconsumereducerii=couponlist.objects.get(code=contactnumberdonei[0]['codecoupon'])
                        if codeconsumereducerii.is_consumable == True and codeconsumereducerii.redeemlimit>0:
                            codeconsumereduceri=int(codeconsumereducerii.redeemlimit)-1
                            codeconsumereducer=couponlist.objects.filter(code=contactnumberdonei[0]['codecoupon']).update(redeemlimit=codeconsumereduceri)
                        else:
                            pass
                    else:
                        pass
                else:
                    pass
                if Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone, productname='Ready'):
                    deletethis=Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone, productname='Ready')
                    deletethis.delete()
                Done = Acceptorder.objects.filter(Admin=userr,contactnumber=contactnumberdone)
                try:
                    Sales.objects.filter(contactnumber=contactnumberdonei[0]['contactnumber'], CusName=contactnumberdonei[0]['Customername'], productname='DeliveryFee', DateTime=contactnumberdonei[0]['DateTime'])
                    deliveryfeepaid='true'
                except Sales.DoesNotExist:
                    deliveryfeepaid='false'
                if contactnumberdonei[0]['DeliveryFee'] != None and deliveryfeepaid == 'true':
                    devfeeassales=Sales.objects.create(
                            user=userr,
                            CusName=contactnumberdonei[0]['Customername'],
                            codecoupon=contactnumberdonei[0]['codecoupon'] or None,
                            discount=contactnumberdonei[0]['discount'] or None,
                            Province=contactnumberdonei[0]['Province'],
                            MunicipalityCity=contactnumberdonei[0]['MunicipalityCity'],
                            Barangay=contactnumberdonei[0]['Barangay'],
                            StreetPurok=contactnumberdonei[0]['StreetPurok'],
                            Housenumber=contactnumberdonei[0]['Housenumber'] or None,
                            LandmarksnNotes=contactnumberdonei[0]['LandmarksnNotes'] or None,
                            DeliveryFee=contactnumberdonei[0]['DeliveryFee'] or None,
                            contactnumber=contactnumberdonei[0]['contactnumber'],
                            productname='DeliveryFee',
                            Category='DeliveryFee',
                            Subcategory='DeliveryFee',
                            Size=None,
                            PSize=None,
                            Addons=None,
                            QtyAddons=0,
                            Price=contactnumberdonei[0]['DeliveryFee'],
                            Subtotal = contactnumberdonei[0]['DeliveryFee'],
                            GSubtotal=contactnumberdonei[0]['GSubtotal'],
                            Cost=0,
                            Qty=1,
                            Bill=contactnumberdonei[0]['Bill'] or 0,
                            Change=contactnumberdonei[0]['Change'] or 0,
                            MOP=contactnumberdonei[0]['MOP'],
                            ordertype='Online',
                            Timetodeliver=contactnumberdonei[0]['Timetodeliver'] or None,
                            ScheduleTime=contactnumberdonei[0]['ScheduleTime'] or None,
                            gpslat = contactnumberdonei[0]['gpslat'],
                            gpslng = contactnumberdonei[0]['gpslng'],
                            gpsaccuracy = contactnumberdonei[0]['gpsaccuracy'],
                            pinnedlat = contactnumberdonei[0]['pinnedlat'],
                            pinnedlng = contactnumberdonei[0]['pinnedlng'],
                            tokens = contactnumberdonei[0]['tokens'] or None,
                            DateTime=contactnumberdonei[0]['DateTime'],
                    )
                    devfeeassales.save()
                if contactnumberdonei[0]['discount']:
                    objs = [Sales(
                                user=userr,
                                CusName=Done.Customername,
                                codecoupon=Done.codecoupon,
                                discount=Done.discount or None,
                                Province=Done.Province,
                                MunicipalityCity=Done.MunicipalityCity,
                                Barangay=Done.Barangay,
                                StreetPurok=Done.StreetPurok,
                                Housenumber=Done.Housenumber or None,
                                LandmarksnNotes=Done.LandmarksnNotes or None,
                                DeliveryFee=Done.DeliveryFee or None,
                                contactnumber=Done.contactnumber,
                                productname=Done.productname,
                                Category=Done.Category,
                                Subcategory=Done.Subcategory or None,
                                Size=Done.Size  or None,
                                PSize=Done.PSize or None,
                                Addons=Done.Addons or None,
                                QtyAddons= Done.QtyAddons or 0,
                                Price=Done.Price,
                                Subtotal = Done.Subtotal-((Done.Subtotal)*(Decimal(int(Done.discount)/100))),
                                GSubtotal=Done.GSubtotal,
                                Cost=Done.Cost,
                                Qty=Done.Qty,
                                Bill=Done.Bill or 0,
                                Change=Done.Change or 0,
                                MOP=Done.MOP,
                                ordertype='Online',
                                Timetodeliver=Done.Timetodeliver,
                                ScheduleTime=Done.ScheduleTime,
                                gpslat = Done.gpslat,
                                gpslng = Done.gpslng,
                                gpsaccuracy = Done.gpsaccuracy,
                                pinnedlat = Done.pinnedlat,
                                pinnedlng = Done.pinnedlng,
                                tokens = Done.tokens or None,
                                DateTime=Done.DateTime,
                        )
                        for Done in Done
                    ]
                else:
                    objs = [Sales(
                                user=userr,
                                CusName=Done.Customername,
                                codecoupon=Done.codecoupon,
                                discount=Done.discount or None,
                                Province=Done.Province,
                                MunicipalityCity=Done.MunicipalityCity,
                                Barangay=Done.Barangay,
                                StreetPurok=Done.StreetPurok,
                                Housenumber=Done.Housenumber or None,
                                LandmarksnNotes=Done.LandmarksnNotes or None,
                                DeliveryFee=Done.DeliveryFee or None,
                                contactnumber=Done.contactnumber,
                                productname=Done.productname,
                                Category=Done.Category,
                                Subcategory=Done.Subcategory or None,
                                Size=Done.Size  or None,
                                PSize=Done.PSize or None,
                                Addons=Done.Addons or None,
                                QtyAddons= Done.QtyAddons or 0,
                                Price=Done.Price,
                                Subtotal = Done.Subtotal,
                                GSubtotal=Done.GSubtotal,
                                Cost=Done.Cost,
                                Qty=Done.Qty,
                                Bill=Done.Bill or 0,
                                Change=Done.Change or 0,
                                MOP=Done.MOP,
                                ordertype='Online',
                                Timetodeliver=Done.Timetodeliver,
                                ScheduleTime=Done.ScheduleTime,
                                gpslat = Done.gpslat,
                                gpslng = Done.gpslng,
                                gpsaccuracy = Done.gpsaccuracy,
                                pinnedlat = Done.pinnedlat,
                                pinnedlng = Done.pinnedlng,
                                tokens = Done.tokens or None,
                                DateTime=Done.DateTime,
                        )
                        for Done in Done
                    ]
                Salesorders = Sales.objects.bulk_create(objs)
                Done.delete()
                datetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
                monthtoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m')
                yeartoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y')
                try:
                    getdailysales=Dailysales.objects.filter(user=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Sales', flat=True)[0]
                    timesheetupdate=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(Sales=getdailysales)
                except IndexError:
                    timesheetupdate=timesheet.objects.none()
                    getdailysales=0
                if getdailysales >= 2000 and timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday):
                    getinitialsalarytoday=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('ISalary', flat=True)
                    getASLBALANCEtodayi=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('ASLbalance', flat=True)
                    addbonusornot=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('Identifybonus', flat=True)
                    if addbonusornot[0] == 'Added bonus':
                        pass
                    else:
                        twokeysalebonus=getinitialsalarytoday[0]+30
                        if getASLBALANCEtodayi[0] >= 30:
                            getASLBALANCEtoday=getASLBALANCEtodayi[0]-30
                            timesheetupdatetwo=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(ISalary=twokeysalebonus, ASLbalance=getASLBALANCEtoday,Identifybonus='Added bonus')
                        else:
                            getASLBALANCEtoday=0
                            addtofinalsalaryi=30-getASLBALANCEtodayi[0]
                            getfinalsalarytoday=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values_list('FSalary', flat=True)
                            addtofinalsalary=addtofinalsalaryi+getfinalsalarytoday
                            timesheetupdatetwo=timesheet.objects.filter(Admin=userr, DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).update(ISalary=twokeysalebonus, ASLbalance=getASLBALANCEtoday,Identifybonus='Added bonus',FSalary=addtofinalsalary)
                return HttpResponseRedirect('/index/pos')



            notifyorder=acknowledgedstockorder.objects.filter(CusName="Notify",user=userr).count()
            if acknowledgedstockorder.objects.all().count()==0:
                notifyadmin=submitstockorder.objects.all().count()
            else:
                notifyadmin=0
            print('userr:',userr) 
            if punchedprod.objects.filter(user=userr).count()==0:
                punchedtotal=0
            else:
                punchedtotal=punchedprod.objects.filter(user=userr).aggregate(Sum('Subtotal')).get('Subtotal__sum')
            notifyorder=acknowledgedstockorder.objects.filter(CusName="Notify",user=userr).count()
            if acknowledgedstockorder.objects.all().count()==0:
                notifyadmin=submitstockorder.objects.all().count()
            else:
                notifyadmin=0
            datetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
            monthtoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%m')
            yeartoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y')
            countsalestoday=Sales.objects.filter(user=userr,DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).count()
            
            da1daily=Sales.objects.filter(user=userr,DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday)
            if Sales.objects.filter(user=userr).count()==0:
                 dd=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
                 daydaily={'user':userr,'Qty':0,'Subtotal':0,'Cost':0,'Price':0,'Amount':0}
                 
                 
            elif Sales.objects.filter(user=userr,DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).count()==0:
                 dd=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d')
                 daydaily={'user':userr,'Qty':0,'Subtotal':0,'Cost':0,'Price':0,'Amount':0}
                 
                 

            elif Sales.objects.filter(user=userr).values('DateTime__day').count()==1:
                daydistinct1=Sales.objects.filter(user=userr).values('DateTime__day').distinct().first()
                for DateTime__day,dd in daydistinct1.items():
                    daydaily=Sales.objects.filter(user=userr,DateTime__day=dd)
                    
                    
            else:
                daydistinct0=Sales.objects.filter(user=userr).values('DateTime__day').distinct()
                daydistinct1=Sales.objects.filter(user=userr).values('DateTime__day').distinct().first()
                for daydistinct in daydistinct0:
                    for DateTime__day, dd in daydistinct.items():
                        daydaily=Sales.objects.filter(user=userr,DateTime__day=dd)
                        
                        
            
            if Sales.objects.filter(user=userr).count()==0:
                daydistinct11=datetime.datetime.now(pytz.timezone('Asia/Singapore'))
                daydaily['subtotalCosti']=(daydaily['Qty']*daydaily['Cost'])
                subtotalcost=daydaily['subtotalCosti']
                salescalc=daydaily['Subtotal']
                Neto=salescalc-subtotalcost
                starts=daydaily['Amount']
                ends=daydaily['Amount']
                values=daydaily['Amount']
                expenses=daydaily['Amount']

            else:
                if Sales.objects.filter(user=userr,DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).count()==0:
                    daydistinct11=datetime.datetime.now(pytz.timezone('Asia/Singapore'))
                    daydaily['subtotalCosti']=(daydaily['Qty']*daydaily['Cost'])
                    subtotalcost=daydaily['subtotalCosti']
                    salescalc=daydaily['Subtotal']
                    Neto=salescalc-subtotalcost
                    starts=daydaily['Amount']
                    ends=daydaily['Amount']
                    values=daydaily['Amount']
                    expenses=daydaily['Amount']
                else:
                    daydistinct11=Sales.objects.filter(user=userr,DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).latest('DateTime__day')
                    
                    subtotalcosti=Sales.objects.filter(user=userr,DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).values('DateTime__day').annotate(subtotalCosti=F('Qty')*F('Cost'))
                    subtotalcost=subtotalcosti.aggregate(Sum('subtotalCosti')).get('subtotalCosti__sum')
                    
                    salescalc=da1daily.aggregate(Sum('Subtotal')).get("Subtotal__sum",0.00)
                    
                    Neto=salescalc-subtotalcost
                    
                    endsi=da1daily.filter(Subcategorys__saesubcatchoices="End Stock").aggregate(Sum('Amount')).get("Amount__sum")
                    valuesi=da1daily.filter(Subcategorys__saesubcatchoices="Value Stock").aggregate(Sum('Amount')).get("Amount__sum")
                    
                    startsi=da1daily.filter(Subcategorys__saesubcatchoices="Start Stock").aggregate(Sum('Amount')).get("Amount__sum")
                    expensesi=da1daily.filter(Categoryaes__saecatchoices="Expenses").aggregate(Sum('Amount')).get("Amount__sum")
                    if expensesi==None:
                        expenses=0
                    else:
                        expenses=expensesi
                    if startsi==None:
                        starts=0
                    else:
                        starts=startsi
                    if endsi==None:
                        ends=0
                    else:
                        ends=endsi
                    if valuesi==None:
                        values=0
                    else:
                        values=valuesi

            if Dailysales.objects.filter(user=userr).count()==0:
                if Sales.objects.filter(user=userr).count()==0:
                    objs = [Dailysales(
                        user=userr,
                        DateTime=daydistinct11,
                        Sales=salescalc,
                        Expenses=expenses,
                        Startstocks = starts,
                        Endstocks = ends,
                        Valuestocks = values,
                        Net=Neto,
                    )
                    ]
                else:

                    objs = [Dailysales(
                        user=userr,
                        DateTime=daydistinct11.DateTime,
                        Sales=salescalc,
                        Expenses=expenses,
                        Startstocks =starts,
                        Endstocks =ends,
                        Valuestocks =values,
                        Net=Neto,
                    )
                    ]
                ddailyi = Dailysales.objects.bulk_create(objs)
                ddaily = Dailysales.objects.filter(user=userr).order_by('DateTime')
                totalsales = ddaily.aggregate(Sum('Sales')).get('Sales__sum',0.00)
                totalnet = ddaily.aggregate(Sum('Net')).get('Net__sum')
                #FOR MONTH
                monthly={}
                monthlysales=Dailysales.objects.filter(user=userr).order_by('DateTime')
                monthtotalsalesi = ddaily.aggregate(Sum('Sales')).get('Sales__sum')
                monthExpensesi= ddaily.aggregate(Sum('Expenses')).get('Expenses__sum')
                monthvalues=ddaily.aggregate(Sum('Valuestocks')).get('Valuestocks__sum')
                monthstarts=ddaily.aggregate(Sum('Startstocks')).get('Startstocks__sum')
                monthends=ddaily.aggregate(Sum('Endstocks')).get('Endstocks__sum')
                monthly['monthCOGS']=monthstarts+monthvalues-monthends
                monthly['monthtotalsales']=monthtotalsalesi
                monthly['monthExpenses']=monthExpensesi
                monthly['monthtotalnet']=monthly['monthtotalsales']-monthly['monthCOGS']-monthly['monthExpenses']
                if len(Acceptorder.objects.filter(Admin=userr, productname='Ready'))>0:
                    initial=Acceptorder.objects.filter(Admin=userr, productname='Ready').values_list('contactnumber', flat=True)
                    readylistcontact=list(initial)
                else:
                    readylistcontact=list(Acceptorder.objects.none())
                print('readylistcontact1:',readylistcontact)
                #END FOR MONTH
                return render(request, 'kgddashboard.html',{'readylistcontact':readylistcontact, 'onlineordercounter':onlineordercounter,'viewordersreject':viewordersreject,'rejectedorder':rejectedorder,'viewordersaccept':viewordersaccept,'acceptedorder':acceptedorder,'onlineorder':onlineorder,'notifyadmin':notifyadmin,'notifyorder':notifyorder,'monthly':monthly,'ddaily':ddaily,'totalnet':totalnet,'totalsales':totalsales})
            else:
                getobjdate=Dailysales.objects.filter(user=userr).latest('DateTime')
                subuk=getobjdate.DateTime
                gettimeobj = localtime(subuk).strftime('%b:%d')
                print('gettimeobj:  ',gettimeobj)
                checkdatetoday=datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%b:%d')
                print('checkdatetoday:  ',checkdatetoday)
                if checkdatetoday!=gettimeobj:
                    if Sales.objects.filter(user=userr,DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).count()==0:
                        objs = [Dailysales(
                            user=userr,
                            DateTime=daydistinct11,
                            Sales=salescalc,
                            Expenses=expenses,
                            Startstocks =starts,
                            Endstocks =ends,
                            Valuestocks =values,
                            Net=Neto,
                        )
                        ]
                    else:
                        objs = [Dailysales(
                            user=userr,
                            DateTime=daydistinct11.DateTime,
                            Sales=salescalc,
                            Expenses=expenses,
                            Startstocks =starts,
                            Endstocks =ends,
                            Valuestocks =values,
                            Net=Neto,
                        )
                        ]
                    ddailyi = Dailysales.objects.bulk_create(objs)
                    ddaily = Dailysales.objects.filter(user=userr).order_by('DateTime')
                    totalsales = ddaily.aggregate(Sum('Sales')).get('Sales__sum',0.00)
                    totalnet = ddaily.aggregate(Sum('Net')).get('Net__sum')
                    #for month 2 Dailysales
                    monthdistinct0=Dailysales.objects.filter(user=userr).values('DateTime__month').distinct()
                    monthdistinct1=Dailysales.objects.filter(user=userr).values_list('DateTime__month',flat=True).distinct()
                    i = 0
                    monthdistinct11=monthdistinct1.count()
                    

                    monthh={}
                    while i < monthdistinct11:
                        sample=monthdistinct1[i]
                        sample2=Dailysales.objects.filter(user=userr,DateTime__month=sample)

                        
                        monthlysales=sample2
                        
                        getmonth=monthlysales.values_list('DateTime__month',flat=True).first()
                    
                        if getmonth==1:
                            finalmonth='January'
                        elif getmonth==2:
                            finalmonth='February'
                        elif getmonth==3:
                            finalmonth='March'
                        elif getmonth==4:
                            finalmonth='April'
                        elif getmonth==5:
                            finalmonth='May'
                        elif getmonth==6:
                            finalmonth='June'
                        elif getmonth==7:
                            finalmonth='July'
                        elif getmonth==8:
                            finalmonth='August'
                        elif getmonth==9:
                            finalmonth='September'
                        elif getmonth==10:
                            finalmonth='October'
                        elif getmonth==11:
                            finalmonth='November'
                        elif getmonth==12:
                            finalmonth='December'
                        finalyear=str(monthlysales.values_list('DateTime__year',flat=True).first())
                        
                        month={}
                        
                        monthtotalsalesi = monthlysales.aggregate(Sum('Sales')).get('Sales__sum')
                        
                        monthExpensesi= monthlysales.aggregate(Sum('Expenses')).get('Expenses__sum')
                        monthvalues=monthlysales.aggregate(Sum('Valuestocks')).get('Valuestocks__sum')
                        monthstarts=monthlysales.aggregate(Sum('Startstocks')).get('Startstocks__sum')
                        monthends=monthlysales.aggregate(Sum('Endstocks')).get('Endstocks__sum')
                        month['monthdate']=finalmonth+", "+finalyear
                        month['monthtotalsales']='₱'+str(monthtotalsalesi)
                        month['monthExpenses']='₱'+(str(monthExpensesi))
                        calculate=monthtotalsalesi-(monthstarts+monthvalues-monthends)-monthExpensesi
                        if calculate<0:
                            month['monthCOGS']='₱0.00'
                            month['monthtotalnet']='₱0.00'
                        else:
                            month['monthCOGS']='₱'+(str(monthstarts+monthvalues-monthends))
                            month['monthtotalnet']='₱'+(str(monthtotalsalesi-(monthstarts+monthvalues-monthends)-monthExpensesi))
                        monthh[i]=month.values()
                        
                        i += 1
                    
                    monthly=monthh.values()
                    cogsss=(monthstarts+monthvalues-monthends)
                    print('cogsss2:',cogsss)
                    identifier=Dailysales.objects.filter(user=userr,DateTime__month=3)
                    monthExpensesiu= identifier.aggregate(Sum('Expenses')).get('Expenses__sum')
                    monthvaluesu=identifier.aggregate(Sum('Valuestocks')).get('Valuestocks__sum')
                    monthstartsu=identifier.aggregate(Sum('Startstocks')).get('Startstocks__sum')
                    monthendsu=identifier.aggregate(Sum('Endstocks')).get('Endstocks__sum')
                    expen='₱'+(str(monthExpensesiu))
                    monthtotalsalesiu = identifier.aggregate(Sum('Sales')).get('Sales__sum')
                    cogs='₱'+(str(monthstartsu+monthvaluesu-monthendsu))
                    net='₱'+(str(monthtotalsalesiu-(monthstartsu+monthvaluesu-monthendsu)-monthExpensesiu))
                    print('monthstarts: ',monthstartsu,'    monthvalues: ',monthvaluesu,'   monthends:',monthendsu,'    cogs:  ',cogs)
                    #endfor month 2 Dailysales
                    if len(Acceptorder.objects.filter(Admin=userr, productname='Ready'))>0:
                        initial=Acceptorder.objects.filter(Admin=userr, productname='Ready').values_list('contactnumber', flat=True)
                        readylistcontact=list(initial)
                    else:
                        readylistcontact=list(Acceptorder.objects.none())
                    print('readylistcontact1:',readylistcontact)
                    return render(request, 'kgddashboard.html',{'readylistcontact':readylistcontact, 'onlineordercounter':onlineordercounter,'viewordersreject':viewordersreject,'rejectedorder':rejectedorder,'viewordersaccept':viewordersaccept,'acceptedorder':acceptedorder,'onlineorder':onlineorder,'notifyadmin':notifyadmin,'notifyorder':notifyorder,'userr':userr,'monthly':monthly,'ddaily':ddaily,'totalnet':totalnet,'totalsales':totalsales})
                elif checkdatetoday==gettimeobj:
                    
                    if Sales.objects.filter(user=userr,DateTime__day=datetoday,DateTime__month=monthtoday,DateTime__year=yeartoday).count()==0:
                        objs = [Dailysales(
                            user=userr,
                            DateTime=daydistinct11,
                            Sales=salescalc,
                            Expenses=expenses,
                            Startstocks =starts,
                            Endstocks =ends,
                            Valuestocks =values,
                            Net=Neto,
                        )
                        ]
                    else:
                        objs = [Dailysales(
                            user=userr,
                            DateTime=daydistinct11.DateTime,
                            Sales=salescalc,
                            Expenses=expenses,
                            Startstocks =starts,
                            Endstocks =ends,
                            Valuestocks =values,
                            Net=Neto,
                        )
                        ]
                    deletelatest=getobjdate.delete()
                    ddailyi = Dailysales.objects.bulk_create(objs)
                    ddaily = Dailysales.objects.filter(user=userr).order_by('DateTime')
                    totalsales = ddaily.aggregate(Sum('Sales')).get('Sales__sum',0.00)
                    totalnet = ddaily.aggregate(Sum('Net')).get('Net__sum')
                    #for month 2 Dailysales
                    monthdistinct0=Dailysales.objects.filter(user=userr).values('DateTime__month').distinct()
                    monthdistinct1=Dailysales.objects.filter(user=userr).values_list('DateTime__month',flat=True).distinct()
                    i = 0
                    monthdistinct11=monthdistinct1.count()
                    

                    monthh={}
                    while i < monthdistinct11:
                        sample=monthdistinct1[i]
                        sample2=Dailysales.objects.filter(user=userr,DateTime__month=sample)

                        
                        monthlysales=sample2
                        
                        getmonth=monthlysales.values_list('DateTime__month',flat=True).first()
                    
                        if getmonth==1:
                            finalmonth='January'
                        elif getmonth==2:
                            finalmonth='February'
                        elif getmonth==3:
                            finalmonth='March'
                        elif getmonth==4:
                            finalmonth='April'
                        elif getmonth==5:
                            finalmonth='May'
                        elif getmonth==6:
                            finalmonth='June'
                        elif getmonth==7:
                            finalmonth='July'
                        elif getmonth==8:
                            finalmonth='August'
                        elif getmonth==9:
                            finalmonth='September'
                        elif getmonth==10:
                            finalmonth='October'
                        elif getmonth==11:
                            finalmonth='November'
                        elif getmonth==12:
                            finalmonth='December'
                        finalyear=str(monthlysales.values_list('DateTime__year',flat=True).first())
                        
                        month={}
                        monthtotalsalesi = monthlysales.aggregate(Sum('Sales')).get('Sales__sum')
                        
                        monthExpensesi= monthlysales.aggregate(Sum('Expenses')).get('Expenses__sum')
                        monthvalues=monthlysales.aggregate(Sum('Valuestocks')).get('Valuestocks__sum')
                        monthstarts=monthlysales.aggregate(Sum('Startstocks')).get('Startstocks__sum')
                        monthends=monthlysales.aggregate(Sum('Endstocks')).get('Endstocks__sum')
                        print('monthstarts: ',monthstarts,'monthvalues: ',monthvalues,'monthends: ',monthends)
                        month['monthdate']=finalmonth+", "+finalyear
                        month['monthtotalsales']='₱'+str(monthtotalsalesi)
                        month['monthExpenses']='₱'+(str(monthExpensesi))
                        calculate=monthtotalsalesi-(monthstarts+monthvalues-monthends)-monthExpensesi
                        if calculate<0:

                            month['monthCOGS']='₱0.00'
                            month['monthtotalnet']='₱0.00'
                        else:
                            month['monthCOGS']='₱'+(str(monthstarts+monthvalues-monthends))
                            month['monthtotalnet']='₱'+(str(monthtotalsalesi-(monthstarts+monthvalues-monthends)-monthExpensesi))
                        monthh[i]=month.values()
                        
                        i += 1
                    cogsss=(monthstarts+monthvalues-monthends)
                    print('cogsss1:',cogsss)
                    print('monthvalues1:',monthvalues)
                    monthly=monthh.values()
                    
                    #endfor month 2 Dailysales
                    if len(Acceptorder.objects.filter(Admin=userr, productname='Ready'))>0:
                        initial=Acceptorder.objects.filter(Admin=userr, productname='Ready').values_list('contactnumber', flat=True)
                        readylistcontact=list(initial)
                    else:
                        readylistcontact=list(Acceptorder.objects.none())
                    print('readylistcontact1:',readylistcontact)
                    return render(request, 'kgddashboard.html',{'readylistcontact':readylistcontact, 'onlineordercounter':onlineordercounter,'viewordersreject':viewordersreject,'rejectedorder':rejectedorder,'viewordersaccept':viewordersaccept,'acceptedorder':acceptedorder,'onlineorder':onlineorder,'notifyadmin':notifyadmin,'notifyorder':notifyorder,'userr':userr,'monthly':monthly,'ddaily':ddaily,'totalnet':totalnet,'totalsales':totalsales})

                else:
                    ddaily = Dailysales.objects.filter(user=userr).order_by('DateTime')
                    totalsales = ddaily.aggregate(Sum('Sales')).get('Sales__sum',0.00)
                    totalnet = ddaily.aggregate(Sum('Net')).get('Net__sum')
                    #FOR MONTH
                    monthlysales=Dailysales.objects.filter(user=userr).order_by('DateTime')
                    monthtotalsales = ddaily.aggregate(Sum('Sales')).get('Sales__sum')
                    monthExpenses= ddaily.aggregate(Sum('Expenses')).get('Expenses__sum')
                    monthvalues=ddaily.aggregate(Sum('Valuestocks')).get('Valuestocks__sum')
                    monthstarts=ddaily.aggregate(Sum('Startstocks')).get('Startstocks__sum')
                    monthends=ddaily.aggregate(Sum('Endstocks')).get('Endstocks__sum')
                    monthCOGS=monthstarts+monthvalues-monthends
                    monthtotalnet=monthtotalsales-monthCOGS-monthExpenses
                    #END FOR MONTH)
                    if len(Acceptorder.objects.filter(Admin=userr, productname='Ready'))>0:
                        initial=Acceptorder.objects.filter(Admin=userr, productname='Ready').values_list('contactnumber', flat=True)
                        readylistcontact=list(initial)
                    else:
                        readylistcontact=list(Acceptorder.objects.none())
                    print('readylistcontact1:',readylistcontact)
                    return render(request, 'kgddashboard.html',{'readylistcontact':readylistcontact, 'onlineordercounter':onlineordercounter,'viewordersreject':viewordersreject,'rejectedorder':rejectedorder,'viewordersaccept':viewordersaccept,'acceptedorder':acceptedorder,'onlineorder':onlineorder,'notifyadmin':notifyadmin,'notifyorder':notifyorder,'userr':userr,'monthlysales':monthlysales,'ddaily':ddaily,'totalnet':totalnet,'totalsales':totalsales})

def Onlineordertestingsystem(request, admin_id):
        #'domain/search/?q=haha', you would use request.GET.get('q', '')
        #theurl+?anykeyhere=anyvalue
        #request.query_params['anykeyhere']
        #then the result will be ="anyvalue"
        #?prmcd=<code>
        
        promocodegeti=request.GET.get('prmcd', '')
        if promocodegeti:
            settings.LOGIN_REDIRECT_URL='/index/onlineordertesting/'+str(admin_id)+'?prmcd='+promocodegeti
            settings.LOGIN_URL='/index/onlineordertesting/'+str(admin_id)+'?prmcd='+promocodegeti
            settings.LOGOUT_URL='/index/onlineordertesting/'+str(admin_id)+'?prmcd='+promocodegeti
        #without minimum amount #withoutredeemlimit
            if couponlist.objects.filter(code=promocodegeti, is_consumable=False, is_active=True, is_withMinimumAmount=False): 
                if couponlist.objects.filter(couponname='KGDDeliveryFree', code=promocodegeti, is_consumable=False, is_active=True, is_withMinimumAmount=False):
                #if promocodegeti == "KGDDeliveryFree":
                    couponvalidity='KGDDeliveryFree'
                    couponvaliditymessage='Valid Coupon.'
                    discount='0'
                    rqrd_minimumamnt=0
                    prmcd='KGDDeliveryFree'
                else:
                    couponvalidity='Valid'
                    couponvaliditymessage='Valid'
                    discounti=couponlist.objects.get(code=promocodegeti)
                    discount=discounti.discountamount
                    rqrd_minimumamnt=0
                    prmcd=promocodegeti
            #without minimum amount #withredeemlimit
            elif couponlist.objects.filter(code=promocodegeti, is_consumable=True, is_active=True, is_withMinimumAmount=False).exclude(redeemlimit=0): 
                if couponlist.objects.filter(couponname='KGDDeliveryFree', code=promocodegeti, is_consumable=True, is_active=True, is_withMinimumAmount=False).exclude(redeemlimit=0):
                #if promocodegeti == "KGDDeliveryFree":
                    couponvalidity='KGDDeliveryFree'
                    couponvaliditymessage='Valid Coupon.'
                    discount='0'
                    rqrd_minimumamnt=0
                    prmcd=promocodegeti
                else:
                    couponvalidity='Valid'
                    couponvaliditymessage='Valid'
                    discounti=couponlist.objects.get(code=promocodegeti)
                    discount=discounti.discountamount
                    rqrd_minimumamnt=0
                    prmcd=promocodegeti
            #this coupon code has been consumed. #without minimum amount #withredeemlimit
            elif couponlist.objects.filter(code=promocodegeti, is_consumable=True, redeemlimit=0,is_active=True, is_withMinimumAmount=False): 
                couponvalidity='Invalid'
                couponvaliditymessage='This coupon code has reached maximum redeem limit.'
                discount='0'
                rqrd_minimumamnt=0
                prmcd=promocodegeti
            #this coupon code is inactive at this moment. #without minimum amount #withoutredeemlimit
            elif couponlist.objects.filter(code=promocodegeti, is_consumable=False, is_active=False, is_withMinimumAmount=False): 
                couponvalidity='Invalid'
                couponvaliditymessage='This coupon code is inactive at this moment.'
                discount='0'
                rqrd_minimumamnt=0
                prmcd=promocodegeti
            #this coupon code is inactive at this moment. #without minimum amount #withredeemlimit
            elif couponlist.objects.filter(code=promocodegeti, is_consumable=True, is_active=False, is_withMinimumAmount=False): 
                couponvalidity='Invalid'
                couponvaliditymessage='This coupon code is inactive at this moment.'
                discount='0'
                rqrd_minimumamnt=0
                prmcd=promocodegeti
            #with minimum amount #withoutredeemlimit
            elif couponlist.objects.filter(code=promocodegeti, is_consumable=False, is_active=True, is_withMinimumAmount=True): 
                if couponlist.objects.filter(couponname='KGDDeliveryFree', code=promocodegeti, is_consumable=False, is_active=True, is_withMinimumAmount=True):
                #if promocodegeti == "KGDDeliveryFree":
                    couponvalidity='KGDDeliveryFree'
                    couponvaliditymessage='Valid Coupon.'
                    discount='0'
                    rqrd_minimumamnti=couponlist.objects.get(code=promocodegeti)
                    rqrd_minimumamnt=rqrd_minimumamnti.MinimumAmount
                    prmcd=promocodegeti
                else:
                    couponvalidity='Valid'
                    couponvaliditymessage='Valid Coupon'
                    discounti=couponlist.objects.get(code=promocodegeti)
                    discount=discounti.discountamount
                    rqrd_minimumamnti=couponlist.objects.get(code=promocodegeti)
                    rqrd_minimumamnt=rqrd_minimumamnti.MinimumAmount
                    prmcd=promocodegeti
            #with minimum amount #withredeemlimit
            elif couponlist.objects.filter(code=promocodegeti, is_consumable=True, is_active=True, is_withMinimumAmount=True).exclude(redeemlimit=0): 
                if couponlist.objects.filter(couponname='KGDDeliveryFree', code=promocodegeti, is_consumable=True, is_active=True, is_withMinimumAmount=True).exclude(redeemlimit=0):
                #if promocodegeti == "KGDDeliveryFree":
                    couponvalidity='KGDDeliveryFree'
                    couponvaliditymessage='Valid Coupon.'
                    discount='0'
                    rqrd_minimumamnti=couponlist.objects.get(code=promocodegeti)
                    rqrd_minimumamnt=rqrd_minimumamnti.MinimumAmount
                    prmcd=promocodegeti
                else:
                    couponvalidity='Valid'
                    couponvaliditymessage='Valid Coupon'
                    discounti=couponlist.objects.get(code=promocodegeti)
                    discount=discounti.discountamount
                    rqrd_minimumamnti=couponlist.objects.get(code=promocodegeti)
                    rqrd_minimumamnt=rqrd_minimumamnti.MinimumAmount
                    prmcd=promocodegeti
            #this coupon code has been consumed. #with minimum amount
            elif couponlist.objects.filter(code=promocodegeti, is_consumable=True, redeemlimit=0, is_active=True, is_withMinimumAmount=True): 
                couponvalidity='Invalid'
                couponvaliditymessage='This coupon code has reached maximum redeem limit.'
                discount='0'
                rqrd_minimumamnt=0
                prmcd=promocodegeti
            #this coupon code is inactive at this moment. #with minimum amount #withoutredeemlimit
            elif couponlist.objects.filter(code=promocodegeti, is_consumable=False, is_active=False, is_withMinimumAmount=True): 
                couponvalidity='Invalid'
                couponvaliditymessage='This coupon code is inactive at this moment.'
                discount='0'
                rqrd_minimumamnt=0
                prmcd=promocodegeti
            #this coupon code is inactive at this moment. #with minimum amount #withredeemlimit
            elif couponlist.objects.filter(code=promocodegeti, is_consumable=True, is_active=False, is_withMinimumAmount=True): 
                couponvalidity='Invalid'
                couponvaliditymessage='This coupon code is inactive at this moment.'
                discount='0'
                rqrd_minimumamnt=0
                prmcd=promocodegeti

            #This coupon code is for testing.
            elif promocodegeti == "Testing123": 
                couponvalidity='Valid'
                couponvaliditymessage='This coupon code is for testing.'
                discount='0'
                rqrd_minimumamnt=0
                prmcd=promocodegeti
            #This coupon code is for testing.

            #this coupon code is invalid.
            else:
                couponvalidity='Invalid'
                couponvaliditymessage='This coupon code is invalid.'
                discount='0'
                rqrd_minimumamnt=0
                prmcd=promocodegeti
            print('couponvalidity:  ',couponvalidity)
        else:
            settings.LOGIN_REDIRECT_URL='/index/onlineordertesting/'+str(admin_id)
            settings.LOGIN_URL='/index/onlineordertesting/'+str(admin_id)
            settings.LOGOUT_URL='/index/onlineordertesting/'+str(admin_id)
            couponvalidity='No Coupon'
            couponvaliditymessage='No Coupon'
            discount='0'
            rqrd_minimumamnt=0
            prmcd='No Coupon'
            print('couponvalidity:  ',couponvalidity)
        print('QTY Sold for five months: ',Sales.objects.filter(user=4).aggregate(Sum('Qty')).get('Qty__sum'))
        userr=request.user.id
        username=request.user.username

        if request.user.is_anonymous:
            promoidentifier=''
        elif datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%A') == 'Friday' and user1.objects.filter(user__id=admin_id, Promo='Special Promo'):
            promoidentifier='FreeFriesDayandSpecialPromo'
        elif datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%A') == 'Friday':
            promoidentifier='FreeFriesDay'
        elif user1.objects.filter(user__id=admin_id, Promo='Special Promo'):
            promoidentifier='Special Promo'
        else:
            
            promoidentifier=''
        if is_ajax(request=request) and request.POST.get('username'):
            usernamess=json.loads(request.POST.get('username'))
            passwordss=json.loads(request.POST.get('password'))
            
            userss = authenticate(request, username=usernamess, password=passwordss)
            if userss is not None:
                login(request, userss)
            # Redirect to a success page.
                return JsonResponse({'reload':'success'})
            else:
                if User.objects.filter(username=usernamess):
                    usernamechecki='usernamechecktrue'
                else:
                    usernamechecki='usernamecheckfalse'
                usernamecheck=json.dumps(usernamechecki)
                # Return an 'invalid login' error message.
                return JsonResponse({'reload':usernamechecki})    
        
        if is_ajax(request=request) and request.POST.get('firstnameid'):
            firstnameid=json.loads(request.POST.get('firstnameid'))
            lastnameid=json.loads(request.POST.get('lastnameid'))
            emailid=json.loads(request.POST.get('emailid'))
            usernamesu=json.loads(request.POST.get('usernamesuid'))
            passwordsu=make_password(json.loads(request.POST.get('passwordsuid')))
            if User.objects.filter(first_name=firstnameid):
                firstnamechecker = 'notpass'
            else:
                firstnamechecker = 'pass'
            if User.objects.filter(last_name=lastnameid):
                lastnamechecker = 'pass'
            else:
                lastnamechecker = 'pass'
            if User.objects.filter(email=emailid):
                emailchecker = 'notpass'
            else:
                emailchecker = 'pass'
            if User.objects.filter(username=usernamesu):
                usernamesuchecker = 'notpass'
            else:
                usernamesuchecker = 'pass'
            if User.objects.filter(password=json.loads(request.POST.get('passwordsuid'))):
                passwordsuchecker = 'notpass'
            else:
                passwordsuchecker = 'pass'
            if firstnamechecker == 'pass' and lastnamechecker == 'pass' and emailchecker == 'pass' and usernamesuchecker == 'pass' and passwordsuchecker == 'pass':
                createnewaccount = User.objects.create(first_name=firstnameid,last_name=lastnameid,username=usernamesu,email=emailid,password=passwordsu)
                usersu = User.objects.get(first_name=firstnameid,last_name=lastnameid,username=usernamesu,email=emailid,password=passwordsu)
                login(request, usersu)
                print('usernamesu: ',usernamesu)
            # Redirect to a success page.
            context={
            'firstnameid':json.dumps(firstnamechecker),
            'lastnameid':json.dumps(lastnamechecker),
            'emailid':json.dumps(emailchecker),
            'usernamesu':json.dumps(usernamesuchecker),
            'passwordsu':json.dumps(passwordsuchecker)
            }
            return JsonResponse(context)

        if is_ajax(request=request) and request.POST.get('response.first_name'):
            first = json.loads(request.POST.get('response.first_name'))
            print(first)
            last = json.loads(request.POST.get('response.last_name'))
            print(last)
            short = json.loads((request.POST.get('response.short_name')).lower())
            print(short)
            uids=json.loads(request.POST.get('response.id'))
            responseresponse=json.loads(request.POST.get('response.response'))
            try:
                email=responseresponse.email
            except AttributeError:
                email=''
            if User.objects.filter(first_name=first, last_name=last):
                print('meron')
                createsocialaccounttwo = User.objects.filter(first_name=first,last_name=last,username=short)
                user=User.objects.get(first_name=first,last_name=last,username=short)
                socialaccountsslogin=login(request, user)
                if promocodegeti:
                    settings.LOGIN_REDIRECT_URL='/index/onlineordertesting/'+str(admin_id)+'?prmcd='+promocodegeti
                    settings.LOGIN_URL='/index/onlineordertesting/'+str(admin_id)+'?prmcd='+promocodegeti
                    settings.LOGOUT_URL='/index/onlineordertesting/'+str(admin_id)+'?prmcd='+promocodegeti
                else:
                    settings.LOGIN_URL='/index/onlineordertesting/'+str(admin_id)
                    settings.LOGOUT_URL='/index/onlineordertesting/'+str(admin_id)
                    settings.LOGIN_REDIRECT_URL='/index/onlineorder/'+str(admin_id)
                return JsonResponse({'reload':'reload'})
            else:
                print('none')
                if responseresponse['email']:
                    createsocialaccounttwo = User.objects.create(first_name=first,last_name=last,username=short,email=email)
                else:
                    createsocialaccounttwo = User.objects.create(first_name=first,last_name=last,username=short)
                user=User.objects.get(id=createsocialaccounttwo.id)
                createsocialaccount = SocialAccount.objects.create(user=user, provider='facebook', uid=uids, extra_data=responseresponse)
                authcreatedsocialaccount=login(request, user)

                if promocodegeti:
                    settings.LOGIN_REDIRECT_URL='/index/onlineordertesting/'+str(admin_id)+'?prmcd='+promocodegeti
                    settings.LOGIN_URL='/index/onlineordertesting/'+str(admin_id)+'?prmcd='+promocodegeti
                    settings.LOGOUT_URL='/index/onlineordertesting/'+str(admin_id)+'?prmcd='+promocodegeti
                else:
                    settings.LOGIN_URL='/index/onlineordertesting/'+str(admin_id)
                    settings.LOGOUT_URL='/index/onlineordertesting/'+str(admin_id)
                    settings.LOGIN_REDIRECT_URL='/index/onlineorder/'+str(admin_id)
                return JsonResponse({'reload':'reload'})
        if is_ajax(request=request) and request.GET.get('addressss'):
            userr=request.user.id
            username=request.user.username
            if request.user.first_name:
                firstname=request.user.first_name
                lastname=request.user.last_name
            elif request.user.is_anonymous:
                print('AnonymousUser')
                firstname=''
                lastname=''
            else:
                firstname=''
                lastname=''
            print(firstname)
            print(lastname)

            if Sales.objects.filter(CusName=firstname+' '+lastname).exclude(productname='DeliveryFee').exclude(MOP="Pickup").values_list('pinnedlat').distinct():
                counteruser=Sales.objects.filter(CusName=firstname+' '+lastname).exclude(productname='DeliveryFee').exclude(MOP="Pickup").distinct('pinnedlat').values_list('pinnedlat', flat=True)
                if len(counteruser) == 1 and counteruser[0] != None:
                    addressuseri = []
                    addressuserii = Sales.objects.filter(CusName=firstname+' '+lastname, pinnedlat__in=counteruser).exclude(productname='DeliveryFee').exclude(MOP="Pickup").first()
                    #addressuseri[0] = addressuserii
                    addressuseri.append(addressuserii)
                    addressuser = serializers.serialize('json',addressuseri, cls=JSONEncoder)
                    #addressuser=json.dumps(addressuseri, cls=JSONEncoder)
                    print('addressuser1:',addressuser)
                else:
                    addressuseri = []
                    i=0
                    while i<len(counteruser):
                        addressuserii=Sales.objects.filter(CusName=firstname+' '+lastname,pinnedlat=counteruser[i]).exclude(productname='DeliveryFee').exclude(MOP="Pickup").distinct().first()
                        addressuseri.append(addressuserii)
                    
                        i += 1
                    addressuser=serializers.serialize('json',addressuseri, cls=JSONEncoder)
                    #addressuser=json.dumps(addressuseri, cls=JSONEncoder)
                    print('addressuser2:',addressuser)
            else:
                addressuseri = Sales.objects.none()
                addressuser = serializers.serialize('json',addressuseri, cls=JSONEncoder)
                #addressuser=json.dumps(addressuseri, cls=JSONEncoder)
                print('addressuser3:',addressuser)
            return JsonResponse({'addressuser':addressuser})
        mtbuttons = user1.objects.filter(Category__Categorychoices='Milktea',user__id=admin_id).distinct('productname')
        mtsizes = Sizes.objects.all()
        Categoriess = Categories.objects.all()
        Subcategoriess = Subcategories.objects.all()
        frbuttons = user1.objects.filter(Category__Categorychoices='Frappe',user__id=admin_id).distinct('productname')
        frsizes = Sizes.objects.all().exclude(Sizechoices__exact='Small')
        psizes = PSizes.objects.all()
        freezebuttons = user1.objects.filter(Category__Categorychoices='Freeze',user__id=admin_id).distinct('productname')
        addonsbuttons = user1.objects.filter(Category__Categorychoices='Add-ons',user__id=admin_id).distinct('productname')
        cookiesbuttons = user1.objects.filter(Subcategory__Subcategorychoices='Cookies',user__id=admin_id).distinct('productname')
        friesbuttons = user1.objects.filter(Subcategory__Subcategorychoices='Fries',user__id=admin_id).distinct('productname')
        shawarmabuttons = user1.objects.filter(Subcategory__Subcategorychoices='Shawarma',user__id=admin_id).distinct('productname')
        bubwafbuttons = user1.objects.filter(Subcategory__Subcategorychoices='Bubble Waffle',user__id=admin_id).distinct('productname')
        pizzabuttons = user1.objects.filter(Subcategory__Subcategorychoices='Pizza',user__id=admin_id).distinct('productname')
        specialpromobuttons = user1.objects.filter(Category__Categorychoices='Promo',user__id=admin_id,Promo='Special Promo').distinct('productname')
        FreeFriespromobuttons = user1.objects.filter(Category__Categorychoices='Promo',user__id=admin_id,Promo='FreeFriesDay').distinct('productname')
        i=0
        pizzapricess={}
        pizzapricesii = user1.objects.filter(Subcategory__Subcategorychoices='Pizza',user__id=admin_id).values_list('Price',flat=True).order_by('-id')
        
        pizzaproductnameii=pizzapricesii.values_list('productname',flat=True)
        
        pizzasizeii=pizzapricesii.values_list('PSize__PSizechoices',flat=True)
        
        while i<pizzapricesii.count():
            pizzapricess[pizzaproductnameii[i]+pizzasizeii[i]]=pizzapricesii[i]

            i += 1
        pizzapricesss=pizzapricess
        
        pizzaall=json.dumps(pizzapricesss)
        snbuttons = user1.objects.filter(Category__Categorychoices='Snacks',user__id=admin_id)

        if request.GET.get('payment'):
            #arraypunchedii=json.dumps(request.GET.get('array'))
            arraypunchedi=json.loads(request.GET.get('array'))
            arraypunched=arraypunchedi
            changeefor=int(json.loads(request.GET.get('changefor') or '0'))
            print('arraypunched:',arraypunched)
            try:
                intorfloat = int(request.GET.get('totalwithdevfeename'))
                
            except ValueError:
                pass
            try:
                intorfloat = float(request.GET.get('totalwithdevfeename'))
                
            except ValueError:
                pass
            objs = [Customer(
                        Admin=admin_id,
                        Customername=request.GET.get('fullname'),
                        codecoupon=request.GET.get('getpromocodename') or None,
                        discount=request.GET.get('discount') or None,
                        Province=request.GET.get('Province'),
                        MunicipalityCity=request.GET.get('Municipality') or None,
                        Barangay=request.GET.get('barangay') or None,
                        StreetPurok=request.GET.get('street') or None,
                        Housenumber=request.GET.get('houseno') or None,
                        LandmarksnNotes=request.GET.get('notesmark') or None,
                        DeliveryFee=request.GET.get('devfeename') or 0,
                        contactnumber=request.GET.get('contactno'),
                        Bill=request.GET.get('changefor') or 0,
                        Change=(changeefor-(intorfloat or 0)),
                        productname=obj['productname'],
                        Category=obj['Category'],
                        Subcategory=obj['Subcategory'] or None,
                        Size=obj['Size'] or None,
                        PSize=obj['PSize'] or None,
                        Addons=obj['Addonsname'] or None,
                        QtyAddons=obj['Addonsqty'] or 0,
                        Price=user1.objects.filter(user__id=admin_id, productname=obj['productname'], PSize__PSizechoices=obj['PSize'] or None, Size__Sizechoices=obj['Size'] or None).values('Price')[0]['Price'] or 0,
                        Cost=user1.objects.filter(user__id=admin_id, productname=obj['productname'], PSize__PSizechoices=obj['PSize'] or None, Size__Sizechoices=obj['Size'] or None).values('Cost')[0]['Cost'] or 0,
                        Subtotal = obj['Subtotal'],
                        GSubtotal=intorfloat or 0,
                        Qty=obj['Qty'],
                        MOP=request.GET.get('payment'),
                        ordertype='Online',
                        Timetodeliver=request.GET.get('deliverytime') or None,
                        ScheduleTime=request.GET.get('schedtimename') or None,
                        gpslat = request.GET.get('gpslat') or None,
                        gpslng = request.GET.get('gpslng') or None,
                        gpsaccuracy = request.GET.get('gpsaccuracy') or None,
                        pinnedlat = request.GET.get('latitude') or None,
                        pinnedlng = request.GET.get('longitude') or None,
                        tokens = request.GET.get('tokens') or None,
                        DateTime=datetime.datetime.now(pytz.timezone('Asia/Singapore')),
                )
                for obj in arraypunched
            ]
            customerandorder = Customer.objects.bulk_create(objs)
            arraypunchedcounter=len(customerandorder)

            messages.success(request, "Your order has been submitted!")
            onlineorder = Customer.objects.filter(Admin=admin_id).distinct('contactnumber')
            submitted(request)
            if promocodegeti:
                return HttpResponseRedirect('/index/onlineorder/'+str(admin_id)+'/OrderProgress/?prmcd='+promocodegeti)
            else:
                return HttpResponseRedirect('/index/onlineorder/'+str(admin_id)+'/OrderProgress/')
        else:
            onlineorder = Customer.objects.none()
        viewordersi={}
        arrayone=[]
        contactdistincteri = Customer.objects.filter(Admin=userr).distinct('contactnumber')
        contactdistincter=contactdistincteri.values_list('contactnumber',flat=True)
        i=0
        for cndistinct in contactdistincter:
            arrayseparatoriii=Customer.objects.filter(Admin=userr,contactnumber=cndistinct)
            arrayseparator = list(arrayseparatoriii)
            arrayone.append(arrayseparator)
            viewordersi[contactdistincter[i]]=arrayone[i]
            i=i+1
        if promocodegeti:
            settings.LOGIN_REDIRECT_URL='/index/onlineordertesting/'+str(admin_id)+'?prmcd='+promocodegeti
            settings.LOGIN_URL='/index/onlineordertesting/'+str(admin_id)+'?prmcd='+promocodegeti
            settings.LOGOUT_URL='/index/onlineordertesting/'+str(admin_id)+'?prmcd='+promocodegeti
        else:
            settings.LOGIN_URL='/index/onlineordertesting/'+str(admin_id)
            settings.LOGOUT_URL='/index/onlineordertesting/'+str(admin_id)
            settings.LOGIN_REDIRECT_URL='/index/onlineorder/'+str(admin_id)
        #vieworders=json.dumps(viewordersi)
        #print('vieworders: ',vieworders)
        return render(request, 'Onlineordertesting.html',{'prmcd':prmcd,'rqrd_minimumamnt':rqrd_minimumamnt,'discount':discount,'couponvaliditymessage':couponvaliditymessage,'couponvalidity':couponvalidity,'promoidentifier':promoidentifier,'FreeFriespromobuttons':FreeFriespromobuttons,'admin_id':admin_id,'onlineorder':onlineorder,'pizzaall':pizzaall,'snbuttons':snbuttons,'pizzabuttons':pizzabuttons,'bubwafbuttons':bubwafbuttons,'shawarmabuttons':shawarmabuttons,'friesbuttons':friesbuttons,'cookiesbuttons':cookiesbuttons,'addonsbuttons':addonsbuttons,'freezebuttons':freezebuttons,'specialpromobuttons':specialpromobuttons,'frsizes':frsizes,'frbuttons':frbuttons,'Subcategoriess':Subcategoriess,'Categoriess':Categoriess,'mtsizes':mtsizes,'mtbuttons':mtbuttons})

