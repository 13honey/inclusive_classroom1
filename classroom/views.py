from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import FileResponse, JsonResponse
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from .models import (
    Student, UserProfile, Task,
    TeacherFeedback, StudentSession, TaskEvaluation, Subject,
    TaskRecording,
)
from .forms import (
    StudentForm,
)
from .middleware import close_stale_sessions


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            try:
                profile = UserProfile.objects.get(user=user)
                if profile.role == 'admin':
                    return redirect('admin_dashboard')
                elif profile.role == 'teacher':
                    return redirect('dashboard')
                elif profile.role == 'student':
                    return redirect('student_dashboard')
            except UserProfile.DoesNotExist:
                messages.error(request, "No role assigned to this user.")
                return redirect('login')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'classroom/login.html')


def user_logout(request):
    logout(request)
    return redirect('login')


def _get_role(request):
    try:
        return UserProfile.objects.get(user=request.user).role
    except UserProfile.DoesNotExist:
        return None


def _teacher_users():
    return User.objects.filter(userprofile__role='teacher').order_by('username')


def _can_manage_classroom(request):
    return _get_role(request) == 'teacher'


def _manages_all_students(user):
    return False


def _default_teacher():
    return _teacher_users().first()


def _teacher_students(teacher):
    if _manages_all_students(teacher):
        return Student.objects.all()
    return Student.objects.filter(assigned_teacher=teacher)


def _teacher_tasks(teacher):
    if _manages_all_students(teacher):
        return Task.objects.all()
    return Task.objects.filter(student__assigned_teacher=teacher)


def _ensure_student_record(user, name=None, age=None, email=None, assigned_teacher=None, force_assign=False):
    student, created = Student.objects.get_or_create(
        user=user,
        defaults={
            'assigned_teacher': assigned_teacher or _default_teacher(),
            'name': name or user.get_full_name() or user.username,
            'age': age if age is not None else 0,
            'email': email or user.email or None,
        },
    )
    if assigned_teacher and (student.assigned_teacher is None or force_assign):
        student.assigned_teacher = assigned_teacher
        student.save(update_fields=['assigned_teacher'])
    return student, created


def _sync_student_user_profiles(default_teacher=None):
    for profile in UserProfile.objects.filter(role='student').select_related('user'):
        _ensure_student_record(profile.user, assigned_teacher=default_teacher or _default_teacher())


