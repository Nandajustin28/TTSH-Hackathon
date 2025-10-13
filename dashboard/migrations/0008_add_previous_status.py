# Generated manually on 2025-10-14 for adding previous_status field for undo functionality

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0007_add_cancelled_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientform',
            name='previous_status',
            field=models.CharField(
                blank=True,
                choices=[
                    ('pending', 'Pending'), 
                    ('processing', 'Processing'), 
                    ('approved', 'Approved'), 
                    ('rejected', 'Rejected'),
                    ('cancelled', 'Cancelled')
                ], 
                help_text='Status before cancellation, used for undo',
                max_length=20,
                null=True
            ),
        ),
    ]