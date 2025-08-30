from django.urls import path
from . import views

app_name = 'converter'

urlpatterns = [
    path('dashboard/', views.converter_dashboard, name='dashboard'),
    path('upload/', views.upload_video, name='upload_video'),
    path('download/<str:conversion_id>/', views.download_audio, name='download_audio'),
    path('srt/<str:conversion_id>/', views.download_srt, name='download_srt'),
    path('status/<str:conversion_id>/', views.conversion_status, name='conversion_status'),
    path('delete/<str:conversion_id>/', views.delete_conversion, name='delete_conversion'),
    path('history/', views.conversion_history, name='conversion_history'),
]
