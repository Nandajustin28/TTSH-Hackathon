from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dashboard.models import PatientForm
from accounts.models import UserProfile
from datetime import datetime, timedelta
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Create sample patient forms and users for testing'

    def handle(self, *args, **options):
        # Create test users if they don't exist
        admin_user, created = User.objects.get_or_create(
            username='admin_test',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'email': 'admin@test.com',
                'is_staff': True
            }
        )
        if created:
            admin_user.set_password('testpass123')
            admin_user.save()
            # Create profile
            profile, _ = UserProfile.objects.get_or_create(
                user=admin_user,
                defaults={'role': 'administrator'}
            )
            self.stdout.write(f'Created admin user: {admin_user.username}')

        physician_user, created = User.objects.get_or_create(
            username='dr_smith',
            defaults={
                'first_name': 'Dr. John',
                'last_name': 'Smith',
                'email': 'doctor@test.com'
            }
        )
        if created:
            physician_user.set_password('testpass123')
            physician_user.save()
            # Create profile
            profile, _ = UserProfile.objects.get_or_create(
                user=physician_user,
                defaults={'role': 'screening_physician'}
            )
            self.stdout.write(f'Created physician user: {physician_user.username}')

        # Create sample patient forms
        sample_patients = [
            {
                'patient_name': 'John Doe',
                'status': 'pending',
                'ai_decision': 'accept',
                'ai_feedback': 'Patient meets all criteria for approval. All required fields are complete.'
            },
            {
                'patient_name': 'Jane Smith',
                'status': 'pending',
                'ai_decision': 'review_required',
                'ai_feedback': 'Missing some documentation. Requires manual review.'
            },
            {
                'patient_name': 'Robert Johnson',
                'status': 'pending',
                'ai_decision': 'reject',
                'ai_feedback': 'Does not meet eligibility criteria based on current information.'
            },
            {
                'patient_name': 'Emily Davis',
                'status': 'approved',
                'ai_decision': 'accept',
                'ai_feedback': 'Excellent candidate. All requirements satisfied.'
            }
        ]

        for patient_data in sample_patients:
            # Create if doesn't exist
            if not PatientForm.objects.filter(patient_name=patient_data['patient_name']).exists():
                # Create with different upload times
                upload_time = timezone.now() - timedelta(
                    hours=random.randint(1, 72),
                    minutes=random.randint(0, 59)
                )
                
                patient_form = PatientForm.objects.create(
                    patient_name=patient_data['patient_name'],
                    extracted_patient_name=patient_data['patient_name'],
                    status=patient_data['status'],
                    ai_decision=patient_data['ai_decision'],
                    ai_feedback=patient_data['ai_feedback'],
                    uploaded_by=admin_user,
                    processed=True,
                    processing_time_seconds=random.randint(5, 30)
                )
                # Set custom upload time
                patient_form.uploaded_at = upload_time
                patient_form.save()
                
                self.stdout.write(f'Created patient form for: {patient_data["patient_name"]}')

        self.stdout.write(
            self.style.SUCCESS('Successfully created test data!')
        )
        self.stdout.write('You can now test the messaging system with:')
        self.stdout.write(f'- Admin user: admin_test (password: testpass123)')
        self.stdout.write(f'- Physician user: dr_smith (password: testpass123)')
        self.stdout.write(f'- {PatientForm.objects.count()} patient forms available')