# Django Role-Based Authentication Setup Guide

## Overview
I've implemented a complete role-based authentication system that connects your frontend role selection to Django groups and permissions. Here's what was implemented:

## Changes Made

### 1. Created UserProfile Model (`accounts/models.py`)
- Added `UserProfile` model with role choices: 'administrator' and 'screening_physician'
- Includes automatic profile creation signals
- OneToOne relationship with User model

### 2. Updated Signup View (`accounts/views.py`)
- Modified to capture `user_role` from the frontend form
- Automatically creates UserProfile with selected role
- Assigns users to appropriate Django groups based on role selection
- Shows success/error messages

### 3. Updated Base Template (`templates/base.html`)
- Role-based navigation: Administrators see full menu, Physicians see limited menu
- Shows user's role from profile in footer
- Conditional display of portal title (ADMINISTRATOR vs PHYSICIAN)

### 4. Updated Admin Interface (`accounts/admin.py`)
- Added UserProfile inline in User admin
- Separate UserProfile admin for managing roles
- Enhanced user management in Django admin

### 5. Created Management Command (`accounts/management/commands/create_groups.py`)
- Automatically creates 'Administrator' and 'Screening Physician' groups
- Assigns appropriate permissions to each group

## Required Setup Steps

### Step 1: Run Migrations
Since the UserProfile model migration already exists, just run:
```bash
python manage.py migrate
```

### Step 2: Create Django Groups
Run the management command to create groups and assign permissions:
```bash
python manage.py create_groups
```

### Step 3: Create Superuser (Optional)
If you don't have a superuser yet:
```bash
python manage.py createsuperuser
```

### Step 4: Test the System
1. Visit the signup page: http://localhost:8000/accounts/signup/
2. Select either Administrator or Screening Physician role
3. Complete registration
4. Login and verify:
   - Role-based navigation appears correctly
   - User role displays in sidebar footer
   - Appropriate access permissions

## How It Works

### Frontend to Backend Flow:
1. User selects role in signup form (`user_role` field)
2. Signup view captures this data from `request.POST.get('user_role')`
3. Creates UserProfile with selected role
4. Assigns user to corresponding Django group
5. Base template shows different navigation based on `user.profile.role`

### Role Permissions:
- **Administrator**: Full access (add, change, delete, view patient forms)
- **Screening Physician**: Limited access (view, change patient forms only)

### Template Role Checking:
```django
{% if user.profile.role == 'administrator' %}
    <!-- Full admin navigation -->
{% else %}
    <!-- Limited physician navigation -->
{% endif %}
```

## Troubleshooting

### If Groups Don't Exist Error:
Run the create_groups command:
```bash
python manage.py create_groups
```

### If UserProfile Doesn't Exist:
The signal handlers should create profiles automatically, but you can create manually:
```python
from accounts.models import UserProfile
from django.contrib.auth.models import User

for user in User.objects.filter(profile__isnull=True):
    UserProfile.objects.create(user=user)
```

### Role Not Showing:
Make sure migrations are applied and profiles exist for all users.

## Testing Role-Based Access

1. Create test users with different roles
2. Login with each role
3. Verify navigation differences:
   - Administrator: Dashboard, Upload Form, Database, Time Saved, Messages, Settings
   - Physician: Database, Messages, Settings only

The system is now fully integrated and ready to use!