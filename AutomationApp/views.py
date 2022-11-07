from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import auth, User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.template import *

# Create your views here.

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


def kgddashboard(request):
        pass
        return render(request, 'kgddashboard.html')