@login_required(login_url='/login/')
def dashboard(request):
    if not _can_manage_classroom(request):
        return redirect('login')

    _sync_student_user_profiles(default_teacher=request.user)

    if request.method == 'POST':
        form         = StudentForm(request.POST, request.FILES)
        username     = request.POST.get('username', '').strip()
        password     = request.POST.get('password', '')
        grading_type = request.POST.get('grading_type', 'ungraded')

        if not username or not password:
            messages.error(request, "Username and password are required.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "That username is already taken.")
        elif form.is_valid():
            email = request.POST.get('email', '').strip()
            user  = User.objects.create_user(username=username, email=email, password=password)
            UserProfile.objects.create(user=user, role='student')
            student = form.save(commit=False)
            student.user             = user
            student.assigned_teacher = request.user
            student.grading_type     = grading_type
            student.save()
            form.save_m2m()
            messages.success(request, f"Student '{student.name}' added successfully!")
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Field '{field}': {error}")
    else:
        form = StudentForm()

    now              = timezone.now()
    teacher_students = _teacher_students(request.user)
    all_tasks        = _teacher_tasks(request.user)
    total_completed  = all_tasks.filter(status='completed').count()
    total_pending    = all_tasks.exclude(status='completed').filter(deadline__gte=now).count()
    total_overdue    = all_tasks.exclude(status='completed').filter(deadline__lt=now).count()
    recent_tasks     = all_tasks.select_related('student').order_by('-created_at')[:6]
    total_subjects   = Subject.objects.filter(created_by=request.user).count()

    student_progress = []
    for student in teacher_students:
        tasks = Task.objects.filter(student=student)
        total = tasks.count()
        done  = tasks.filter(status='completed').count()
        pct   = round((done / total) * 100) if total > 0 else 0
        student_progress.append({'student': student, 'done': done, 'total': total, 'pct': pct})

    online_profiles = UserProfile.objects.filter(role='student', is_online=True)
    if not _manages_all_students(request.user):
        online_profiles = online_profiles.filter(user__student__assigned_teacher=request.user)
    online_count = online_profiles.count()

    return render(request, 'classroom/dashboard.html', {
        'total_students':   teacher_students.count(),
        'total_completed':  total_completed,
        'total_pending':    total_pending,
        'total_overdue':    total_overdue,
        'recent_tasks':     recent_tasks,
        'student_progress': student_progress,
        'now':              now,
        'form':             form,
        'online_count':     online_count,
        'total_subjects':   total_subjects,
    })


@login_required(login_url='/login/')
def student_monitoring(request):
    if not _can_manage_classroom(request):
        return redirect('login')

    close_stale_sessions()

    open_session_student_ids = list(StudentSession.objects.filter(
        logout_time__isnull=True
    ).values_list('student_id', flat=True))

    online_profiles = UserProfile.objects.filter(
        role='student', is_online=True
    ).select_related('user')

    online_students = []
    for profile in online_profiles:
        try:
            student = Student.objects.get(user=profile.user)
            if not _manages_all_students(request.user) and student.assigned_teacher != request.user:
                continue
            if student.id not in open_session_student_ids:
                profile.is_online = False
                profile.save(update_fields=['is_online'])
                continue
            session = StudentSession.objects.filter(
                student=student, logout_time__isnull=True
            ).order_by('-login_time').first()
            online_students.append({
                'student':    student,
                'profile':    profile,
                'login_time': session.login_time if session else profile.last_seen,
            })
        except Student.DoesNotExist:
            pass

    search_filter = request.GET.get('q', '').strip()
    date_filter   = request.GET.get('date', '').strip()
    sessions = StudentSession.objects.select_related('student')
    if not _manages_all_students(request.user):
        sessions = sessions.filter(student__assigned_teacher=request.user)
    if search_filter:
        sessions = sessions.filter(student__name__icontains=search_filter)
    if date_filter:
        sessions = sessions.filter(login_time__date=date_filter)

    return render(request, 'classroom/student_monitoring.html', {
        'online_students': online_students,
        'online_count':    len(online_students),
        'total_students':  _teacher_students(request.user).count(),
        'sessions':        sessions,
        'date_filter':     date_filter,
        'search_filter':   search_filter,
        'now':             timezone.now(),
    })


@login_required(login_url='/login/')
def monitoring_status_api(request):
    if not _can_manage_classroom(request):
        return JsonResponse({'error': 'forbidden'}, status=403)

    close_stale_sessions()

    open_session_student_ids = list(StudentSession.objects.filter(
        logout_time__isnull=True
    ).values_list('student_id', flat=True))

    online_profiles = UserProfile.objects.filter(
        role='student', is_online=True
    ).select_related('user')

    data = []
    for profile in online_profiles:
        try:
            student = Student.objects.get(user=profile.user)
            if not _manages_all_students(request.user) and student.assigned_teacher != request.user:
                continue
            if student.id not in open_session_student_ids:
                profile.is_online = False
                profile.save(update_fields=['is_online'])
                continue
            session = StudentSession.objects.filter(
                student=student, logout_time__isnull=True
            ).order_by('-login_time').first()
            data.append({
                'id':         student.id,
                'name':       student.name,
                'login_time': session.login_time.strftime('%I:%M %p') if session else '—',
                'avatar':     student.profile_picture.url if student.profile_picture else None,
            })
        except Student.DoesNotExist:
            pass

    return JsonResponse({
        'online_count':    len(data),
        'total_students':  _teacher_students(request.user).count(),
        'online_students': data,
    })


@login_required(login_url='/login/')
def student_heartbeat(request):
    if _get_role(request) != 'student':
        return JsonResponse({'ok': False, 'role': _get_role(request)})

    now = timezone.now()
    profile = get_object_or_404(UserProfile, user=request.user, role='student')
    profile.is_online = True
    profile.last_seen = now
    profile.save(update_fields=['is_online', 'last_seen'])

    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'student_not_found'}, status=404)

    page_student_id = request.GET.get('student')
    if page_student_id and str(student.id) != page_student_id:
        return JsonResponse({'ok': False, 'error': 'student_session_changed'})

    has_open_session = StudentSession.objects.filter(
        student=student,
        logout_time__isnull=True,
    ).exists()
    if not has_open_session:
        StudentSession.objects.create(student=student, login_time=now)

    return JsonResponse({'ok': True})


@login_required(login_url='/login/')
def student_list(request):
    if not _can_manage_classroom(request):
        return redirect('login')
    _sync_student_user_profiles(default_teacher=request.user)
    query    = request.GET.get('q', '').strip()
    students = _teacher_students(request.user).order_by('name')
    if query:
        students = students.filter(Q(name__icontains=query) | Q(lrn__icontains=query))
    return render(request, 'classroom/student_list.html', {'students': students, 'query': query})


