from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from .models import Conversation, Message, MessageReadStatus
from dashboard.models import PatientForm
import json
import re

@login_required
def inbox(request):
    """Display user's conversations"""
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        unread_count=Count(
            'messages',
            filter=Q(
                messages__is_read=False
            ) & ~Q(messages__sender=request.user)
        )
    ).order_by('-updated_at')
    
    # Add other participant info to each conversation
    for conv in conversations:
        conv.other_participant = conv.get_other_participant(request.user)
    
    # Paginate conversations
    paginator = Paginator(conversations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Add other participant info to paginated conversations
    for conv in page_obj:
        conv.other_participant = conv.get_other_participant(request.user)
    
    context = {
        'conversations': page_obj,
        'total_unread': sum(conv.unread_count for conv in conversations)
    }
    return render(request, 'messaging/inbox.html', context)

@login_required
def conversation_detail(request, conversation_id):
    """Display a specific conversation and its messages"""
    conversation = get_object_or_404(
        Conversation, 
        id=conversation_id,
        participants=request.user
    )
    
    # Mark messages as read
    unread_messages = conversation.messages.filter(
        ~Q(sender=request.user),
        is_read=False
    )
    for message in unread_messages:
        message.mark_as_read()
        MessageReadStatus.objects.get_or_create(
            message=message,
            user=request.user
        )
    
    # Get messages with pagination
    messages_list = conversation.messages.select_related('sender').order_by('created_at')
    paginator = Paginator(messages_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Handle new message submission
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            # Check if this is a physician decision and automatically add patient case info
            enhanced_content = content
            if (hasattr(request.user, 'profile') and 
                request.user.profile.role == 'screening_physician' and
                any(keyword in content.upper() for keyword in ['ACCEPT', 'REJECT', 'APPROVED', 'DENIED', 'DECISION'])):
                
                # Find the most recent pending patient form
                try:
                    patient_form = PatientForm.objects.filter(status='pending').order_by('-uploaded_at').first()
                    if patient_form:
                        patient_display_name = patient_form.patient_name or patient_form.extracted_patient_name or 'Unknown Patient'
                        case_header = f"📋 PATIENT CASE: {patient_display_name.upper()}\n"
                        case_header += f"📅 Submitted: {patient_form.uploaded_at.strftime('%B %d, %Y at %I:%M %p')}\n\n"
                        
                        # Add case details
                        patient_case_info = f"\n\n--- PATIENT CASE DETAILS ---\n"
                        patient_case_info += f"Patient: {patient_form.patient_name or patient_form.extracted_patient_name or 'Unknown Patient'}\n"
                        patient_case_info += f"Submitted: {patient_form.uploaded_at.strftime('%B %d, %Y at %I:%M %p')}\n"
                        patient_case_info += f"Current Status: {patient_form.get_status_display()}\n"
                        if patient_form.ai_decision:
                            patient_case_info += f"AI Recommendation: {patient_form.get_ai_decision_display()}\n"
                        patient_case_info += "--- END CASE DETAILS ---\n\n"
                        
                        # Format as physician decision
                        if 'PHYSICIAN DECISION:' not in content.upper():
                            enhanced_content = case_header + f"PHYSICIAN DECISION: {content.upper()}\n\n"
                            enhanced_content += f"Form has been reviewed with decision: {content}" + patient_case_info
                        else:
                            enhanced_content = case_header + content + patient_case_info
                            
                        # Update patient form status
                        if any(keyword in content.upper() for keyword in ['ACCEPT', 'APPROVED']):
                            patient_form.status = 'approved'
                            patient_form.save()
                        elif any(keyword in content.upper() for keyword in ['REJECT', 'DENIED']):
                            patient_form.status = 'rejected'
                            patient_form.save()
                except:
                    pass
            
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=enhanced_content
            )
            conversation.updated_at = timezone.now()
            conversation.save()
            messages.success(request, 'Message sent successfully!')
            return redirect('messaging:conversation_detail', conversation_id=conversation.id)
        else:
            messages.error(request, 'Message content cannot be empty.')
    
    context = {
        'conversation': conversation,
        'messages': page_obj,
        'other_participant': conversation.get_other_participant(request.user)
    }
    return render(request, 'messaging/conversation_detail.html', context)

@login_required
def start_conversation(request):
    """Start a new conversation with another user"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        initial_message = request.POST.get('message', '').strip()
        physician_decision = request.POST.get('physician_decision', '').strip()
        
        # Extract patient case information from the initial message if it contains patient form reference
        patient_case_info = ""
        patient_form = None
        if initial_message and 'patient form:' in initial_message.lower():
            import re
            patient_match = re.search(r'patient form: (.+?)(?:\n|$)', initial_message)
            if patient_match:
                patient_name = patient_match.group(1).strip()
                # Try to find the actual patient form
                try:
                    patient_form = PatientForm.objects.filter(
                        Q(patient_name__icontains=patient_name) | 
                        Q(extracted_patient_name__icontains=patient_name)
                    ).order_by('-uploaded_at').first()
                    
                    if patient_form:
                        patient_case_info = f"\n\n--- PATIENT CASE DETAILS ---\n"
                        patient_case_info += f"Patient: {patient_form.patient_name or patient_form.extracted_patient_name or 'Unknown Patient'}\n"
                        patient_case_info += f"Submitted: {patient_form.uploaded_at.strftime('%B %d, %Y at %I:%M %p')}\n"
                        patient_case_info += f"Current Status: {patient_form.get_status_display()}\n"
                        if patient_form.ai_decision:
                            patient_case_info += f"AI Recommendation: {patient_form.get_ai_decision_display()}\n"
                        patient_case_info += "--- END CASE DETAILS ---\n\n"
                except:
                    pass

        # Build the final message with decision if provided
        final_message = ""
        
        # Build admin/physician message
        if physician_decision:
            # If no patient form found from message, try to find the most recent pending form
            if not patient_form:
                try:
                    patient_form = PatientForm.objects.filter(status='pending').order_by('-uploaded_at').first()
                    if patient_form:
                        patient_case_info = f"\n\n--- PATIENT CASE DETAILS ---\n"
                        patient_case_info += f"Patient: {patient_form.patient_name or patient_form.extracted_patient_name or 'Unknown Patient'}\n"
                        patient_case_info += f"Submitted: {patient_form.uploaded_at.strftime('%B %d, %Y at %I:%M %p')}\n"
                        patient_case_info += f"Current Status: {patient_form.get_status_display()}\n"
                        if patient_form.ai_decision:
                            patient_case_info += f"AI Recommendation: {patient_form.get_ai_decision_display()}\n"
                        patient_case_info += "--- END CASE DETAILS ---\n\n"
                except:
                    pass
            
            # Create a header with patient case information if available
            case_header = ""
            if patient_form:
                patient_display_name = patient_form.patient_name or patient_form.extracted_patient_name or 'Unknown Patient'
                case_header = f"📋 PATIENT CASE: {patient_display_name.upper()}\n"
                case_header += f"📅 Submitted: {patient_form.uploaded_at.strftime('%B %d, %Y at %I:%M %p')}\n\n"
            
            decision_messages = {
                'accept': 'PHYSICIAN DECISION: ACCEPT\n\nForm has been reviewed and approved for processing.',
                'reject': 'PHYSICIAN DECISION: REJECT\n\nForm requires attention or has issues that need to be addressed.',
                'review': 'PHYSICIAN DECISION: NEEDS REVIEW\n\nForm requires additional review or clarification.'
            }
            final_message = case_header + decision_messages.get(physician_decision, '')
            
            # Add detailed patient case information if available
            if patient_case_info:
                final_message = final_message + patient_case_info
            
            if initial_message and not initial_message.startswith('PHYSICIAN DECISION:'):
                final_message += f'\n\nAdditional Notes:\n{initial_message}'
        else:
            # Handle regular messages (no decision, no patient case selected)
            final_message = initial_message
        
        if not username:
            messages.error(request, 'Please provide a username.')
            return render(request, 'messaging/start_conversation.html')
        
        # Get the user to message
        try:
            recipient = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, f'User "{username}" not found.')
            return render(request, 'messaging/start_conversation.html')
        
        if recipient == request.user:
            messages.error(request, 'You cannot send a message to yourself.')
            return render(request, 'messaging/start_conversation.html')
        
        # Check if conversation already exists
        existing_conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=recipient
        ).annotate(
            participant_count=Count('participants')
        ).filter(
            participant_count=2
        ).first()
        
        if existing_conversation:
            # Add message to existing conversation
            if final_message:
                Message.objects.create(
                    conversation=existing_conversation,
                    sender=request.user,
                    content=final_message
                )
                existing_conversation.updated_at = timezone.now()
                existing_conversation.save()
                
                # Update patient form status if physician decision is made
                if physician_decision and hasattr(request.user, 'profile') and request.user.profile.role == 'screening_physician':
                    update_patient_form_status(final_message, physician_decision, patient_form)
                    
            success_msg = 'Decision sent!' if physician_decision else 'Message sent!'
            messages.success(request, success_msg)
            return redirect('messaging:conversation_detail', conversation_id=existing_conversation.id)
        
        # Create new conversation
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, recipient)
        
        # Add initial message if provided
        if final_message:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=final_message
            )
        
        # Update patient form status if physician decision is made
        if physician_decision and hasattr(request.user, 'profile') and request.user.profile.role == 'screening_physician':
            update_patient_form_status(final_message, physician_decision, patient_form)
        
        success_msg = 'Decision sent!' if physician_decision else 'Conversation started!'
        messages.success(request, success_msg)
        return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    
    # Get all users except current user for autocomplete
    users = User.objects.exclude(id=request.user.id).order_by('username')
    
    # Handle pre-filled recipient and message from URL parameters
    recipient_username = request.GET.get('recipient', '')
    pre_message = request.GET.get('message', '')
    
    context = {
        'users': users,
        'recipient_username': recipient_username,
        'pre_message': pre_message,
    }
    return render(request, 'messaging/start_conversation.html', context)

@login_required
def send_message_ajax(request):
    """Send a message via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            conversation_id = data.get('conversation_id')
            content = data.get('content', '').strip()
            
            if not content:
                return JsonResponse({'success': False, 'error': 'Message content cannot be empty.'})
            
            conversation = get_object_or_404(
                Conversation,
                id=conversation_id,
                participants=request.user
            )
            
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            
            conversation.updated_at = timezone.now()
            conversation.save()
            
            return JsonResponse({
                'success': True,
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender': message.sender.username,
                    'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            })
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def user_search_ajax(request):
    """Search for users via AJAX for autocomplete"""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'users': []})
    
    users = User.objects.filter(
        Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
    ).exclude(id=request.user.id)[:10]
    
    user_data = [{
        'id': user.id,
        'username': user.username,
        'full_name': user.get_full_name() or user.username
    } for user in users]
    
    return JsonResponse({'users': user_data})


def update_patient_form_status(message_content, physician_decision, patient_form=None):
    """Update patient form status based on physician decision"""
    try:
        # Use provided patient form if available, otherwise try to find it from message content
        if not patient_form:
            # Extract patient name from message content that contains "patient form:"
            patient_name_match = re.search(r'patient form:\s*([^,\n]+)', message_content, re.IGNORECASE)
            
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip()
                
                # Find the most recent patient form with this name
                patient_forms = PatientForm.objects.filter(
                    Q(patient_name__icontains=patient_name) | 
                    Q(extracted_patient_name__icontains=patient_name)
                ).filter(status='pending').order_by('-uploaded_at')
                
                if patient_forms.exists():
                    patient_form = patient_forms.first()
        
        if patient_form:
            # Map physician decision to form status
            status_mapping = {
                'accept': 'approved',
                'reject': 'rejected',
                'review': 'pending'  # Keep as pending for review
            }
            
            new_status = status_mapping.get(physician_decision)
            if new_status:
                patient_form.status = new_status
                patient_form.save()
                    
        # If no specific patient form mentioned, try to find the most recent pending form
        elif physician_decision in ['accept', 'reject']:
            recent_form = PatientForm.objects.filter(status='pending').order_by('-uploaded_at').first()
            if recent_form:
                status_mapping = {
                    'accept': 'approved',
                    'reject': 'rejected'
                }
                recent_form.status = status_mapping[physician_decision]
                recent_form.save()
                
    except Exception as e:
        # Log error but don't fail the message sending
        print(f"Error updating patient form status: {e}")

@login_required
def delete_message(request, message_id):
    """Delete a message (only sender can delete their own messages)"""
    if request.method == 'POST':
        try:
            message = get_object_or_404(Message, id=message_id)
            
            # Check if user has permission to delete this message
            if message.sender != request.user:
                return JsonResponse({'success': False, 'error': 'Permission denied. You can only delete your own messages.'})
            
            # Store conversation info before deletion
            conversation_id = message.conversation.id
            message_content_preview = message.content[:50] + "..." if len(message.content) > 50 else message.content
            
            # Delete the message
            message.delete()
            
            # Update conversation's updated_at timestamp if this was the last message
            conversation = message.conversation
            last_message = conversation.get_last_message()
            if not last_message or last_message.created_at < message.created_at:
                conversation.updated_at = timezone.now()
                conversation.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Message deleted successfully.',
                'conversation_id': conversation_id
            })
            
        except Message.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Message not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def delete_conversation(request, conversation_id):
    """Delete an entire conversation (only participants can delete)"""
    if request.method == 'POST':
        try:
            conversation = get_object_or_404(Conversation, id=conversation_id)
            
            # Check if user is a participant in this conversation
            if not conversation.participants.filter(id=request.user.id).exists():
                return JsonResponse({'success': False, 'error': 'Permission denied. You are not a participant in this conversation.'})
            
            # Store conversation info before deletion
            other_participant = conversation.get_other_participant(request.user)
            conversation_title = conversation.title or (other_participant.get_full_name() if other_participant else "Unknown")
            message_count = conversation.messages.count()
            
            # Delete the entire conversation (this will cascade delete all messages)
            conversation.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Conversation with {conversation_title} has been deleted ({message_count} messages removed).'
            })
            
        except Conversation.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Conversation not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
