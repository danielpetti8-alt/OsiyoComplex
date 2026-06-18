# core/admin.py

from django.contrib import admin
from .models import (
    Department, Employee, Announcement, RuleDocument,
    QuestionBank, Exam, ExamResult, CertificateTemplate, Certificate
)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'department', 'phone', 'is_senior']
    list_filter = ['department', 'is_senior']

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'created_at', 'is_active']

@admin.register(RuleDocument)
class RuleDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'uploaded_by', 'uploaded_at']

@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ['text', 'department', 'correct_answer']
    list_filter = ['department']

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'department', 'exam_date', 'total_questions', 'passing_score']
    list_filter = ['department']

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ['employee', 'exam', 'score', 'result_status']
    list_filter = ['result_status']

@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_number', 'employee', 'issued_date']