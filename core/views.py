# core/views.py

import random
import json
import io
from datetime import datetime, date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, FileResponse
from django.utils import timezone
from django.conf import settings
from .models import (
    Department, Employee, Announcement, RuleDocument,
    QuestionBank, Exam, ExamResult, CertificateTemplate, Certificate
)

# =====================================================
# LOGIN / LOGOUT
# =====================================================
def get_exam_window(exam):
    """Imtihonning start va end datetime qiymatlari"""
    tz = timezone.get_current_timezone()

    start_dt = datetime.combine(exam.exam_date, exam.exam_start_time)
    end_dt = datetime.combine(exam.exam_date, exam.exam_end_time)

    if timezone.is_naive(start_dt):
        start_dt = timezone.make_aware(start_dt, tz)
    if timezone.is_naive(end_dt):
        end_dt = timezone.make_aware(end_dt, tz)

    return start_dt, end_dt


def get_exam_status(exam):
    """Imtihon holatini aniqlash: not_started / available / ended"""
    now = timezone.localtime()
    start_dt, end_dt = get_exam_window(exam)

    if now < start_dt:
        return 'not_started', start_dt, end_dt
    elif now > end_dt:
        return 'ended', start_dt, end_dt
    else:
        return 'available', start_dt, end_dt
    
def login_view(request):
    """Kirish sahifasi"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Xush kelibsiz, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Login yoki parol noto\'g\'ri!')
    
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """Chiqish"""
    logout(request)
    return redirect('login')


# =====================================================
# DASHBOARD (Asosiy sahifa)
# =====================================================

@login_required
def dashboard(request):
    """Foydalanuvchi turiga qarab boshqaruv paneliga yo'naltirish"""
    
    # Admin tekshirish
    if request.user.is_staff or request.user.is_superuser:
        context = {
            'total_employees': Employee.objects.count(),
            'total_exams': Exam.objects.count(),
            'total_announcements': Announcement.objects.filter(is_active=True).count(),
            'recent_results': ExamResult.objects.all().order_by('-started_at')[:10],
        }
        return render(request, 'admin_panel/dashboard.html', context)
    
    # Oddiy xodim
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Sizning profilingiz topilmadi. Admin bilan bog\'laning.')
        logout(request)
        return redirect('login')
    
    # O'tkazilgan imtihonlar
    passed_exams = ExamResult.objects.filter(
        employee=employee, 
        result_status='passed'
    ).count()
    
    # Kutilayotgan imtihonlar
    upcoming_exams = Exam.objects.filter(
        department=employee.department,
        is_active=True,
        exam_date__gte=date.today()
    )
    
    # Sertifikatlar
    certificates = Certificate.objects.filter(employee=employee)
    
    context = {
        'employee': employee,
        'passed_exams': passed_exams,
        'upcoming_exams': upcoming_exams,
        'certificates': certificates,
        'recent_results': ExamResult.objects.filter(employee=employee).order_by('-started_at')[:5],
    }
    return render(request, 'employee/dashboard.html', context)


# =====================================================
# ADMIN PANEL — XODIMLAR BOSHQARUVI
# =====================================================

@login_required
def admin_panel(request):
    """Admin paneli asosiy sahifasi"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Sizda admin huquqi yo\'q!')
        return redirect('dashboard')
    
    return redirect('manage_employees')


@login_required
def manage_employees(request):
    """Xodimlar ro'yxati"""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')
    
    employees = Employee.objects.select_related('department', 'senior_employee', 'user').all()
    departments = Department.objects.all()
    
    # Bo'yicha filter
    dept_filter = request.GET.get('department')
    if dept_filter:
        employees = employees.filter(department_id=dept_filter)
    
    context = {
        'employees': employees,
        'departments': departments,
        'selected_dept': dept_filter,
    }
    return render(request, 'admin_panel/manage_employees.html', context)


