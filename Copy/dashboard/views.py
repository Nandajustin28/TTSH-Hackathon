from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.conf import settings
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth.models import User
import os
import json
from .models import PatientForm

@login_required
def dashboard_home(request):
    # Mock data for the dashboard
    recent_forms = PatientForm.objects.all()[:5]  # Get 5 most recent forms
    total_forms = PatientForm.objects.count()
    
    # Get message notifications for administrators
    unread_messages_count = 0
    latest_conversation = None
    if hasattr(request.user, 'profile') and request.user.profile.role == 'administrator':
        try:
            from messaging.models import Conversation, Message, MessageReadStatus
            # Get conversations where user is participant
            user_conversations = Conversation.objects.filter(participants=request.user)
            
            unread_messages_count = 0
            latest_conversation_with_unread = None
            
            for conversation in user_conversations:
                # Count unread messages in this conversation (messages not sent by current user and not read by them)
                unread_in_conversation = Message.objects.filter(
                    conversation=conversation
                ).exclude(
                    sender=request.user
                ).exclude(
                    read_statuses__user=request.user
                ).count()
                
                unread_messages_count += unread_in_conversation
                
                if unread_in_conversation > 0 and not latest_conversation_with_unread:
                    latest_conversation_with_unread = conversation
            
            latest_conversation = latest_conversation_with_unread
        except ImportError:
            pass
    
    context = {
        'user_name': request.user.get_full_name() or request.user.username,
        'total_forms': total_forms,
        'accepted_forms': PatientForm.objects.filter(processed=True).count(),
        'rejected_forms': 0,  # Add logic for rejected forms if needed
        'avg_processing_time': '0.0m',
        'forms_processed_today': PatientForm.objects.filter(uploaded_at__date=timezone.now().date()).count() if 'timezone' in globals() else 0,
        'acceptance_rate': '100%' if total_forms > 0 else '0%',
        'processing_target': '<6 min',
        'recent_forms': recent_forms,
        'unread_messages_count': unread_messages_count,
        'latest_conversation': latest_conversation,
    }
    return render(request, 'dashboard/home.html', context)

@login_required
def upload_form(request):
    """Handle the upload form page and file uploads"""
    if request.method == 'POST':
        patient_name = request.POST.get('patient_name', '').strip()
        uploaded_file = request.FILES.get('patient_form')
        
        if not uploaded_file:
            messages.error(request, 'Please select a file to upload.')
            return render(request, 'dashboard/upload_form.html')
        
        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if uploaded_file.size > max_size:
            messages.error(request, 'File size must be less than 10MB.')
            return render(request, 'dashboard/upload_form.html')
        
        # Validate file extension
        allowed_extensions = ['pdf', 'png', 'jpg', 'jpeg']
        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            messages.error(request, 'Only PDF, PNG, and JPG files are allowed.')
            return render(request, 'dashboard/upload_form.html')
        
        try:
            # Create PatientForm instance
            patient_form = PatientForm.objects.create(
                patient_name=patient_name if patient_name else None,
                uploaded_file=uploaded_file,
                uploaded_by=request.user
            )
            
            # Here you would add AI processing logic
            # For now, we'll just simulate instant feedback
            patient_form.ai_feedback = "AI will analyze the form and provide instant feedback"
            patient_form.save()
            
            messages.success(request, f'Form uploaded successfully! File: {uploaded_file.name}')
            return redirect('dashboard:upload_form')
            
        except Exception as e:
            messages.error(request, f'Error uploading file: {str(e)}')
            return render(request, 'dashboard/upload_form.html')
    
    return render(request, 'dashboard/upload_form.html')

@csrf_exempt
@login_required
def ajax_upload(request):
    """Handle AJAX file uploads for drag and drop functionality"""
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        patient_name = request.POST.get('patient_name', '').strip()
        
        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if uploaded_file.size > max_size:
            return JsonResponse({'success': False, 'error': 'File size must be less than 10MB.'})
        
        # Validate file extension
        allowed_extensions = ['pdf', 'png', 'jpg', 'jpeg']
        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            return JsonResponse({'success': False, 'error': 'Only PDF, PNG, and JPG files are allowed.'})
        
        try:
            # Create PatientForm instance
            patient_form = PatientForm.objects.create(
                patient_name=patient_name if patient_name else None,
                uploaded_file=uploaded_file,
                uploaded_by=request.user
            )
            
            # Simulate AI processing
            patient_form.ai_feedback = "AI will analyze the form and provide instant feedback"
            patient_form.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'File "{uploaded_file.name}" uploaded successfully!',
                'file_id': patient_form.id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error uploading file: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'No file provided'})

