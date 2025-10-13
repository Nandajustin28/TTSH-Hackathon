from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import Group
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserProfile

def signup_view(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        # Get the role from the frontend form
        user_role = request.POST.get('user_role')
        
        form = UserCreationForm(request.POST)
        if form.is_valid() and user_role:
            user = form.save()
            username = form.cleaned_data.get('username')
            
            # Create or get user profile and set role
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = user_role
            profile.save()
            
            # Assign user to appropriate Django group
            try:
                if user_role == 'administrator':
                    group = Group.objects.get(name='Administrator')
                elif user_role == 'screening_physician':
                    group = Group.objects.get(name='Screening Physician')
                else:
                    group = None
                
                if group:
                    user.groups.add(group)
                    messages.success(request, f'Account created for {username} as {profile.get_role_display()}! You can now log in.')
                    
            except Group.DoesNotExist:
                messages.warning(request, f'Account created for {username}, but user groups not found. Please contact administrator.')
            
            return redirect('accounts:login')
        else:
            if not user_role:
                messages.error(request, 'Please select a role.')
            else:
                messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/signup.html', {'form': form})

def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('dashboard:home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')