@login_required
def create_employee(request):
    """Yangi xodim yaratish"""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')
    
    departments = Department.objects.all()
    
    if request.method == 'POST':
        try:
            # Ma'lumotlarni olish
            username = request.POST.get('username')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            age = request.POST.get('age')
            work_experience = request.POST.get('work_experience', '')
            department_id = request.POST.get('department')
            senior_id = request.POST.get('senior_employee')
            phone = request.POST.get('phone')
            is_senior = request.POST.get('is_senior') == 'on'
            
            # Username mavjudligini tekshirish
            if User.objects.filter(username=username).exists():
                messages.error(request, f'XATOLIK: "{username}" logini band! Iltimos boshqasini kiriting.')
                return redirect('create_employee')
            
            # Django User yaratish
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            
            # Employee profil yaratish
            department = Department.objects.filter(id=department_id).first() if department_id else None
            senior = Employee.objects.filter(id=senior_id).first() if senior_id else None
            
            Employee.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                age=int(age) if age else 0,
                work_experience=work_experience,
                department=department,
                senior_employee=senior,
                phone=phone,
                is_senior=is_senior,
            )
            
            messages.success(request, f'{first_name} {last_name} muvaffaqiyatli bazaga qo\'shildi!')
            return redirect('manage_employees')
            
        except Exception as e:
            # XATONI TERMINALGA CHIQARISH
            print("\n\n======== XATOLIK YUZ BERDI ========")
            print(f"SABAB: {str(e)}")
            print("===================================\n\n")
            messages.error(request, f'Tizim xatosi yuz berdi: {str(e)}')
            return redirect('create_employee')
    
    context = {
        'departments': departments,
        'seniors': Employee.objects.filter(is_senior=True),
    }
    return render(request, 'admin_panel/create_employee.html', context)


@login_required
def edit_employee(request, pk):
    """Xodim ma'lumotlarini tahrirlash"""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')
    
    employee = get_object_or_404(Employee, pk=pk)
    departments = Department.objects.all()
    
    if request.method == 'POST':
        employee.first_name = request.POST.get('first_name')
        employee.last_name = request.POST.get('last_name')
        employee.age = int(request.POST.get('age'))
        employee.work_experience = request.POST.get('work_experience', '')
        employee.phone = request.POST.get('phone')
        employee.is_senior = request.POST.get('is_senior') == 'on'
        
        dept_id = request.POST.get('department')
        employee.department = Department.objects.get(id=dept_id) if dept_id else None
        
        senior_id = request.POST.get('senior_employee')
        employee.senior_employee = Employee.objects.get(id=senior_id) if senior_id else None
        
        # Parol o'zgartirish (ixtiyoriy)
        new_password = request.POST.get('new_password')
        if new_password:
            employee.user.set_password(new_password)
            employee.user.save()
        
        employee.user.first_name = employee.first_name
        employee.user.last_name = employee.last_name
        employee.user.save()
        employee.save()
        
        messages.success(request, f'{employee.first_name} {employee.last_name} ma\'lumotlari yangilandi!')
        return redirect('manage_employees')
    
    context = {
        'employee': employee,
        'departments': departments,
        'seniors': Employee.objects.filter(is_senior=True).exclude(pk=pk),
    }
    return render(request, 'admin_panel/edit_employee.html', context)


@login_required
def delete_employee(request, pk):
    """Xodimni o'chirish"""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')
    
    employee = get_object_or_404(Employee, pk=pk)
    name = f"{employee.first_name} {employee.last_name}"
    employee.user.delete()
    messages.success(request, f'{name} o\'chirildi.')
    return redirect('manage_employees')


# =====================================================
# QOLGAN FUNKSIYALAR
# =====================================================

@login_required
def manage_announcements(request):
    if not (request.user.is_staff or request.user.is_superuser): return redirect('dashboard')
    announcements = Announcement.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/manage_announcements.html', {'announcements': announcements})

@login_required
def create_announcement(request):
    if not (request.user.is_staff or request.user.is_superuser): return redirect('dashboard')
    if request.method == 'POST':
        Announcement.objects.create(
            title=request.POST.get('title'),
            content=request.POST.get('content'),
            image=request.FILES.get('image'),
            created_by=request.user,
        )
        messages.success(request, 'E\'lon muvaffaqiyatli yaratildi!')
        return redirect('manage_announcements')
    return render(request, 'admin_panel/create_announcement.html')

@login_required
def manage_rules(request):
    if not (request.user.is_staff or request.user.is_superuser): return redirect('dashboard')
    rules = RuleDocument.objects.all().order_by('-uploaded_at')
    return render(request, 'admin_panel/manage_rules.html', {'rules': rules})

@login_required
def upload_rule(request):
    if not (request.user.is_staff or request.user.is_superuser): return redirect('dashboard')
    if request.method == 'POST':
        RuleDocument.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            pdf_file=request.FILES.get('pdf_file'),
            uploaded_by=request.user,
        )
        messages.success(request, 'Hujjat muvaffaqiyatli yuklandi!')
        return redirect('manage_rules')
    return render(request, 'admin_panel/upload_rule.html')