@login_required(login_url='/login/')
def add_student(request):
    if not _can_manage_classroom(request):
        return redirect('login')
    if request.method == 'POST':
        form             = StudentForm(request.POST, request.FILES)
        username         = request.POST.get('username', '').strip()
        password         = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        grading_type     = request.POST.get('grading_type', 'ungraded')
        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, 'classroom/add_student.html', {'form': form})
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'classroom/add_student.html', {'form': form})
        if User.objects.filter(username=username).exists():
            messages.error(request, "That username is already taken.")
            return render(request, 'classroom/add_student.html', {'form': form})
        if form.is_valid():
            email = request.POST.get('email', '').strip()
            try:
                with transaction.atomic():
                    user  = User.objects.create_user(username=username, email=email, password=password)
                    UserProfile.objects.create(user=user, role='student')
                    student = form.save(commit=False)
                    student.user             = user
                    student.assigned_teacher = request.user
                    student.grading_type     = grading_type
                    student.save()
                    form.save_m2m()
            except IntegrityError:
                messages.error(request, "That username or LRN is already in use. Please choose unique values.")
                return render(request, 'classroom/add_student.html', {'form': form})
            messages.success(request, f"Student '{student.name}' added successfully!")
            return redirect('student_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Field '{field}': {error}")
    else:
        form = StudentForm()
    return render(request, 'classroom/add_student.html', {'form': form})


@login_required(login_url='/login/')
def student_detail(request, id):
    if not _can_manage_classroom(request):
        return redirect('login')
    student = get_object_or_404(_teacher_students(request.user), id=id)
    tasks   = Task.objects.filter(student=student).order_by('-created_at')
    if request.method == 'POST':
        title       = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        deadline    = request.POST.get('deadline')
        video_url   = request.POST.get('video_url', '').strip()
        attachment  = request.FILES.get('attachment')
        video_file  = request.FILES.get('video_file')
        if not title:
            messages.error(request, "Task title is required.")
        elif not deadline:
            messages.error(request, "Deadline is required.")
        else:
            Task.objects.create(
                student=student, title=title, description=description or None,
                deadline=deadline, video_url=video_url or None,
                attachment=attachment, video_file=video_file,
                created_by=request.user,
            )
            messages.success(request, "Task added successfully!")
            return redirect('student_detail', id=id)
    return render(request, 'classroom/student_detail.html', {
        'student': student, 'tasks': tasks, 'now': timezone.now(),
    })


@login_required(login_url='/login/')
def edit_student(request, id):
    if not _can_manage_classroom(request):
        return redirect('login')
    student = get_object_or_404(_teacher_students(request.user), id=id)
    if request.method == 'POST':
        form         = StudentForm(request.POST, request.FILES, instance=student)
        grading_type = request.POST.get('grading_type', 'ungraded')
        if form.is_valid():
            s = form.save(commit=False)
            s.grading_type           = grading_type
            s.learning_level         = request.POST.get('learning_level') or None
            s.progress_status        = request.POST.get('progress_status') or None
            s.learning_goals         = request.POST.get('learning_goals', '').strip() or None
            s.skills_focus           = request.POST.get('skills_focus', '').strip() or None
            s.progress_communication = int(request.POST.get('progress_communication', 0) or 0)
            s.progress_motor         = int(request.POST.get('progress_motor', 0) or 0)
            s.progress_social        = int(request.POST.get('progress_social', 0) or 0)
            s.progress_selfcare      = int(request.POST.get('progress_selfcare', 0) or 0)
            s.progress_academic      = int(request.POST.get('progress_academic', 0) or 0)
            s.save()
            form.save_m2m()
            messages.success(request, "Student updated successfully!")
            return redirect('student_list')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = StudentForm(instance=student)
    return render(request, 'classroom/edit_student.html', {'form': form, 'student': student})


@login_required(login_url='/login/')
def delete_student(request, id):
    if not _can_manage_classroom(request):
        return redirect('login')
    student = get_object_or_404(_teacher_students(request.user), id=id)
    if request.method == 'POST':
        linked_user = student.user
        if linked_user:
            linked_user.delete()
        else:
            student.delete()
        messages.success(request, "Student deleted successfully!")
        return redirect('student_list')
    return render(request, 'classroom/confirm_delete.html', {'student': student})


@login_required(login_url='/login/')
def assign_task(request):
    if not _can_manage_classroom(request):
        return redirect('login')

    students         = _teacher_students(request.user).order_by('name')
    all_subjects     = Subject.objects.filter(created_by=request.user).order_by('name')
    preselect_id     = request.GET.get('student', '').strip()
    preselect_subject_id = request.GET.get('subject', '').strip()
    selected_student = None
    if preselect_id:
        selected_student = students.filter(id=preselect_id).first()

    if request.method == 'POST':
        student_ids = request.POST.getlist('student_id')
        title       = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        deadline    = request.POST.get('deadline', '').strip()
        video_url   = request.POST.get('video_url', '').strip()
        subject_id  = (request.POST.get('subject_id') or request.POST.get('subject') or '').strip()
        attachment  = request.FILES.get('attachment')
        video_file  = request.FILES.get('video_file')
        subject     = Subject.objects.filter(id=subject_id, created_by=request.user).first() if subject_id else None
        preselect_subject_id = subject_id

        if not student_ids:
            messages.error(request, "Please select at least one student.")
        elif not subject:
            messages.error(request, "Please select a subject for this task.")
        elif not title:
            messages.error(request, "Task title is required.")
        elif not deadline:
            messages.error(request, "Please set a deadline.")
        else:
            selected_students = _teacher_students(request.user).filter(id__in=student_ids)
            for student in selected_students:
                Task.objects.create(
                    student=student, title=title, description=description or None,
                    deadline=deadline, video_url=video_url or None,
                    attachment=attachment, video_file=video_file,
                    created_by=request.user, subject=subject,
                )
                if subject:
                    subject.students.add(student)
            names = ", ".join(s.name for s in selected_students)
            messages.success(request, f"Task \"{title}\" assigned to {names} successfully!")
            return redirect(request.path)

        selected_student = students.filter(id__in=student_ids).first()

    return render(request, 'classroom/assign_task.html', {
        'students':         students,
        'selected_student': selected_student,
        'subjects':         all_subjects,
        'selected_subject_id': preselect_subject_id,
    })


@login_required(login_url='/login/')
def teacher_feedback(request):
    if not _can_manage_classroom(request):
        return redirect('login')

    students         = _teacher_students(request.user).order_by('name')
    preselect_id     = request.GET.get('student', '').strip()
    selected_student = students.filter(id=preselect_id).first() if preselect_id else students.first()

    if request.method == 'POST':
        student_id     = request.POST.get('student_id', '').strip()
        observation    = request.POST.get('observation', '').strip()
        recommendation = request.POST.get('recommendation', '').strip()
        selected_student = students.filter(id=student_id).first()

        if not selected_student:
            messages.error(request, "Please select a student.")
        elif not observation:
            messages.error(request, "Feedback observation is required.")
        else:
            TeacherFeedback.objects.create(
                student=selected_student,
                teacher=request.user,
                observation=observation,
                recommendation=recommendation or None,
            )
            messages.success(request, f"Feedback saved for {selected_student.name}.")
            return redirect(f"{request.path}?student={selected_student.id}")

    feedbacks = TeacherFeedback.objects.select_related('student', 'teacher')
    if not _manages_all_students(request.user):
        feedbacks = feedbacks.filter(student__assigned_teacher=request.user)
    feedbacks = feedbacks.order_by('-date')

    return render(request, 'classroom/teacher_feedback.html', {
        'students':         students,
        'selected_student': selected_student,
        'feedbacks':        feedbacks,
    })


@login_required(login_url='/login/')
def edit_task(request, task_id):
    if not _can_manage_classroom(request):
        return redirect('login')
    task       = get_object_or_404(_teacher_tasks(request.user), id=task_id)
    student_id = task.student.id
    if request.method == 'POST':
        title       = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        deadline    = request.POST.get('deadline')
        video_url   = request.POST.get('video_url', '').strip()
        if not title:
            messages.error(request, "Task title is required.")
        elif not deadline:
            messages.error(request, "Deadline is required.")
        else:
            task.title       = title
            task.description = description or None
            task.deadline    = deadline
            task.video_url   = video_url or None
            if request.FILES.get('attachment'):
                task.attachment = request.FILES['attachment']
            if request.FILES.get('video_file'):
                task.video_file = request.FILES['video_file']
            task.save()
            messages.success(request, "Task updated successfully!")
            return redirect('student_detail', id=student_id)
    return render(request, 'classroom/edit_task.html', {'task': task, 'student': task.student})


@login_required(login_url='/login/')
def delete_task(request, task_id):
    if not _can_manage_classroom(request):
        return redirect('login')
    task       = get_object_or_404(_teacher_tasks(request.user), id=task_id)
    student_id = task.student.id
    next_url   = request.POST.get('next') or request.GET.get('next', '')
    if request.method == 'POST':
        task.delete()
        messages.success(request, "Task deleted successfully!")
        if next_url == 'task_history':
            return redirect('task_history')
        return redirect('student_detail', id=student_id)
    return render(request, 'classroom/confirm_delete_task.html', {
        'task': task,
        'student': task.student,
        'next': next_url,
    })


@login_required(login_url='/login/')
def admin_dashboard(request):
    if _get_role(request) != 'admin':
        return redirect('login')
    _sync_student_user_profiles()
    total_students  = Student.objects.count()
    total_teachers  = UserProfile.objects.filter(role='teacher').count()
    total_admins    = UserProfile.objects.filter(role='admin').count()
    total_users     = UserProfile.objects.count()
    user_profiles   = UserProfile.objects.select_related('user').all().order_by('-user__date_joined')[:5]
    return render(request, 'classroom/admin_dashboard.html', {
        'user_profiles':   user_profiles,
        'total_students':  total_students,
        'total_teachers':  total_teachers,
        'total_admins':    total_admins,
        'total_users':     total_users,
    })


@login_required(login_url='/login/')
def admin_user_list(request):
    if _get_role(request) != 'admin':
        return redirect('login')
    _sync_student_user_profiles()
    query         = request.GET.get('q', '').strip()
    role_filter   = request.GET.get('role', '').strip()
    user_profiles = UserProfile.objects.select_related('user').all().order_by('-user__date_joined')
    if query:
        user_profiles = (user_profiles.filter(user__username__icontains=query) |
                         user_profiles.filter(user__email__icontains=query)).distinct()
    if role_filter:
        user_profiles = user_profiles.filter(role=role_filter)
    return render(request, 'classroom/admin_user_list.html', {
        'user_profiles': user_profiles, 'query': query, 'role_filter': role_filter,
    })


@login_required(login_url='/login/')
def admin_add_user(request):
    if _get_role(request) != 'admin':
        return redirect('login')
    teachers       = _teacher_users()
    teacher_exists = teachers.exists()
    if not teachers.exists():
        teachers = User.objects.filter(id=request.user.id)
    default_teacher = teachers.first()
    form_data = {
        'username': '', 'email': '', 'role': 'student',
        'student_name': '', 'student_age': '',
        'assigned_teacher': str(default_teacher.id) if default_teacher else '',
    }
    if request.method == 'POST':
        username            = request.POST.get('username', '').strip()
        email               = request.POST.get('email', '').strip()
        password            = request.POST.get('password', '')
        role                = request.POST.get('role', 'student')
        student_name        = request.POST.get('student_name', '').strip()
        student_age         = request.POST.get('student_age', '').strip()
        assigned_teacher_id = request.POST.get('assigned_teacher', '').strip()
        assigned_teacher    = teachers.filter(id=assigned_teacher_id).first() if assigned_teacher_id else default_teacher
        form_data.update({
            'username': username, 'email': email, 'role': role,
            'student_name': student_name, 'student_age': student_age,
            'assigned_teacher': assigned_teacher_id,
        })
        allowed_roles = {'student'}
        if not teacher_exists:
            allowed_roles.add('teacher')

        if role == 'admin':
            messages.error(request, "Only one administrator account is allowed for this system.")
        elif role == 'teacher' and teacher_exists:
            messages.error(request, "Only one SPED teacher account is allowed for this system.")
        elif role not in allowed_roles:
            messages.error(request, "Please choose a valid role.")
        elif not username or not password:
            messages.error(request, "Username and password are required.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        elif role == 'student' and not student_name:
            messages.error(request, "Student full name is required.")
        elif role == 'student' and not student_age:
            messages.error(request, "Student age is required.")
        elif role == 'student' and not student_age.isdigit():
            messages.error(request, "Student age must be a number.")
        elif role == 'student' and not 3 <= int(student_age) <= 25:
            messages.error(request, "Student age must be between 3 and 25.")
        elif role == 'student' and assigned_teacher is None:
            messages.error(request, "Please create or keep a SPED teacher account before adding students.")
        else:
            with transaction.atomic():
                user = User.objects.create_user(username=username, email=email, password=password)
                UserProfile.objects.create(user=user, role=role)
                if role == 'student':
                    _ensure_student_record(
                        user, name=student_name, age=int(student_age),
                        email=email, assigned_teacher=assigned_teacher,
                    )
            messages.success(request, f"User '{username}' created successfully!")
            return redirect('admin_user_list')
    return render(request, 'classroom/admin_add_user.html', {
        'teachers': teachers, 'form_data': form_data, 'teacher_exists': teacher_exists,
    })


@login_required(login_url='/login/')
def admin_edit_user(request, id):
    if _get_role(request) != 'admin':
        return redirect('login')
    edit_profile   = get_object_or_404(UserProfile, id=id)
    teachers       = _teacher_users()
    if not teachers.exists():
        teachers = User.objects.filter(id=request.user.id)
    student_record = Student.objects.filter(user=edit_profile.user).first()
    other_admin_exists = UserProfile.objects.filter(role='admin').exclude(id=edit_profile.id).exists()
    other_teacher_exists = UserProfile.objects.filter(role='teacher').exclude(id=edit_profile.id).exists()
    if request.method == 'POST':
        new_username        = request.POST.get('username', '').strip()
        new_email           = request.POST.get('email', '').strip()
        new_role            = request.POST.get('role', '')
        new_password        = request.POST.get('new_password', '')
        confirm_password    = request.POST.get('confirm_password', '')
        reset_password      = request.POST.get('reset_password') == 'on'
        assigned_teacher_id = request.POST.get('assigned_teacher', '').strip()
        assigned_teacher    = teachers.filter(id=assigned_teacher_id).first() if assigned_teacher_id else _default_teacher()
        allowed_roles = {'student'}
        if edit_profile.role == 'admin' or not other_admin_exists:
            allowed_roles.add('admin')
        if edit_profile.role == 'teacher' or not other_teacher_exists:
            allowed_roles.add('teacher')

        if new_role not in allowed_roles:
            messages.error(request, "Please choose a valid role.")
            return render(request, 'classroom/admin_edit_user.html', {
                'profile': edit_profile, 'teachers': teachers, 'student_record': student_record,
                'other_admin_exists': other_admin_exists, 'other_teacher_exists': other_teacher_exists,
            })
        if User.objects.filter(username=new_username).exclude(pk=edit_profile.user.pk).exists():
            messages.error(request, "That username is already taken.")
            return render(request, 'classroom/admin_edit_user.html', {
                'profile': edit_profile, 'teachers': teachers, 'student_record': student_record,
                'other_admin_exists': other_admin_exists, 'other_teacher_exists': other_teacher_exists,
            })
        if new_role == 'admin' and other_admin_exists:
            messages.error(request, "Only one administrator account is allowed for this system.")
            return render(request, 'classroom/admin_edit_user.html', {
                'profile': edit_profile, 'teachers': teachers, 'student_record': student_record,
                'other_admin_exists': other_admin_exists, 'other_teacher_exists': other_teacher_exists,
            })
        if new_role == 'teacher' and other_teacher_exists:
            messages.error(request, "Only one SPED teacher account is allowed for this system.")
            return render(request, 'classroom/admin_edit_user.html', {
                'profile': edit_profile, 'teachers': teachers, 'student_record': student_record,
                'other_admin_exists': other_admin_exists, 'other_teacher_exists': other_teacher_exists,
            })
        if reset_password:
            if not new_password or not confirm_password:
                messages.error(request, "Please enter and confirm the new password.")
                return render(request, 'classroom/admin_edit_user.html', {
                    'profile': edit_profile, 'teachers': teachers, 'student_record': student_record,
                    'other_admin_exists': other_admin_exists, 'other_teacher_exists': other_teacher_exists,
                })
            if new_password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return render(request, 'classroom/admin_edit_user.html', {
                    'profile': edit_profile, 'teachers': teachers, 'student_record': student_record,
                    'other_admin_exists': other_admin_exists, 'other_teacher_exists': other_teacher_exists,
                })
            edit_profile.user.set_password(new_password)
        edit_profile.user.username = new_username
        edit_profile.user.email    = new_email
        edit_profile.user.save()
        edit_profile.role = new_role
        edit_profile.save()
        if new_role == 'student':
            _ensure_student_record(
                edit_profile.user, email=new_email,
                assigned_teacher=assigned_teacher, force_assign=True,
            )
        elif student_record:
            student_record.assigned_teacher = None
            student_record.save(update_fields=['assigned_teacher'])
        messages.success(request, "User updated successfully!")
        return redirect('admin_user_list')
    return render(request, 'classroom/admin_edit_user.html', {
        'profile': edit_profile, 'teachers': teachers, 'student_record': student_record,
        'other_admin_exists': other_admin_exists, 'other_teacher_exists': other_teacher_exists,
    })


@login_required(login_url='/login/')
def admin_delete_user(request, id):
    if _get_role(request) != 'admin':
        return redirect('login')
    delete_profile = get_object_or_404(UserProfile, id=id)
    if request.method == 'POST':
        user_to_delete = delete_profile.user
        with transaction.atomic():
            if delete_profile.role == 'student':
                Student.objects.filter(user=user_to_delete).delete()
            user_to_delete.delete()
        messages.success(request, "User deleted successfully!")
        return redirect('admin_user_list')
    return render(request, 'classroom/admin_confirm_delete.html', {'profile': delete_profile})


def _student_task_stats(tasks):
    task_list = list(tasks)
    total     = len(task_list)
    done      = sum(1 for t in task_list if t.status == 'completed')
    pending   = total - done
    return total, done, pending


@login_required(login_url='/login/')
def student_dashboard(request):
    if _get_role(request) != 'student':
        return redirect('login')
    student = Student.objects.filter(user=request.user).first()
    tasks   = list(Task.objects.filter(student=student).order_by('-created_at')) if student else []
    total, done, pending = _student_task_stats(tasks)
    return render(request, 'classroom/student_dashboard.html', {
        'student': student, 'total_tasks': total, 'done_tasks': done,
        'pending_tasks': pending, 'recent_tasks': tasks[:3], 'now': timezone.now(),
    })


@login_required(login_url='/login/')
def student_profile(request):
    if _get_role(request) != 'student':
        return redirect('login')
    student   = Student.objects.filter(user=request.user).first()
    tasks     = list(Task.objects.filter(student=student).order_by('-created_at')) if student else []
    total, done, pending = _student_task_stats(tasks)
    feedbacks   = TeacherFeedback.objects.filter(student=student).order_by('-date') if student else []
    skills_list = [s.strip() for s in student.skills_focus.split(',') if s.strip()] if student and student.skills_focus else []
    return render(request, 'classroom/student_profile.html', {
        'student': student, 'feedbacks': feedbacks, 'skills_list': skills_list,
        'total_tasks': total, 'done_tasks': done, 'pending_tasks': pending,
    })


@login_required(login_url='/login/')
def student_tasks(request):
    if _get_role(request) != 'student':
        return redirect('login')
    student     = Student.objects.filter(user=request.user).first()
    filter_type = request.GET.get('filter', 'all')
    eval_task_id = request.GET.get('eval')
    eval_task    = None
    if eval_task_id:
        try:
            eval_task = Task.objects.get(id=eval_task_id, student=student)
            if hasattr(eval_task, 'evaluation'):
                eval_task = None
        except Task.DoesNotExist:
            eval_task = None

    now       = timezone.now()
    all_tasks = Task.objects.filter(student=student).order_by('-created_at') if student else Task.objects.none()
    total, done, pending = _student_task_stats(list(all_tasks))
    completed_tasks = list(all_tasks.filter(status='completed')[:6]) if student else []
    pending_preview = list(all_tasks.exclude(status='completed')[:6]) if student else []

    if filter_type == 'completed':
        tasks = [t for t in all_tasks if t.status == 'completed']
    elif filter_type == 'pending':
        tasks = [t for t in all_tasks if t.status != 'completed' and t.deadline >= now]
    elif filter_type == 'overdue':
        tasks = [t for t in all_tasks if t.status != 'completed' and t.deadline < now]
    else:
        tasks = list(all_tasks)

    return render(request, 'classroom/student_tasks.html', {
        'student':       student,
        'tasks':         tasks,
        'total_tasks':   total,
        'done_tasks':    done,
        'pending_tasks': pending,
        'filter':        filter_type,
        'now':           now,
        'eval_task':     eval_task,
        'completed_tasks': completed_tasks,
        'pending_preview': pending_preview,
    })


@login_required(login_url='/login/')
def complete_task(request, task_id):
    if _get_role(request) != 'student':
        return redirect('login')
    task    = get_object_or_404(Task, id=task_id)
    student = Student.objects.filter(user=request.user).first()
    if not student or task.student != student:
        messages.error(request, "You do not have permission to complete this task.")
        return redirect('student_tasks')
    if request.method == 'POST':
        task.status       = 'completed'
        task.completed_at = timezone.now()
        recorded_video = request.FILES.get('recorded_video')
        if recorded_video:
            TaskRecording.objects.create(
                task=task,
                student=student,
                subject=task.subject,
                video_file=recorded_video,
            )
        if request.FILES.get('output_file'):
            task.output_file = request.FILES['output_file']
        task.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'ok': True,
                'task_id': task.id,
                'evaluation_url': f"{request.build_absolute_uri('/student-dashboard/tasks/')}?eval={task.id}",
            })
        return redirect(f"{request.build_absolute_uri('/student-dashboard/tasks/')}?eval={task.id}")
    return redirect('student_tasks')


