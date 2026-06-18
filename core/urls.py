# core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # --- Autentifikatsiya (Login/Logout) ---
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # --- Dashboard (asosiy sahifa) ---
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # --- Admin paneli ---
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/employees/', views.manage_employees, name='manage_employees'),
    path('admin-panel/employees/create/', views.create_employee, name='create_employee'),
    path('admin-panel/employees/<int:pk>/edit/', views.edit_employee, name='edit_employee'),
    path('admin-panel/employees/<int:pk>/delete/', views.delete_employee, name='delete_employee'),
    
    # --- E'lonlar ---
    path('admin-panel/announcements/', views.manage_announcements, name='manage_announcements'),
    path('admin-panel/announcements/create/', views.create_announcement, name='create_announcement'),
    
    # --- Qoidalar ---
    path('admin-panel/rules/', views.manage_rules, name='manage_rules'),
    path('admin-panel/rules/upload/', views.upload_rule, name='upload_rule'),
    
    # --- Imtihonlar ---
    path('admin-panel/exams/', views.manage_exams, name='manage_exams'),
    path('admin-panel/exams/create/', views.create_exam, name='create_exam'),
    path('admin-panel/questions/upload/', views.upload_questions, name='upload_questions'),
    path('admin-panel/exams/<int:pk>/edit/', views.edit_exam, name='edit_exam'),
    path('admin-panel/exams/<int:pk>/delete/', views.delete_exam, name='delete_exam'),

    # --- Savollar boshqaruvi (qo'lda) ---
    path('admin-panel/questions/', views.manage_questions, name='manage_questions'),
    path('admin-panel/questions/create/', views.create_question, name='create_question'),
    path('admin-panel/questions/<int:pk>/edit/', views.edit_question, name='edit_question'),
    path('admin-panel/questions/<int:pk>/delete/', views.delete_question, name='delete_question'),

    # --- Sertifikatlar ---
    path('admin-panel/certificates/', views.manage_certificates, name='manage_certificates'),
    path('admin-panel/certificates/template/upload/', views.upload_cert_template, name='upload_cert_template'),
    path('admin-panel/certificates/<int:pk>/regenerate/', views.regenerate_certificate_admin, name='regenerate_certificate_admin'),
    path('admin-panel/certificates/<int:pk>/regenerate/', views.regenerate_certificate_admin, name='regenerate_certificate_admin'),
    
    # --- Xodim paneli ---
    path('employee/announcements/', views.employee_announcements, name='employee_announcements'),
    path('employee/rules/', views.employee_rules, name='employee_rules'),
    path('employee/exams/', views.employee_exams, name='employee_exams'),
    path('employee/exams/<int:pk>/start/', views.start_exam, name='start_exam'),
    path('employee/exams/<int:pk>/submit/', views.submit_exam, name='submit_exam'),
    path('employee/exams/<int:pk>/result/', views.exam_result, name='exam_result'),
    path('employee/certificates/', views.employee_certificates, name='employee_certificates'),
    path('employee/certificates/<int:pk>/download/', views.download_certificate, name='download_certificate'),
]   