@login_required
def upload_questions(request):
    if not (request.user.is_staff or request.user.is_superuser): return redirect('dashboard')
    departments = Department.objects.all()
    if request.method == 'POST':
        word_file = request.FILES.get('word_file')
        department_id = request.POST.get('department')
        if not word_file:
            messages.error(request, 'Fayl tanlanmagan!')
            return redirect('upload_questions')
        department = get_object_or_404(Department, id=department_id)
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument(word_file)
            full_text = '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
            questions_raw = full_text.split('---')
            count = 0
            for q_raw in questions_raw:
                q_raw = q_raw.strip()
                if not q_raw: continue
                lines = [line.strip() for line in q_raw.split('\n') if line.strip()]
                question_text = option_a = option_b = option_c = option_d = correct = ''
                for line in lines:
                    if line.startswith('Savol:'): question_text = line.replace('Savol:', '').strip()
                    elif line.startswith('A)'): option_a = line.replace('A)', '').strip()
                    elif line.startswith('B)'): option_b = line.replace('B)', '').strip()
                    elif line.startswith('C)'): option_c = line.replace('C)', '').strip()
                    elif line.startswith('D)'): option_d = line.replace('D)', '').strip()
                    elif line.startswith("To'g'ri javob:"): correct = line.replace("To'g'ri javob:", '').strip().upper()
                if question_text and option_a and correct:
                    QuestionBank.objects.create(
                        department=department, text=question_text, option_a=option_a, option_b=option_b,
                        option_c=option_c, option_d=option_d, correct_answer=correct
                    )
                    count += 1
            messages.success(request, f'{count} ta savol yuklandi!')
        except Exception as e: messages.error(request, f'Xatolik: {str(e)}')
        return redirect('upload_questions')
    return render(request, 'admin_panel/upload_questions.html', {'departments': departments, 'total_questions': QuestionBank.objects.count()})
@login_required
def manage_questions(request):
    """Savollar ro'yxati va boshqaruvi"""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')
    
    questions = QuestionBank.objects.select_related('department').all().order_by('-created_at')
    departments = Department.objects.all()
    
    # Filter
    dept_filter = request.GET.get('department')
    if dept_filter:
        questions = questions.filter(department_id=dept_filter)
    
    # Statistika
    stats = {}
    for dept in departments:
        stats[dept.name] = QuestionBank.objects.filter(department=dept).count()
    
    context = {
        'questions': questions,
        'departments': departments,
        'selected_dept': dept_filter,
        'stats': stats,
        'total': QuestionBank.objects.count(),
    }
    return render(request, 'admin_panel/manage_questions.html', context)


@login_required
def create_question(request):
    """Yangi savol qo'lda yaratish"""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')
    
    departments = Department.objects.all()
    
    if request.method == 'POST':
        try:
            QuestionBank.objects.create(
                department_id=request.POST.get('department'),
                text=request.POST.get('text'),
                option_a=request.POST.get('option_a'),
                option_b=request.POST.get('option_b'),
                option_c=request.POST.get('option_c'),
                option_d=request.POST.get('option_d'),
                correct_answer=request.POST.get('correct_answer'),
            )
            messages.success(request, '✅ Savol muvaffaqiyatli qo\'shildi!')
            
            # "Yana qo'shish" tugmasi bosilgan bo'lsa
            if request.POST.get('save_and_add'):
                return redirect('create_question')
            return redirect('manage_questions')
        except Exception as e:
            messages.error(request, f'Xatolik: {str(e)}')
    
    return render(request, 'admin_panel/create_question.html', {'departments': departments})


@login_required
def edit_question(request, pk):
    """Savolni tahrirlash"""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')
    
    question = get_object_or_404(QuestionBank, pk=pk)
    departments = Department.objects.all()
    
    if request.method == 'POST':
        question.department_id = request.POST.get('department')
        question.text = request.POST.get('text')
        question.option_a = request.POST.get('option_a')
        question.option_b = request.POST.get('option_b')
        question.option_c = request.POST.get('option_c')
        question.option_d = request.POST.get('option_d')
        question.correct_answer = request.POST.get('correct_answer')
        question.save()
        messages.success(request, '✅ Savol yangilandi!')
        return redirect('manage_questions')
    
    return render(request, 'admin_panel/edit_question.html', {'question': question, 'departments': departments})


