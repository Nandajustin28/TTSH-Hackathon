from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile
from dashboard.models import PatientForm
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create quick test data for debugging'

    def handle(self, *args, **options):
        # Create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'email': 'admin@test.com'
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            
        # Create or update profile
        profile, created = UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={'role': 'administrator'}
        )
        profile.role = 'administrator'
        profile.save()
        
        # Create physician user
        physician_user, created = User.objects.get_or_create(
            username='doctor',
            defaults={
                'first_name': 'Dr. John',
                'last_name': 'Smith',
                'email': 'doctor@test.com'
            }
        )
        if created:
            physician_user.set_password('doctor123')
            physician_user.save()
            
        # Create or update profile
        profile, created = UserProfile.objects.get_or_create(
            user=physician_user,
            defaults={'role': 'screening_physician'}
        )
        profile.role = 'screening_physician'
        profile.save()
        
        # Create test patient forms
        test_patients = [
            'John Doe',
            'Jane Smith', 
            'Robert Johnson'
        ]
        
        for patient_name in test_patients:
            if not PatientForm.objects.filter(patient_name=patient_name).exists():
                PatientForm.objects.create(
                    patient_name=patient_name,
                    status='pending',
                    ai_decision='accept',
                    uploaded_by=admin_user,
                    processed=True
                )
        
        self.stdout.write(self.style.SUCCESS('Test data created!'))
        self.stdout.write(f'Admin user: admin / admin123')
        self.stdout.write(f'Doctor user: doctor / doctor123')
        self.stdout.write(f'Patient forms: {PatientForm.objects.count()}')