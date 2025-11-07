from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
import os

def upload_to(instance, filename):
    """Generate upload path for patient forms"""
    return os.path.join('patient_forms', filename)

class PatientForm(models.Model):
    """Model to store uploaded patient forms"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    def can_be_cancelled(self):
        return self.status in ['approved', 'rejected']

    def is_cancelled(self):
        return self.status == 'cancelled'
    
    def can_undo_cancellation(self):
        try:
            return self.status == 'cancelled' and hasattr(self, 'previous_status') and self.previous_status in ['approved', 'rejected']
        except:
            return False
    
    def undo_cancellation(self):
        """Restore the form to its previous status before cancellation"""
        try:
            if self.can_undo_cancellation():
                self.status = self.previous_status
                self.previous_status = None
                return True
        except:
            pass
        return False
    
    AI_DECISION_CHOICES = [
        ('analyzing', 'Analyzing...'),
        ('accept', 'Accept'),
        ('reject', 'Reject'),
        ('review_required', 'Review Required'),
    ]
    
    patient_name = models.CharField(max_length=255, blank=True, null=True, help_text="Will be extracted from form if not provided")
    uploaded_file = models.FileField(
        upload_to=upload_to,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'png', 'jpg', 'jpeg'])],
        help_text="Supported: PDF, PNG, JPG (Max 10MB)"
    )
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, help_text="User who uploaded this form")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    previous_status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True, null=True, help_text="Status before cancellation, used for undo")
    ai_decision = models.CharField(max_length=20, choices=AI_DECISION_CHOICES, default='analyzing')
    ai_feedback = models.TextField(blank=True, null=True)
    extracted_patient_name = models.CharField(max_length=255, blank=True, null=True)
    processing_time_seconds = models.IntegerField(null=True, blank=True, help_text="Processing time in seconds")
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Form for {self.patient_name or self.extracted_patient_name or 'Unknown'} - {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def file_size_mb(self):
        """Return file size in MB"""
        if self.uploaded_file:
            return round(self.uploaded_file.size / (1024 * 1024), 2)
        return 0
    
    @property
    def processing_time_display(self):
        """Return formatted processing time"""
        if self.processing_time_seconds:
            minutes = self.processing_time_seconds // 60
            seconds = self.processing_time_seconds % 60
            if minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        elif self.processed:
            return "Completed"
        else:
            return "Processing..."
    
    @property
    def status_display(self):
        """Return human-readable status"""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    @property
    def ai_decision_display(self):
        """Return human-readable AI decision"""
        return dict(self.AI_DECISION_CHOICES).get(self.ai_decision, self.ai_decision)