@login_required
def delete_question(request, pk):
    """Savolni o'chirish"""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')
    
    question = get_object_or_404(QuestionBank, pk=pk)
    question.delete()
    messages.success(request, 'Savol o\'chirildi.')
    return redirect('manage_questions')

@login_required
def manage_exams(request):
    if not (request.user.is_staff or request.user.is_superuser): return redirect('dashboard')
    exams = Exam.objects.select_related('department').all().order_by('-created_at')
    return render(request, 'admin_panel/manage_exams.html', {'exams': exams})

@login_required
def create_exam(request):
    """Yangi imtihon yaratish"""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')

    departments = Department.objects.all()

    # Har bir bo'lim uchun savollar sonini tayyorlab yuboramiz
    department_stats = []
    for dept in departments:
        department_stats.append({
            'id': dept.id,
            'name': dept.name,
            'count': QuestionBank.objects.filter(department=dept).count()
        })

    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            department_id = request.POST.get('department')
            exam_date = request.POST.get('exam_date')
            exam_start_time = request.POST.get('exam_start_time')
            exam_end_time = request.POST.get('exam_end_time')
            duration_minutes = request.POST.get('duration_minutes')
            total_questions = request.POST.get('total_questions')
            passing_score = request.POST.get('passing_score')

            if not all([title, department_id, exam_date, exam_start_time, exam_end_time, duration_minutes, total_questions, passing_score]):
                messages.error(request, "Barcha majburiy maydonlarni to'ldiring!")
                return redirect('create_exam')

            department = Department.objects.filter(id=department_id).first()
            if not department:
                messages.error(request, "Bo'lim topilmadi!")
                return redirect('create_exam')

            available_questions_count = QuestionBank.objects.filter(department=department).count()
            if int(total_questions) > available_questions_count:
                messages.error(
                    request,
                    f"Bu bo'limda faqat {available_questions_count} ta savol bor. "
                    f"Siz esa {total_questions} ta savol kiritdingiz."
                )
                return redirect('create_exam')

            if int(passing_score) < 1 or int(passing_score) > 100:
                messages.error(request, "O'tish bali 1 dan 100 gacha bo'lishi kerak!")
                return redirect('create_exam')

            exam = Exam.objects.create(
                title=title,
                department=department,
                exam_date=exam_date,
                exam_start_time=exam_start_time,
                exam_end_time=exam_end_time,
                duration_minutes=int(duration_minutes),
                total_questions=int(total_questions),
                passing_score=int(passing_score),
                created_by=request.user,
            )

            messages.success(request, f'"{exam.title}" imtihoni muvaffaqiyatli yaratildi!')
            return redirect('manage_exams')

        except Exception as e:
            print("\n\n======== IMTIHON YARATISHDA XATOLIK ========")
            print(f"SABAB: {str(e)}")
            print("============================================\n\n")
            messages.error(request, f"Xatolik yuz berdi: {str(e)}")
            return redirect('create_exam')

    context = {
        'departments': departments,
        'department_stats': department_stats,
    }
    return render(request, 'admin_panel/create_exam.html', context)
@login_required
def edit_exam(request, pk):
    """Imtihonni tahrirlash"""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')

    exam = get_object_or_404(Exam, pk=pk)
    departments = Department.objects.all()

    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            department_id = request.POST.get('department')
            exam_date = request.POST.get('exam_date')
            exam_start_time = request.POST.get('exam_start_time')
            exam_end_time = request.POST.get('exam_end_time')
            duration_minutes = request.POST.get('duration_minutes')
            total_questions = request.POST.get('total_questions')
            passing_score = request.POST.get('passing_score')
            is_active = request.POST.get('is_active') == 'on'

            if not all([title, department_id, exam_date, exam_start_time, exam_end_time, duration_minutes, total_questions, passing_score]):
                messages.error(request, "Barcha majburiy maydonlarni to'ldiring!")
                return redirect('edit_exam', pk=exam.pk)

            department = Department.objects.filter(id=department_id).first()
            if not department:
                messages.error(request, "Bo'lim topilmadi!")
                return redirect('edit_exam', pk=exam.pk)

            available_questions_count = QuestionBank.objects.filter(department=department).count()
            if int(total_questions) > available_questions_count:
                messages.error(
                    request,
                    f"Bu bo'limda faqat {available_questions_count} ta savol bor. "
                    f"Siz esa {total_questions} ta savol kiritdingiz."
                )
                return redirect('edit_exam', pk=exam.pk)

            if int(passing_score) < 1 or int(passing_score) > 100:
                messages.error(request, "O'tish bali 1 dan 100 gacha bo'lishi kerak!")
                return redirect('edit_exam', pk=exam.pk)

            exam.title = title
            exam.department = department
            exam.exam_date = exam_date
            exam.exam_start_time = exam_start_time
            exam.exam_end_time = exam_end_time
            exam.duration_minutes = int(duration_minutes)
            exam.total_questions = int(total_questions)
            exam.passing_score = int(passing_score)
            exam.is_active = is_active
            exam.save()

            messages.success(request, "Imtihon muvaffaqiyatli yangilandi!")
            return redirect('manage_exams')

        except Exception as e:
            messages.error(request, f"Xatolik yuz berdi: {str(e)}")
            return redirect('edit_exam', pk=exam.pk)

    context = {
        'exam': exam,
        'departments': departments,
    }
    return render(request, 'admin_panel/edit_exam.html', context)


