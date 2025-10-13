# Generated manually on 2025-10-14 for adding cancelled status

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0006_delete_statuschangelog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patientform',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'), 
                    ('processing', 'Processing'), 
                    ('approved', 'Approved'), 
                    ('rejected', 'Rejected'),
                    ('cancelled', 'Cancelled')
                ], 
                default='pending', 
                max_length=20
            ),
        ),
    ]