@login_required(login_url='/login/')
def submit_evaluation(request, task_id):
    if _get_role(request) != 'student':
        return JsonResponse({'error': 'forbidden'}, status=403)
    task    = get_object_or_404(Task, id=task_id)
    student = Student.objects.filter(user=request.user).first()
    if not student or task.student != student:
        return JsonResponse({'error': 'not your task'}, status=403)
    if task.status != 'completed':
        return JsonResponse({'error': 'task not completed yet'}, status=400)
    if TaskEvaluation.objects.filter(task=task).exists():
        return JsonResponse({'ok': True, 'already_submitted': True})
    if request.method == 'POST':
        enjoyment     = request.POST.get('enjoyment', '')
        difficulty    = request.POST.get('difficulty', '')
        effort        = request.POST.get('effort', '')
        feeling       = request.POST.get('feeling', '')
        participation = request.POST.get('participation', '')
        required_values = [enjoyment, difficulty, effort, feeling, participation]
        if not all(required_values) or not enjoyment.isdigit():
            return JsonResponse({'error': 'all evaluation questions are required'}, status=400)
        TaskEvaluation.objects.create(
            task=task,
            enjoyment=int(enjoyment),
            difficulty=difficulty, effort=effort,
            feeling=feeling, participation=participation,
        )
        return JsonResponse({'ok': True})
    return JsonResponse({'error': 'method not allowed'}, status=405)


