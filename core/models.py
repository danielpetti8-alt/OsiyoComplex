# core/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# =====================================================
# BO'LIM (DEPARTMENT)
# =====================================================
class Department(models.Model):
    """Supermarket bo'limlari: Savdo, Omborxona, Kassa, Xavfsizlik"""
    name = models.CharField(max_length=200, verbose_name="Bo'lim nomi")
    description = models.TextField(blank=True, null=True, verbose_name="Bo'lim haqida")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Bo'lim"
        verbose_name_plural = "Bo'limlar"


# =====================================================
# XODIM (EMPLOYEE)
# =====================================================
class Employee(models.Model):
    """Xodim profili - Django User modeliga ulanadi"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Foydalanuvchi")
    
    first_name = models.CharField(max_length=100, verbose_name="Ism")
    last_name = models.CharField(max_length=100, verbose_name="Familiya")
    age = models.PositiveIntegerField(verbose_name="Yosh")
    work_experience = models.CharField(max_length=100, blank=True, verbose_name="Ish staji")
    
    department = models.ForeignKey(
        Department, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="Bo'lim"
    )
    
    senior_employee = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Starshiy xodim",
        related_name='junior_employees'
    )
    
    phone = models.CharField(max_length=20, verbose_name="Telefon raqami")
    is_senior = models.BooleanField(default=False, verbose_name="Starshiy xodimmi?")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.department})"

    class Meta:
        verbose_name = "Xodim"
        verbose_name_plural = "Xodimlar"


# =====================================================
# E'LON (ANNOUNCEMENT)
# =====================================================
class Announcement(models.Model):
    """Rahbariyat tomonidan e'lon qilingan yangiliklar"""
    title = models.CharField(max_length=300, verbose_name="E'lon sarlavhasi")
    content = models.TextField(verbose_name="E'lon matni")
    image = models.ImageField(
        upload_to='announcements/', 
        blank=True, 
        null=True, 
        verbose_name="Rasm (ixtiyoriy)"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="Kim tomonidan"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="Faolmi?")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "E'lon"
        verbose_name_plural = "E'lonlar"
        ordering = ['-created_at']


# =====================================================
# QOIDA (RULE/DOCUMENT)
# =====================================================
class RuleDocument(models.Model):
    """Korxona ichki tartib qoidalari (PDF formatda)"""
    title = models.CharField(max_length=300, verbose_name="Hujjat nomi")
    description = models.TextField(blank=True, verbose_name="Qisqacha tavsif")
    pdf_file = models.FileField(upload_to='documents/', verbose_name="PDF fayl")
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="Kim yuklagan"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Qoida hujjati"
        verbose_name_plural = "Qoida hujjatlari"


# =====================================================
# SAVOL (QUESTION)
# =====================================================
class QuestionBank(models.Model):
    """Savollar bazasi — admin Word fayl yuklaganda shu yerga saqlanadi"""
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE,
        verbose_name="Bo'lim"
    )
    text = models.TextField(verbose_name="Savol matni")
    option_a = models.CharField(max_length=500, verbose_name="A variant")
    option_b = models.CharField(max_length=500, verbose_name="B variant")
    option_c = models.CharField(max_length=500, verbose_name="C variant")
    option_d = models.CharField(max_length=500, verbose_name="D variant")
    
    CORRECT_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]
    correct_answer = models.CharField(
        max_length=1, 
        choices=CORRECT_CHOICES,
        verbose_name="To'g'ri javob"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.department}] {self.text[:60]}..."

    class Meta:
        verbose_name = "Savol"
        verbose_name_plural = "Savollar bazasi"