@login_required
def delete_exam(request, pk):
    """Imtihonni o'chirish"""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')

    exam = get_object_or_404(Exam, pk=pk)
    exam.delete()
    messages.success(request, "Imtihon o'chirildi!")
    return redirect('manage_exams')

@login_required
def manage_certificates(request):
    if not (request.user.is_staff or request.user.is_superuser): return redirect('dashboard')
    templates = CertificateTemplate.objects.all()
    certificates = Certificate.objects.select_related('employee', 'exam_result__exam').all()
    return render(request, 'admin_panel/manage_certificates.html', {'templates': templates, 'certificates': certificates})

@login_required
def upload_cert_template(request):
    """Sertifikat shablonini yuklash"""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')

    if request.method == 'POST':
        CertificateTemplate.objects.update(is_active=False)

        CertificateTemplate.objects.create(
            name=request.POST.get('name'),
            background_image=request.FILES.get('background_image'),
            name_x=int(request.POST.get('name_x', 400)),
            name_y=int(request.POST.get('name_y', 300)),
            name_font_size=int(request.POST.get('name_font_size', 24)),
            date_x=int(request.POST.get('date_x', 400)),
            date_y=int(request.POST.get('date_y', 450)),
            is_active=True,
        )
        messages.success(request, 'Sertifikat shabloni yuklandi va faol holatga o‘tkazildi!')
        return redirect('manage_certificates')

    return render(request, 'admin_panel/upload_cert_template.html')

@login_required
def employee_announcements(request):
    announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'employee/announcements.html', {'announcements': announcements})

@login_required
def employee_rules(request):
    rules = RuleDocument.objects.all().order_by('-uploaded_at')
    return render(request, 'employee/rules.html', {'rules': rules})

