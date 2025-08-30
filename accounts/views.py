from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
import logging

logger = logging.getLogger(__name__)

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                # Get form data
                username = form.cleaned_data.get('username')
                password1 = form.cleaned_data.get('password1')
                
                # Check if user already exists
                if User.objects.filter(username=username).exists():
                    messages.error(request, 'Username already exists. Please choose a different one.')
                    return render(request, 'register.html', {'form': form})
                
                # Create user using Django's create_user method
                user = User.objects.create_user(
                    username=username,
                    password=password1
                )
                
                # Authenticate and login the user
                authenticated_user = authenticate(request, username=username, password=password1)
                if authenticated_user is not None:
                    login(request, authenticated_user)
                    messages.success(request, f'Account created successfully for {username}!')
                    return redirect('accounts:home')
                else:
                    messages.warning(request, 'Account created but automatic login failed. Please log in manually.')
                    return redirect('accounts:login')
                    
            except IntegrityError as e:
                logger.error(f"IntegrityError during user registration: {e}")
                messages.error(request, 'Username already exists. Please choose a different one.')
                return render(request, 'register.html', {'form': form})
            except Exception as e:
                logger.error(f"Error during user registration: {e}")
                messages.error(request, 'An error occurred during registration. Please try again.')
                return render(request, 'register.html', {'form': form})
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()
    
    return render(request, 'register.html', {'form': form})

def user_login(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('accounts:home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

def user_logout(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:home')

@login_required
def profile(request):
    """User profile view (requires login)"""
    return render(request, 'profile.html')

def home(request):
    """Home page view with login functionality"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('accounts:home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'home.html')