@login_required
def database_view(request):
    """Display all patient forms with search and filter functionality"""
    forms = PatientForm.objects.all()
    
    # Role-based filtering: Physicians only see pending forms, Administrators see all
    if hasattr(request.user, 'profile') and request.user.profile.role == 'screening_physician':
        forms = forms.filter(status='pending')
    
    # Search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        forms = forms.filter(
            Q(patient_name__icontains=search_query) | 
            Q(extracted_patient_name__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        forms = forms.filter(status=status_filter)
    
    # Time-based sorting
    sort_order = request.GET.get('sort', 'desc')  # Default to newest first (descending)
    if sort_order == 'asc':
        forms = forms.order_by('uploaded_at')  # Oldest first
    else:
        forms = forms.order_by('-uploaded_at')  # Newest first
    
    # Add message information for administrators
    forms_with_messages = []
    for form in forms:
        form.has_messages = False
        form.unread_count = 0
        form.related_conversation = None
        
        # For administrators, check if there are messages about this form
        if hasattr(request.user, 'profile') and request.user.profile.role == 'administrator':
            try:
                from messaging.models import Conversation, Message, MessageReadStatus
                
                # Look for conversations where the message content mentions this form
                form_patient_name = form.patient_name or form.extracted_patient_name or "Unknown Patient"
                related_messages = Message.objects.filter(
                    content__icontains=f"patient form: {form_patient_name}"
                ).exclude(sender=request.user)
                
                if related_messages.exists():
                    form.has_messages = True
                    # Find the conversation with the most recent message
                    latest_message = related_messages.order_by('-created_at').first()
                    form.related_conversation = latest_message.conversation
                    
                    # Check if any messages contain physician decisions
                    form.has_physician_decision = related_messages.filter(
                        content__icontains="PHYSICIAN DECISION:"
                    ).exists()
                    
                    # Count unread messages in this conversation
                    form.unread_count = Message.objects.filter(
                        conversation=latest_message.conversation
                    ).exclude(
                        sender=request.user
                    ).exclude(
                        read_statuses__user=request.user
                    ).count()
                else:
                    form.has_physician_decision = False
                    
            except ImportError:
                pass
        
        forms_with_messages.append(form)
    
    # Calculate category counts for administrators
    pending_count = 0
    approved_count = 0
    rejected_count = 0
    
    if hasattr(request.user, 'profile') and request.user.profile.role == 'administrator':
        all_forms = PatientForm.objects.all()
        pending_count = all_forms.filter(status='pending').count()
        approved_count = all_forms.filter(status='approved').count()
        rejected_count = all_forms.filter(status='rejected').count()
    
    context = {
        'forms': forms_with_messages,
        'search_query': search_query,
        'status_filter': status_filter,
        'sort_order': sort_order,
        'total_forms': len(forms_with_messages),
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    
    return render(request, 'dashboard/database.html', context)

@login_required
def time_saved_analytics(request):
    """Display time saved analytics and processing efficiency metrics"""
    from django.utils import timezone
    from datetime import timedelta
    import json
    
    # Get all forms for calculations
    all_forms = PatientForm.objects.all()
    processed_forms = PatientForm.objects.filter(processed=True)
    
    # Calculate metrics
    total_processed = processed_forms.count()
    
    # Calculate average processing time (mock data for now)
    avg_processing_minutes = 0.0
    ai_processing_seconds = 0.0
    if processed_forms.exists():
        # Mock calculation - in real implementation, you'd use actual processing times
        avg_processing_minutes = 2.5  # Simulated average
        ai_processing_seconds = 0.0  # AI is instant for display purposes
    
    # Calculate time saved vs manual processing
    # Assume manual processing takes 15 minutes per form on average
    manual_processing_minutes_per_form = 15
    ai_processing_minutes_per_form = avg_processing_minutes
    time_saved_per_form = manual_processing_minutes_per_form - ai_processing_minutes_per_form
    total_time_saved_hours = (time_saved_per_form * total_processed) / 60
    
    # Calculate efficiency gain percentage
    efficiency_gain = 0
    if manual_processing_minutes_per_form > 0 and total_processed > 0:
        efficiency_gain = ((manual_processing_minutes_per_form - ai_processing_minutes_per_form) / manual_processing_minutes_per_form) * 100
    
    # Target achievement (forms processed under 6 minutes)
    target_minutes = 6
    forms_under_target = processed_forms.filter(processing_time_seconds__lt=target_minutes*60).count() if processed_forms.exists() else 0
    target_achievement_percentage = (forms_under_target / total_processed * 100) if total_processed > 0 else 0
    success_rate = target_achievement_percentage
    
    # Generate chart data for last 7 days
    today = timezone.now().date()
    last_7_days = []
    processing_time_data = []
    daily_volume_data = []
    
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        day_name = date.strftime('%a')
        last_7_days.append(day_name)
        
        # Mock data for processing times (in real app, calculate from actual data)
        processing_time_data.append(0.0)  # All showing 0 as in screenshot
        
        # Mock data for daily volume
        daily_volume_data.append(0)  # All showing 0 as in screenshot
    
    context = {
        'total_processed': total_processed,
        'avg_processing_minutes': avg_processing_minutes,
        'total_time_saved_hours': total_time_saved_hours,
        'target_achievement_percentage': int(target_achievement_percentage),
        'forms_under_target': forms_under_target,
        'target_minutes': target_minutes,
        'last_7_days': json.dumps(last_7_days),
        'processing_time_data': json.dumps(processing_time_data),
        'daily_volume_data': json.dumps(daily_volume_data),
        'performance_status': 'excellent' if avg_processing_minutes < target_minutes else 'good' if avg_processing_minutes < target_minutes * 1.5 else 'needs_improvement',
        # Key Insights data
        'ai_processing_seconds': ai_processing_seconds,
        'efficiency_gain': efficiency_gain if efficiency_gain > 0 else 'NaN',
        'success_rate': int(success_rate),
    }
    
    return render(request, 'dashboard/time_saved.html', context)

@login_required
def settings_view(request):
    """Display and handle settings page"""
    if request.method == 'POST':
        # Handle form submission
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip()
        email_notifications = request.POST.get('email_notifications') == 'on'
        new_referrals = request.POST.get('new_referrals') == 'on'
        
        # In a real application, you would save these to user model or settings model
        # For now, we'll just show a success message
        messages.success(request, 'Settings saved successfully!')
        return redirect('dashboard:settings')
    
    # Mock user data - in real app, get from authenticated user
    context = {
        'user_email': 'dhammanandajustinyu@gmail.com',
        'user_full_name': 'Nanda 28',
        'user_username': '',
        'user_role': 'Admin',
        'email_notifications_enabled': True,
        'new_referrals_enabled': True,
    }
    
    return render(request, 'dashboard/settings.html', context)

@login_required
def update_form_status(request):
    """Update the status of a patient form via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            form_id = data.get('form_id')
            new_status = data.get('status')
            
            # Validate the new status
            if new_status not in ['pending', 'approved', 'rejected']:
                return JsonResponse({'success': False, 'error': 'Invalid status'})
            
            # Only administrators can update status directly. Physicians must request via messaging.
            if not hasattr(request.user, 'profile') or request.user.profile.role != 'administrator':
                return JsonResponse({'success': False, 'error': 'Permission denied. Physicians must request status changes via Messages.'})
            
            # Get the form and update its status
            try:
                form = PatientForm.objects.get(id=form_id)
                old_status = form.status
                form.status = new_status
                form.save()
                
                # If admin is reverting a decision back to pending, notify physicians
                if (hasattr(request.user, 'profile') and 
                    request.user.profile.role == 'administrator' and
                    old_status in ['approved', 'rejected'] and 
                    new_status == 'pending'):
                    
                    # Create a notification message to physicians
                    notify_physicians_of_status_reversion(form, old_status, request.user)
                
                return JsonResponse({
                    'success': True, 
                    'message': f'Form status updated to {new_status}',
                    'new_status': new_status,
                    'status_display': form.get_status_display()
                })
            except PatientForm.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Form not found'})
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def view_patient_file(request, form_id):
    """View/download the uploaded patient file"""
    try:
        form = PatientForm.objects.get(id=form_id)
        
        # Check if user has permission to view this file
        if hasattr(request.user, 'profile'):
            user_role = request.user.profile.role
            # Allow administrators and screening physicians to view files
            if user_role not in ['administrator', 'screening_physician']:
                # Also allow the user who uploaded the file to view it
                if form.uploaded_by != request.user:
                    return JsonResponse({'success': False, 'error': 'Permission denied'})
        
        if form.uploaded_file:
            # Get file information
            file_url = form.uploaded_file.url
            file_name = os.path.basename(form.uploaded_file.name)
            file_extension = os.path.splitext(file_name)[1].lower()
            
            # Return file information for JavaScript to handle
            return JsonResponse({
                'success': True,
                'file_url': file_url,
                'file_name': file_name,
                'file_extension': file_extension,
                'patient_name': form.patient_name or form.extracted_patient_name or 'Unknown Patient',
                'upload_date': form.uploaded_at.strftime('%Y-%m-%d %H:%M')
            })
        else:
            return JsonResponse({'success': False, 'error': 'No file found for this form'})
            
    except PatientForm.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Form not found'})


def notify_physicians_of_status_reversion(patient_form, old_status, admin_user):
    """Notify physicians when admin reverts a form status back to pending"""
    try:
        from messaging.models import Conversation, Message
        from django.contrib.auth.models import User
        from accounts.models import UserProfile
        
        # Get all physicians
        physicians = User.objects.filter(profile__role='screening_physician')
        
        patient_name = patient_form.patient_name or patient_form.extracted_patient_name or 'Unknown Patient'
        
        # Create a message for each physician
        for physician in physicians:
            # Check if conversation already exists between admin and physician
            existing_conversation = Conversation.objects.filter(
                participants=admin_user
            ).filter(
                participants=physician
            ).annotate(
                participant_count=Count('participants')
            ).filter(
                participant_count=2
            ).first()
            
            if existing_conversation:
                conversation = existing_conversation
            else:
                # Create new conversation
                conversation = Conversation.objects.create(
                    title=f"Form Status Updates - {patient_name}"
                )
                conversation.participants.add(admin_user, physician)
            
            # Create the notification message
            reversion_message = f"""ADMIN STATUS REVERSION NOTICE

The status of patient form for "{patient_name}" has been reverted from {old_status.upper()} back to PENDING for re-evaluation.

Please review this case again and provide your decision.

Patient: {patient_name}
Previous Status: {old_status.title()}
New Status: Pending
Reverted by: {admin_user.get_full_name() or admin_user.username}
Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

This form is now available in your dashboard for review."""
            
            # Create the message
            Message.objects.create(
                conversation=conversation,
                sender=admin_user,
                content=reversion_message
            )
            
    except Exception as e:
        # Log error but don't fail the main operation
        print(f"Error notifying physicians of status reversion: {e}")


@login_required
def delete_patient_form(request, form_id):
    """Delete a patient form (administrators only)"""
    if request.method == 'POST':
        try:
            form = PatientForm.objects.get(id=form_id)
            
            # Check if user has permission to delete this form
            if hasattr(request.user, 'profile'):
                user_role = request.user.profile.role
                # Only administrators can delete forms
                if user_role != 'administrator':
                    return JsonResponse({'success': False, 'error': 'Permission denied. Only administrators can delete forms.'})
            else:
                return JsonResponse({'success': False, 'error': 'Permission denied'})
            
            # Store file info for cleanup
            file_path = None
            if form.uploaded_file:
                file_path = form.uploaded_file.path
            
            patient_name = form.patient_name or form.extracted_patient_name or 'Unknown Patient'
            
            # Delete the form
            form.delete()
            
            # Try to delete the associated file from filesystem
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass  # File deletion failed, but form is already deleted
            
            return JsonResponse({
                'success': True,
                'message': f'Patient form for {patient_name} has been successfully deleted.'
            })
            
        except PatientForm.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Form not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def api_patient_cases(request):
    """API endpoint to get patient cases for administrators"""
    # Only allow administrators to access this
    if not (hasattr(request.user, 'profile') and request.user.profile.role == 'administrator'):
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        # Get recent patient cases (last 20)
        patient_cases = PatientForm.objects.all().order_by('-uploaded_at')[:20]
        
        cases_data = []
        for case in patient_cases:
            cases_data.append({
                'id': case.id,
                'patient_name': case.patient_name,
                'extracted_patient_name': case.extracted_patient_name,
                'uploaded_at': case.uploaded_at.isoformat(),
                'status': case.status,
                'status_display': case.get_status_display(),
                'ai_decision': case.ai_decision,
                'ai_decision_display': case.get_ai_decision_display(),
                'ai_feedback': case.ai_feedback or '',
            })
        
        return JsonResponse({
            'success': True,
            'cases': cases_data
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