@login_required
def employee_exams(request):
    """Xodimlar uchun imtihonlar ro'yxati"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Profil topilmadi!')
        return redirect('dashboard')

    exams = Exam.objects.filter(
        department=employee.department,
        is_active=True
    ).order_by('exam_date', 'exam_start_time')

    exam_data = []
    for exam in exams:
        result = ExamResult.objects.filter(exam=exam, employee=employee).first()
        status, start_dt, end_dt = get_exam_status(exam)

        exam_data.append({
            'exam': exam,
            'result': result,
            'status': status,
            'start_dt': start_dt,
            'end_dt': end_dt,
            'can_take': result is None and status == 'available',
        })

    past_results = ExamResult.objects.filter(
        employee=employee
    ).order_by('-started_at')

    context = {
        'exam_data': exam_data,
        'past_results': past_results,
        'employee': employee,
    }
    return render(request, 'employee/exams.html', context)

@login_required
def start_exam(request, pk):
    """Imtihonni boshlash"""
    exam = get_object_or_404(Exam, pk=pk)

    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return redirect('dashboard')

    if ExamResult.objects.filter(exam=exam, employee=employee).exists():
        messages.warning(request, 'Siz bu imtihonni allaqachon topshirgansiz!')
        return redirect('employee_exams')

    if exam.department != employee.department:
        messages.error(request, 'Bu imtihon sizning bo‘limingizga tegishli emas!')
        return redirect('employee_exams')

    status, start_dt, end_dt = get_exam_status(exam)

    if status == 'not_started':
        messages.warning(
            request,
            f"Imtihon hali boshlanmagan. Boshlanish vaqti: {start_dt.strftime('%d.%m.%Y %H:%M')}"
        )
        return redirect('employee_exams')

    if status == 'ended':
        messages.error(request, "Bu imtihon vaqti tugagan!")
        return redirect('employee_exams')

    available_questions = QuestionBank.objects.filter(department=exam.department)
    if available_questions.count() < exam.total_questions:
        messages.error(request, 'Savollar bazasida yetarli savol yo‘q!')
        return redirect('employee_exams')

    questions = list(available_questions.order_by('?')[:exam.total_questions])

    questions_data = []
    for i, q in enumerate(questions, 1):
        questions_data.append({
            'id': q.id,
            'number': i,
            'text': q.text,
            'option_a': q.option_a,
            'option_b': q.option_b,
            'option_c': q.option_c,
            'option_d': q.option_d,
        })

    result = ExamResult.objects.create(
        exam=exam,
        employee=employee,
        total_questions=exam.total_questions,
        questions_data={'questions': questions_data},
        user_answers={},
    )

    now = timezone.localtime()
    remaining_seconds_until_end = int((end_dt - now).total_seconds())
    duration_seconds = min(exam.duration_minutes * 60, remaining_seconds_until_end)

    if duration_seconds <= 0:
        messages.error(request, "Imtihon vaqti tugagan!")
        return redirect('employee_exams')

    context = {
        'exam': exam,
        'result': result,
        'questions': questions_data,
        'duration_seconds': duration_seconds,
    }
    return render(request, 'employee/take_exam.html', context)

@login_required
def submit_exam(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    result = get_object_or_404(ExamResult, exam=exam, employee__user=request.user)
    user_answers = {key.replace('question_', ''): val for key, val in request.POST.items() if key.startswith('question_')}
    result.user_answers = user_answers
    correct = sum(1 for q in result.questions_data.get('questions', []) if str(q['id']) in user_answers and user_answers[str(q['id'])].upper() == QuestionBank.objects.filter(id=q['id']).first().correct_answer)
    result.correct_answers, result.wrong_answers = correct, result.total_questions - correct
    result.score = round((correct / result.total_questions) * 100, 1) if result.total_questions > 0 else 0
    result.result_status, result.finished_at = 'passed' if result.score >= exam.passing_score else 'failed', timezone.now()
    result.save()
    if result.result_status == 'passed': generate_certificate(result)
    return redirect('exam_result', pk=exam.pk)

@login_required
def exam_result(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    result = get_object_or_404(ExamResult, exam=exam, employee__user=request.user)
    detailed = []
    for q in result.questions_data.get('questions', []):
        correct_ans = QuestionBank.objects.filter(id=q['id']).first().correct_answer if QuestionBank.objects.filter(id=q['id']).exists() else '?'
        detailed.append({'number': q['number'], 'text': q['text'], 'options': {'A': q['option_a'], 'B': q['option_b'], 'C': q['option_c'], 'D': q['option_d']}, 'user_answer': result.user_answers.get(str(q['id']), '-'), 'correct_answer': correct_ans, 'is_correct': result.user_answers.get(str(q['id']), '').upper() == correct_ans})
    return render(request, 'employee/exam_result.html', {'exam': exam, 'result': result, 'detailed_results': detailed})

def generate_certificate(exam_result, force=False):
    """Imtihondan o'tgan xodim uchun chiroyli sertifikat yaratish"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.colors import HexColor, white, black
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from django.core.files.base import ContentFile
    import uuid
    import os

    employee = exam_result.employee
    exam = exam_result.exam

    # Agar eski sertifikat bo'lsa va force=True bo'lsa, o'chirib tashlaymiz
    existing_certificate = Certificate.objects.filter(exam_result=exam_result).first()
    if existing_certificate and not force:
        return existing_certificate

    if existing_certificate and force:
        if existing_certificate.certificate_file:
            existing_certificate.certificate_file.delete(save=False)
        existing_certificate.delete()

    cert_number = f"OC-{exam.id}-{employee.id}-{uuid.uuid4().hex[:6].upper()}"

    # PDF o'lchami: Landscape A4
    width, height = landscape(A4)  # 842 x 595

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(A4))

    # === FON RASMNI CHIZISH ===
    template = CertificateTemplate.objects.filter(is_active=True).order_by('-id').first()

    if template and template.background_image:
        bg_path = template.background_image.path
        if os.path.exists(bg_path):
            # Butun sahifani fon rasmdan to'ldirish
            p.drawImage(bg_path, 0, 0, width=width, height=height, preserveAspectRatio=True, mask='auto')

    # === MATNLARNI CHIZISH ===
    # Sertifikat markaziy joylashuv nuqtalari
    center_x = width / 2

    # 1. YUQORI QISM: Sana (kichik, yuqorida o'ng yoki chap tomonda)
    p.setFillColor(HexColor("#5a4a3a"))  # Qoraygan oltin/qaymoq rang
    p.setFont("Helvetica", 10)
    p.drawCentredString(center_x, height - 55, timezone.localtime().strftime('%d.%m.%Y'))

    # 2. SERTIFIKAT SARlavhasi (agar fonda yo'q bo'lsa, biz chizamiz)
    # Agar shablon o'zida "Certificate" yozuvi bo'lsa, bu qismini # comment qilish mumkin
    # p.setFillColor(HexColor("#1a1d2e"))  # To'q ko'k
    # p.setFont("Times-Bold", 42)
    # p.drawCentredString(center_x, height - 110, "SERTIFIKAT")

    # 3. "Topshiriladi" matni
    p.setFillColor(HexColor("#5a4a3a"))
    p.setFont("Helvetica-Oblique", 13)
    p.drawCentredString(center_x, height - 155, "Ushbu sertifikat quyidagi shaxsga topshiriladi")

    # 4. XODIM ISMI (ENG KATTA, MARKAZDA)
    # Shablonning markaziy bo'sh qismiga joylashadi
    p.setFillColor(HexColor("#1a1d2e"))  # To'q ko'k-qora
    p.setFont("Helvetica-Bold", 32)
    full_name = f"{employee.first_name} {employee.last_name}"
    p.drawCentredString(center_x, height - 220, full_name)

    # 5. CHIZIQ (ism ostida)
    p.setStrokeColor(HexColor("#D4A85A"))  # Oltin rang
    p.setLineWidth(2)
    line_width = 350
    p.line(center_x - line_width/2, height - 235, center_x + line_width/2, height - 235)

    # 6. BO'LIM NOMI
    p.setFillColor(HexColor("#2EB5A8"))  # Feruza
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(center_x, height - 265, f"Bo'lim: {employee.department.name if employee.department else '---'}")

    # 7. IMTIHON NOMI
    p.setFillColor(HexColor("#5a4a3a"))
    p.setFont("Helvetica", 13)
    p.drawCentredString(center_x, height - 290, f"Imtihon: {exam.title}")

    # 8. NATIJA (katta va ko'zga tegishli)
    p.setFillColor(HexColor("#1a1d2e"))
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(center_x, height - 325, f"Natija: {exam_result.score}%")

    # 9. O'TISH / O'TMASLIK holati
    if exam_result.result_status == 'passed':
        status_text = "Imtihondan muvaffaqiyatli o'tdi"
        status_color = HexColor("#1cc88a")  # Yashil
    else:
        status_text = "Imtihon topshirildi"
        status_color = HexColor("#5a4a3a")

    p.setFillColor(status_color)
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(center_x, height - 355, status_text)

    # 10. PASTKI QISM: Sertifikat raqami
    # Ekranning eng pastida, markazda
    p.setFillColor(HexColor("#7a869a"))  # Kulrang
    p.setFont("Helvetica", 9)
    p.drawCentredString(center_x, 30, f"Sertifikat raqami: {cert_number}  |  Berilgan sana: {timezone.localtime().strftime('%d.%m.%Y')}")

    # === PDF NI YAKUNLASH ===
    p.showPage()
    p.save()
    buffer.seek(0)

    # === BAZAGA SAQLASH ===
    cert = Certificate(
        exam_result=exam_result,
        employee=employee,
        certificate_number=cert_number,
    )
    cert.certificate_file.save(
        f"certificate_{cert_number}.pdf",
        ContentFile(buffer.getvalue())
    )
    cert.save()

    return cert

