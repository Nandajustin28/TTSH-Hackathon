from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('upload/', views.upload_form, name='upload_form'),
    path('database/', views.database_view, name='database'),
    path('time-saved/', views.time_saved_analytics, name='time_saved'),
    path('settings/', views.settings_view, name='settings'),
    path('ajax-upload/', views.ajax_upload, name='ajax_upload'),
    path('update-form-status/', views.update_form_status, name='update_form_status'),
    path('undo-cancellation/', views.undo_cancellation, name='undo_cancellation'),
    path('view-file/<int:form_id>/', views.view_patient_file, name='view_patient_file'),
    path('delete-form/<int:form_id>/', views.delete_patient_form, name='delete_patient_form'),
    path('api/patient-cases/', views.api_patient_cases, name='api_patient_cases'),
]
