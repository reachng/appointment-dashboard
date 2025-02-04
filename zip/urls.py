from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('user_status_analysis/', views.user_status_analysis, name='user_status_analysis'),
    path('total_final_summmary/', views.total_final_summmary, name='total_final_summmary'),
    path('export_g_id_summary/', views.export_g_id_summary, name='export_g_id_summary'),
    path('export_g_id_complaints/', views.export_g_id_complaints, name='export_g_id_complaints'),
    path('export_user_state_count/', views.export_user_state_count, name='export_user_state_count'),
    path('appointment_analysis/', views.appointment_analysis, name='appointment_analysis'),
    path('registration_analysis/', views.registration_analysis, name='registration_analysis'),
]