@login_required
def employee_certificates(request):
    try: employee = Employee.objects.get(user=request.user)
    except: return redirect('dashboard')
    return render(request, 'employee/certificates.html', {'certificates': Certificate.objects.filter(employee=employee).order_by('-issued_date')})

@login_required
def download_certificate(request, pk):
    cert = get_object_or_404(Certificate, pk=pk, employee__user=request.user)
    if cert.certificate_file: return FileResponse(cert.certificate_file.open('rb'), as_attachment=True, filename=f"sertifikat_{cert.certificate_number}.pdf")
    return redirect('employee_certificates')


# =====================================================
# SAVOLLAR BOSHQARUVI (Qo'lda yaratish)
# =====================================================

@login_required
def manage_questions(request):
    """Savollar ro'yxati va boshqaruvi"""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')
    
    questions = QuestionBank.objects.select_related('department').all().order_by('-created_at')
    departments = Department.objects.all()
    
    # Filter
    dept_filter = request.GET.get('department')
    if dept_filter:
        questions = questions.filter(department_id=dept_filter)
    
    # Statistika
    stats = {}
    for dept in departments:
        stats[dept.name] = QuestionBank.objects.filter(department=dept).count()
    
    context = {
        'questions': questions,
        'departments': departments,
        'selected_dept': dept_filter,
        'stats': stats,
        'total': QuestionBank.objects.count(),
    }
    return render(request, 'admin_panel/manage_questions.html', context)