@login_required(login_url='/login/')
def task_history(request):
    if not _can_manage_classroom(request):
        return redirect('login')

    search_filter  = request.GET.get('q', '').strip()
    status_filter  = request.GET.get('status', '').strip()
    student_filter = request.GET.get('student', '').strip()

    now        = timezone.now()
    base_tasks = (
        _teacher_tasks(request.user)
        .select_related('student', 'subject', 'evaluation')
        .prefetch_related('recordings')
        .order_by('-created_at')
    )
    stat_tasks = base_tasks

    if search_filter:
        stat_tasks = stat_tasks.filter(
            Q(title__icontains=search_filter) | Q(student__name__icontains=search_filter)
        )
    if student_filter:
        stat_tasks = stat_tasks.filter(student__id=student_filter)

    tasks = stat_tasks
    if status_filter == 'completed':
        tasks = tasks.filter(status='completed')
    elif status_filter == 'pending':
        tasks = tasks.exclude(status='completed').filter(deadline__gte=now)
    elif status_filter == 'overdue':
        tasks = tasks.exclude(status='completed').filter(deadline__lt=now)

    students  = _teacher_students(request.user).order_by('name')
    total     = stat_tasks.count()
    completed = stat_tasks.filter(status='completed').count()
    pending   = stat_tasks.exclude(status='completed').filter(deadline__gte=now).count()
    overdue   = stat_tasks.exclude(status='completed').filter(deadline__lt=now).count()
    evaluated = TaskEvaluation.objects.filter(task__in=stat_tasks).count()
    common_effort = (
        TaskEvaluation.objects.filter(task__in=stat_tasks).exclude(effort='')
        .values('effort').annotate(total=Count('id')).order_by('-total').first()
    )
    common_feeling = (
        TaskEvaluation.objects.filter(task__in=stat_tasks).exclude(feeling='')
        .values('feeling').annotate(total=Count('id')).order_by('-total').first()
    )

    return render(request, 'classroom/task_history.html', {
        'tasks':          tasks,
        'students':       students,
        'search_filter':  search_filter,
        'status_filter':  status_filter,
        'student_filter': student_filter,
        'total':          total,
        'completed':      completed,
        'pending':        pending,
        'overdue':        overdue,
        'evaluated':      evaluated,
        'common_effort':  dict(TaskEvaluation.EFFORT_CHOICES).get(common_effort['effort']) if common_effort else 'No evaluations yet',
        'common_feeling': dict(TaskEvaluation.FEELING_CHOICES).get(common_feeling['feeling']) if common_feeling else 'No evaluations yet',
        'now':            now,
    })


