from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from dashboard.models import PatientForm


class Command(BaseCommand):
    help = 'Create user groups and assign permissions'

    def handle(self, *args, **options):
        # Create Administrator group
        admin_group, created = Group.objects.get_or_create(name='Administrator')
        if created:
            self.stdout.write(
                self.style.SUCCESS('Successfully created Administrator group')
            )
        else:
            self.stdout.write('Administrator group already exists')

        # Create Screening Physician group
        physician_group, created = Group.objects.get_or_create(name='Screening Physician')
        if created:
            self.stdout.write(
                self.style.SUCCESS('Successfully created Screening Physician group')
            )
        else:
            self.stdout.write('Screening Physician group already exists')

        # Get content types
        patient_form_ct = ContentType.objects.get_for_model(PatientForm)

        # Administrator permissions (full access)
        admin_permissions = [
            'add_patientform',
            'change_patientform',
            'delete_patientform',
            'view_patientform',
        ]

        for perm_codename in admin_permissions:
            try:
                permission = Permission.objects.get(
                    codename=perm_codename,
                    content_type=patient_form_ct
                )
                admin_group.permissions.add(permission)
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Permission {perm_codename} not found')
                )

        # Screening Physician permissions (view and change only)
        physician_permissions = [
            'view_patientform',
            'change_patientform',
        ]

        for perm_codename in physician_permissions:
            try:
                permission = Permission.objects.get(
                    codename=perm_codename,
                    content_type=patient_form_ct
                )
                physician_group.permissions.add(permission)
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Permission {perm_codename} not found')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully assigned permissions to groups')
        )