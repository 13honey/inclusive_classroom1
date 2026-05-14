from django.urls import path
from . import views

urlpatterns = [
    path('login/',  views.user_login,  name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Teacher dashboard
    path('',                        views.dashboard,      name='dashboard'),

    # Student management
    path('students/',               views.student_list,   name='student_list'),
    path('add-student/',            views.add_student,    name='add_student'),
    path('student/<int:id>/',       views.student_detail, name='student_detail'),
    path('edit/<int:id>/',          views.edit_student,   name='edit_student'),
    path('delete/<int:id>/',        views.delete_student, name='delete_student'),

    # Subjects
    path('subjects/',                    views.subject_list,   name='subject_list'),
    path('subjects/add/',                views.add_subject,    name='add_subject'),
    path('subjects/<int:id>/edit/',      views.edit_subject,   name='edit_subject'),
    path('subjects/<int:id>/delete/',    views.delete_subject, name='delete_subject'),
    path('subjects/<int:id>/enroll/', views.enroll_student, name='enroll_student'),

    # Task management
    path('assign-task/',               views.assign_task,      name='assign_task'),
    path('teacher-feedback/',          views.teacher_feedback, name='teacher_feedback'),
    path('task-history/',              views.task_history,     name='task_history'),
    path('task/<int:task_id>/edit/',   views.edit_task,        name='edit_task'),
    path('task/<int:task_id>/delete/', views.delete_task,      name='delete_task'),
    path('recordings/<int:recording_id>/', views.task_recording_detail, name='task_recording_detail'),
    path('recordings/<int:recording_id>/download/', views.task_recording_download, name='task_recording_download'),

    # Monitoring
    path('monitoring/',             views.student_monitoring,    name='student_monitoring'),
    path('monitoring/status/',      views.monitoring_status_api, name='monitoring_status_api'),

    # Admin
    path('admin-dashboard/',                      views.admin_dashboard,   name='admin_dashboard'),
    path('admin-panel/users/',                    views.admin_user_list,   name='admin_user_list'),
    path('admin-panel/add-user/',                 views.admin_add_user,    name='admin_add_user'),
    path('admin-panel/edit-user/<int:id>/',       views.admin_edit_user,   name='admin_edit_user'),
    path('admin-panel/delete-user/<int:id>/',     views.admin_delete_user, name='admin_delete_user'),

    # Student
    path('student-dashboard/',           views.student_dashboard, name='student_dashboard'),
    path('student-dashboard/heartbeat/', views.student_heartbeat, name='student_heartbeat'),
    path('student-dashboard/profile/',   views.student_profile,   name='student_profile'),
    path('student-dashboard/tasks/',     views.student_tasks,     name='student_tasks'),
    path('task/<int:task_id>/complete/', views.complete_task,      name='complete_task'),
    path('task/<int:task_id>/evaluate/', views.submit_evaluation,  name='submit_evaluation'),
    path('student-dashboard/subjects/', views.student_subject_list,   name='student_subject_list'),
    path('student-dashboard/subjects/<int:id>/', views.student_subject_detail, name='student_subject_detail'),
]