# ── Subject Views ─────────────────────────────────────────────────────────────

def _recording_role(user):
    try:
        return UserProfile.objects.get(user=user).role
    except UserProfile.DoesNotExist:
        return None


def _can_view_recording(user, recording):
    role = _recording_role(user)
    if role == 'teacher':
        return _teacher_tasks(user).filter(id=recording.task_id).exists()
    if role == 'student':
        return recording.student.user_id == user.id
    return False


@login_required(login_url='/login/')
def task_recording_detail(request, recording_id):
    recording = get_object_or_404(
        TaskRecording.objects.select_related('task', 'student', 'subject'),
        id=recording_id,
    )
    if not _can_view_recording(request.user, recording):
        return redirect('login')
    back_url = request.META.get('HTTP_REFERER') or request.GET.get('next') or ''
    if not back_url or f"/recordings/{recording.id}/" in back_url:
        back_url = request.build_absolute_uri('/task-history/')
    return render(request, 'classroom/task_recording_detail.html', {
        'recording': recording,
        'back_url':  back_url,
    })


@login_required(login_url='/login/')
def task_recording_download(request, recording_id):
    recording = get_object_or_404(
        TaskRecording.objects.select_related('task', 'student'),
        id=recording_id,
    )
    if not _can_view_recording(request.user, recording):
        return redirect('login')
    filename = recording.video_file.name.split('/')[-1] or f"task-recording-{recording.id}.webm"
    return FileResponse(recording.video_file.open('rb'), as_attachment=True, filename=filename)