@login_required
def create_question(request):
    """Yangi savol qo'lda yaratish"""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')
    
    departments = Department.objects.all()
    
    if request.method == 'POST':
        try:
            QuestionBank.objects.create(
                department_id=request.POST.get('department'),
                text=request.POST.get('text'),
                option_a=request.POST.get('option_a'),
                option_b=request.POST.get('option_b'),
                option_c=request.POST.get('option_c'),
                option_d=request.POST.get('option_d'),
                correct_answer=request.POST.get('correct_answer'),
            )
            messages.success(request, 'Savol muvaffaqiyatli qo\'shildi!')
            
            if request.POST.get('save_and_add'):
                return redirect('create_question')
            return redirect('manage_questions')
        except Exception as e:
            messages.error(request, f'Xatolik: {str(e)}')
    
    return render(request, 'admin_panel/create_question.html', {'departments': departments})


@login_required
def edit_question(request, pk):
    """Savolni tahrirlash"""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')
    
    question = get_object_or_404(QuestionBank, pk=pk)
    departments = Department.objects.all()
    
    if request.method == 'POST':
        question.department_id = request.POST.get('department')
        question.text = request.POST.get('text')
        question.option_a = request.POST.get('option_a')
        question.option_b = request.POST.get('option_b')
        question.option_c = request.POST.get('option_c')
        question.option_d = request.POST.get('option_d')
        question.correct_answer = request.POST.get('correct_answer')
        question.save()
        messages.success(request, 'Savol yangilandi!')
        return redirect('manage_questions')
    
    return render(request, 'admin_panel/edit_question.html', {'question': question, 'departments': departments})

@login_required
def delete_question(request, pk):
    """Savolni o'chirish"""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')
    
    question = get_object_or_404(QuestionBank, pk=pk)
    question.delete()
    messages.success(request, 'Savol o\'chirildi.')
    return redirect('manage_questions')
    
def get_exam_window(exam):
    tz = timezone.get_current_timezone()

    start_dt = datetime.combine(exam.exam_date, exam.exam_start_time)
    end_dt = datetime.combine(exam.exam_date, exam.exam_end_time)

    if timezone.is_naive(start_dt):
        start_dt = timezone.make_aware(start_dt, tz)
    if timezone.is_naive(end_dt):
        end_dt = timezone.make_aware(end_dt, tz)

    return start_dt, end_dt

def get_exam_status(exam):
    now = timezone.localtime()
    start_dt, end_dt = get_exam_window(exam)

    if now < start_dt:
        return 'not_started', start_dt, end_dt
    elif now > end_dt:
        return 'ended', start_dt, end_dt
    else:
        return 'available', start_dt, end_dt  
    
@login_required
def regenerate_certificate_admin(request, pk):
    """Admin sertifikatni qayta generatsiya qiladi"""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')

    certificate = get_object_or_404(Certificate, pk=pk)
    generate_certificate(certificate.exam_result, force=True)
    messages.success(request, "Sertifikat yangi dizayn asosida qayta generatsiya qilindi!")
    return redirect('manage_certificates')
@login_required
def regenerate_certificate_admin(request, pk):
    """Admin sertifikatni qayta generatsiya qiladi"""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')

    certificate = get_object_or_404(Certificate, pk=pk)
    generate_certificate(certificate.exam_result, force=True)
    messages.success(request, "✅ Sertifikat yangi dizayn asosida qayta generatsiya qilindi!")
    return redirect('manage_certificates')