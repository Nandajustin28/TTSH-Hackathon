from django.core.management.base import BaseCommand
from django.db import connection
import os
import re


class Command(BaseCommand):
    help = 'Enable previous_status functionality after database migration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== ENABLING PREVIOUS_STATUS FUNCTIONALITY ==='))
        
        # Check if previous_status column exists
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(dashboard_patientform);")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'previous_status' not in column_names:
                self.stdout.write(self.style.ERROR('✗ previous_status column not found. Run migrations first.'))
                return
            
            self.stdout.write(self.style.SUCCESS('✓ previous_status column exists'))
        
        # Path to models.py
        models_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models.py')
        
        if not os.path.exists(models_path):
            self.stdout.write(self.style.ERROR(f'Models file not found at {models_path}'))
            return
        
        # Read current models.py
        with open(models_path, 'r') as f:
            content = f.read()
        
        # Check if field is already enabled
        if 'previous_status = models.CharField' in content and not content.count('# previous_status = models.CharField'):
            self.stdout.write(self.style.WARNING('✓ previous_status field is already enabled'))
            return
        
        # Enable the previous_status field
        content = content.replace(
            '    # previous_status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True, null=True, help_text="Status before cancellation, used for undo")',
            '    previous_status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True, null=True, help_text="Status before cancellation, used for undo")'
        )
        
        # Enable the undo methods
        content = re.sub(
            r'def can_undo_cancellation\(self\):\s*# Temporarily disabled.*?return False.*?# except:\s*#     return False',
            '''def can_undo_cancellation(self):
        try:
            return self.status == 'cancelled' and hasattr(self, 'previous_status') and self.previous_status in ['approved', 'rejected']
        except:
            return False''',
            content,
            flags=re.DOTALL
        )
        
        content = re.sub(
            r'def undo_cancellation\(self\):\s*""".*?""".*?# Temporarily disabled.*?return False.*?# return False',
            '''def undo_cancellation(self):
        """Restore the form to its previous status before cancellation"""
        try:
            if self.can_undo_cancellation():
                self.status = self.previous_status
                self.previous_status = None
                return True
        except:
            pass
        return False''',
            content,
            flags=re.DOTALL
        )
        
        # Write back to file
        with open(models_path, 'w') as f:
            f.write(content)
        
        self.stdout.write(self.style.SUCCESS('✓ previous_status functionality enabled successfully'))
        self.stdout.write(self.style.SUCCESS('=== PREVIOUS_STATUS ACTIVATION COMPLETE ==='))
        self.stdout.write(self.style.WARNING('Please restart your Django application for changes to take effect.'))