@login_required(login_url='/login/')
def subject_list(request):
    if not _can_manage_classroom(request):
        return redirect('login')
    subjects     = Subject.objects.filter(created_by=request.user).prefetch_related('students').order_by('name')
    all_students = _teacher_students(request.user).order_by('name')
    return render(request, 'classroom/subject_list.html', {
        'subjects':     subjects,
        'all_students': all_students,
        'now':          timezone.now(),
    })


@login_required(login_url='/login/')
def add_subject(request):
    if not _can_manage_classroom(request):
        return redirect('login')
    students = _teacher_students(request.user).order_by('name')

    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        icon        = request.POST.get('icon', '📚').strip() or '📚'
        color       = request.POST.get('color', '#2563eb').strip() or '#2563eb'
        student_ids = request.POST.getlist('student_ids')

        if not name:
            messages.error(request, "Please choose or enter a subject name.")
        elif Subject.objects.filter(created_by=request.user, name__iexact=name).exists():
            messages.error(request, f"Subject '{name}' already exists.")
        else:
            subject = Subject.objects.create(
                name=name,
                description=description or None,
                icon='📚',
                color=color,
                created_by=request.user,
            )
            subject.icon = icon
            subject.save(update_fields=['icon'])
            if student_ids:
                subject.students.set(students.filter(id__in=student_ids))
            messages.success(request, f'Subject "{name}" created successfully!')
            return redirect('subject_list')

    return render(request, 'classroom/add_subject.html', {
        'students': students,
    })


