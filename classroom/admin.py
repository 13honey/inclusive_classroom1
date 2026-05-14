from pathlib import Path

from django.conf import settings
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.models import User
from django.template.response import TemplateResponse
from django.urls import path

from .models import (
    Classification,
    Student,
    StudentSession,
    Subject,
    Task,
    TaskEvaluation,
    TaskRecording,
    TeacherFeedback,
    UserProfile,
)


admin.site.site_header = 'Inclusive Classroom Administration'
admin.site.site_title = 'Inclusive Classroom Admin'
admin.site.index_title = 'System Records'
admin.site.site_url = '/admin-dashboard/'


def media_library_view(request):
    media_root = Path(settings.MEDIA_ROOT)
    media_files = []

    if media_root.exists():
        for file_path in media_root.rglob('*'):
            if not file_path.is_file():
                continue
            relative_path = file_path.relative_to(media_root).as_posix()
            media_files.append({
                'name': file_path.name,
                'folder': file_path.parent.relative_to(media_root).as_posix(),
                'url': f'{settings.MEDIA_URL}{relative_path}',
                'size': file_path.stat().st_size,
                'modified': file_path.stat().st_mtime,
            })

    media_files.sort(key=lambda item: (item['folder'], item['name'].lower()))
    media_groups = []
    for media_file in media_files:
        if not media_groups or media_groups[-1]['folder'] != media_file['folder']:
            media_groups.append({
                'folder': media_file['folder'],
                'files': [],
            })
        media_groups[-1]['files'].append(media_file)

    context = {
        **admin.site.each_context(request),
        'title': 'Media Library',
        'media_files': media_files,
        'media_groups': media_groups,
    }
    return TemplateResponse(request, 'admin/media_library.html', context)


original_get_urls = admin.site.get_urls


def get_admin_urls():
    custom_urls = [
        path('media-library/', admin.site.admin_view(media_library_view), name='media_library'),
    ]
    return custom_urls + original_get_urls()


admin.site.get_urls = get_admin_urls


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0


class UserAdmin(DefaultUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    list_select_related = ('userprofile',)

    @admin.display(description='Role')
    def get_role(self, obj):
        return getattr(getattr(obj, 'userprofile', None), 'role', '-')


try:
    admin.site.unregister(User)
except NotRegistered:
    pass
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_online', 'last_seen')
    list_filter = ('role', 'is_online')
    search_fields = ('user__username', 'user__email')
    autocomplete_fields = ('user',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'assigned_teacher', 'age', 'grade_level', 'email', 'enrolled_date')
    list_filter = ('assigned_teacher', 'grade_level', 'grading_type', 'learning_level', 'progress_status', 'classifications')
    search_fields = ('name', 'user__username', 'user__email', 'email', 'lrn')
    autocomplete_fields = ('user', 'assigned_teacher', 'classifications')
    filter_horizontal = ('classifications',)


@admin.register(Classification)
class ClassificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    search_fields = ('name', 'description', 'created_by__username')
    autocomplete_fields = ('created_by', 'students')
    filter_horizontal = ('students',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'subject', 'status', 'deadline', 'created_by', 'created_at')
    list_filter = ('status', 'subject', 'created_by')
    search_fields = ('title', 'description', 'student__name', 'created_by__username')
    autocomplete_fields = ('student', 'subject', 'created_by')


@admin.register(TaskEvaluation)
class TaskEvaluationAdmin(admin.ModelAdmin):
    list_display = ('task', 'enjoyment', 'difficulty', 'effort', 'feeling', 'participation', 'submitted_at')
    list_filter = ('difficulty', 'effort', 'feeling', 'participation', 'submitted_at')
    search_fields = ('task__title', 'task__student__name')
    autocomplete_fields = ('task',)


@admin.register(TaskRecording)
class TaskRecordingAdmin(admin.ModelAdmin):
    list_display = ('task', 'student', 'subject', 'recorded_at')
    list_filter = ('subject', 'recorded_at')
    search_fields = ('task__title', 'student__name')
    autocomplete_fields = ('task', 'student', 'subject')


@admin.register(TeacherFeedback)
class TeacherFeedbackAdmin(admin.ModelAdmin):
    list_display = ('student', 'teacher', 'date')
    list_filter = ('teacher', 'date')
    search_fields = ('student__name', 'teacher__username', 'observation', 'recommendation')
    autocomplete_fields = ('student', 'teacher')


@admin.register(StudentSession)
class StudentSessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'login_time', 'logout_time', 'duration')
    list_filter = ('login_time', 'logout_time')
    search_fields = ('student__name',)
    autocomplete_fields = ('student',)
