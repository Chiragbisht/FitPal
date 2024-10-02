from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.backends import ModelBackend

def login_or_register(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # User exists, log them in
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Successfully logged in.")
            return redirect('dashboard')
        else:
            # User doesn't exist, try to create a new one
            if User.objects.filter(email=email).exists():
                # Email exists but password is wrong
                messages.error(request, "Invalid email or password.")
            else:
                # Create new user
                user = User.objects.create_user(username=email, email=email, password=password)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, "Account created and logged in successfully.")
                return redirect('dashboard')
    
    return render(request, 'fitnessapp/login_or_register.html')

@login_required
def dashboard(request):
    return render(request, 'fitnessapp/dashboard.html')





def logout_view(request):
    logout(request)
    return redirect('home')

def home(request):
    
    return render(request, 'fitnessapp/login.html')

@login_required
def update_user(request):
    if request.method == 'POST':
        new_username = request.POST['username']
        if new_username != request.user.username:
            if User.objects.filter(username=new_username).exists():
                messages.error(request, 'This username is already taken.')
            else:
                request.user.username = new_username
                request.user.save()
                messages.success(request, 'Your username has been updated successfully.')
                return redirect('home')
    return render(request, 'fitnessapp/update_user.html')