@login_required(login_url='/login/')
def edit_subject(request, id):
    if not _can_manage_classroom(request):
        return redirect('login')
    subject  = get_object_or_404(Subject, id=id, created_by=request.user)
    students = _teacher_students(request.user).order_by('name')
    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        icon        = request.POST.get('icon', '📚').strip()
        color       = request.POST.get('color', '#2563eb').strip()
        student_ids = request.POST.getlist('student_ids')
        if not name:
            messages.error(request, "Subject name is required.")
        else:
            subject.name        = name
            subject.description = description or None
            subject.icon        = icon
            subject.color       = color
            subject.save()
            subject.students.set(_teacher_students(request.user).filter(id__in=student_ids))
            messages.success(request, f"Subject \"{name}\" updated successfully!")
            return redirect('subject_list')
    return render(request, 'classroom/edit_subject.html', {
        'subject':      subject,
        'students':     students,
        'enrolled_ids': list(subject.students.values_list('id', flat=True)),
    })


@login_required(login_url='/login/')
def delete_subject(request, id):
    if not _can_manage_classroom(request):
        return redirect('login')
    subject = get_object_or_404(Subject, id=id, created_by=request.user)
    if request.method == 'POST':
        name = subject.name
        subject.delete()
        messages.success(request, f'Subject "{name}" deleted.')
        return redirect('subject_list')
    return redirect('subject_list')


@login_required(login_url='/login/')
def enroll_student(request, id):
    if not _can_manage_classroom(request):
        return JsonResponse({'error': 'forbidden'}, status=403)
    subject    = get_object_or_404(Subject, id=id, created_by=request.user)
    student_id = request.POST.get('student_id')
    action     = request.POST.get('action')
    student    = get_object_or_404(_teacher_students(request.user), id=student_id)
    if action == 'add':
        subject.students.add(student)
    elif action == 'remove':
        subject.students.remove(student)
    return JsonResponse({'ok': True})

@login_required(login_url='/login/')
def student_subject_list(request):
    if _get_role(request) != 'student':
        return redirect('login')
    student  = Student.objects.filter(user=request.user).first()
    subjects = Subject.objects.filter(Q(students=student) | Q(tasks__student=student)).distinct() if student else Subject.objects.none()
    return render(request, 'classroom/student_subject_list.html', {
        'student':  student,
        'subjects': subjects,
    })


@login_required(login_url='/login/')
def student_subject_detail(request, id):
    if _get_role(request) != 'student':
        return redirect('login')
    student = Student.objects.filter(user=request.user).first()
    subject = get_object_or_404(Subject, id=id)

    if not student:
        messages.error(request, "Student profile was not found.")
        return redirect('student_dashboard')

    if not subject.students.filter(id=student.id).exists() and not Task.objects.filter(student=student, subject=subject).exists():
        messages.error(request, "You are not enrolled in this subject.")
        return redirect('student_dashboard')

    eval_task_id = request.GET.get('eval')
    eval_task    = None
    if eval_task_id:
        try:
            eval_task = Task.objects.get(id=eval_task_id, student=student, subject=subject)
            if hasattr(eval_task, 'evaluation'):
                eval_task = None
        except Task.DoesNotExist:
            eval_task = None

    now   = timezone.now()
    tasks = Task.objects.filter(student=student, subject=subject).order_by('-created_at')
    total_tasks   = tasks.count()
    done_tasks    = tasks.filter(status='completed').count()
    pending_tasks = total_tasks - done_tasks

    return render(request, 'classroom/student_subject_detail.html', {
        'student':       student,
        'subject':       subject,
        'tasks':         tasks,
        'now':           now,
        'total_tasks':   total_tasks,
        'done_tasks':    done_tasks,
        'pending_tasks': pending_tasks,
        'eval_task':     eval_task,
    })
