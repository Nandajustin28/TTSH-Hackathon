# Generated manually for adding uploaded_by field

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dashboard', '0002_patientform_ai_decision_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientform',
            name='uploaded_by',
            field=models.ForeignKey(blank=True, help_text='User who uploaded this form', null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]