# =====================================================
# IMTIHON (EXAM)
# =====================================================
class Exam(models.Model):
    """Admin tomonidan yaratilgan imtihon"""
    title = models.CharField(max_length=300, verbose_name="Imtihon nomi")
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE,
        verbose_name="Bo'lim"
    )
    
    # Imtihon vaqti
    exam_date = models.DateField(verbose_name="Imtihon sanasi")
    exam_start_time = models.TimeField(verbose_name="Boshlanish vaqti")
    exam_end_time = models.TimeField(verbose_name="Tugash vaqti")
    
    # Imtihon sozlamalari
    duration_minutes = models.PositiveIntegerField(
        verbose_name="Imtihon davomiyligi (daqiqa)"
    )
    total_questions = models.PositiveIntegerField(
        verbose_name="Savollar soni"
    )
    passing_score = models.PositiveIntegerField(
        verbose_name="O'tish bali (foizda, masalan: 70)"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="Faolmi?")
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="Kim yaratgan"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.department.name}"

    class Meta:
        verbose_name = "Imtihon"
        verbose_name_plural = "Imtihonlar"


# =====================================================
# IMTIHON NATIJASI (EXAM RESULT)
# =====================================================
class ExamResult(models.Model):
    """Xodimning imtihon natijasi"""
    RESULT_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('passed', 'O\'tdi'),
        ('failed', 'O\'tmadi'),
    ]
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, verbose_name="Imtihon")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Xodim")
    
    # Natijalar
    score = models.FloatField(default=0, verbose_name="Ball (foizda)")
    correct_answers = models.PositiveIntegerField(default=0, verbose_name="To'g'ri javoblar")
    wrong_answers = models.PositiveIntegerField(default=0, verbose_name="Noto'g'ri javoblar")
    total_questions = models.PositiveIntegerField(default=0, verbose_name="Jami savollar")
    
    result_status = models.CharField(
        max_length=10, 
        choices=RESULT_CHOICES, 
        default='pending',
        verbose_name="Holat"
    )
    
    # Savollar va javoblar (JSON formatda saqlanadi)
    questions_data = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name="Savollar va javoblar (JSON)"
    )
    user_answers = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name="Foydalanuvchi javoblari (JSON)"
    )
    
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee} - {self.exam} - {self.result_status}"

    class Meta:
        verbose_name = "Imtihon natijasi"
        verbose_name_plural = "Imtihon natijalari"
        unique_together = ['exam', 'employee']  # Bir xodim bir imtihonga faqat bir marta


# =====================================================
# SERTIFIKAT SHABLONI (CERTIFICATE TEMPLATE)
# =====================================================
class CertificateTemplate(models.Model):
    """Sertifikat dizayni shabloni"""
    name = models.CharField(max_length=200, verbose_name="Shablon nomi")
    background_image = models.ImageField(
        upload_to='certificates/templates/',
        verbose_name="Sertifikat fon rasmi"
    )
    # Xodim ismi qayerga yozilishi kerakligi
    name_x = models.IntegerField(default=400, verbose_name="Ism X koordinatasi")
    name_y = models.IntegerField(default=300, verbose_name="Ism Y koordinatasi")
    name_font_size = models.IntegerField(default=24, verbose_name="Ism shrift o'lchami")
    
    # Sana qayerga yozilishi kerakligi
    date_x = models.IntegerField(default=400, verbose_name="Sana X koordinatasi")
    date_y = models.IntegerField(default=450, verbose_name="Sana Y koordinatasi")
    
    is_active = models.BooleanField(default=True, verbose_name="Faolmi?")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Sertifikat shabloni"
        verbose_name_plural = "Sertifikat shablonlari"


# =====================================================
# SERTIFIKAT (CERTIFICATE)
# =====================================================
class Certificate(models.Model):
    """Yaratilgan sertifikatlar"""
    exam_result = models.OneToOneField(
        ExamResult, 
        on_delete=models.CASCADE,
        verbose_name="Imtihon natijasi"
    )
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Xodim")
    certificate_file = models.FileField(
        upload_to='certificates/generated/',
        verbose_name="Sertifikat fayli"
    )
    issued_date = models.DateTimeField(auto_now_add=True, verbose_name="Berilgan sana")
    certificate_number = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name="Sertifikat raqami"
    )

    def __str__(self):
        return f"Sertifikat #{self.certificate_number} - {self.employee}"

    class Meta:
        verbose_name = "Sertifikat"
        verbose_name_plural = "Sertifikatlar"