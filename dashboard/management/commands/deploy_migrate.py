from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection


class Command(BaseCommand):
    help = 'Run migrations and show database status for deployment'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== DEPLOYMENT MIGRATION CHECK ==='))
        
        # Show current migration status
        self.stdout.write('\n1. Checking current migration status...')
        call_command('showmigrations', verbosity=1)
        
        # Run migrations
        self.stdout.write('\n2. Running migrations...')
        call_command('migrate', verbosity=1)
        
        # Verify database structure
        self.stdout.write('\n3. Verifying database structure...')
        with connection.cursor() as cursor:
            # Check if previous_status column exists
            cursor.execute("PRAGMA table_info(dashboard_patientform);")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'previous_status' in column_names:
                self.stdout.write(self.style.SUCCESS('✓ previous_status column exists'))
            else:
                self.stdout.write(self.style.ERROR('✗ previous_status column missing'))
            
            # Show all columns
            self.stdout.write(f'Available columns: {", ".join(column_names)}')
        
        self.stdout.write(self.style.SUCCESS('\n=== MIGRATION CHECK COMPLETE ==='))