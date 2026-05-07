from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    """Fires every time any user successfully logs in."""
    from .models import UserProfile, Student, StudentSession

    try:
        profile = UserProfile.objects.get(user=user)
        profile.is_online = True
        profile.last_seen = timezone.now()
        profile.save(update_fields=['is_online', 'last_seen'])

        if profile.role == 'student':
            teacher = UserProfile.objects.filter(role='teacher').select_related('user').first()
            student, _ = Student.objects.get_or_create(
                user=user,
                defaults={
                    'assigned_teacher': teacher.user if teacher else None,
                    'name': user.get_full_name() or user.username,
                    'age': 0,
                    'email': user.email or None,
                },
            )
            # Close any leftover open sessions
            StudentSession.objects.filter(
                student=student,
                logout_time__isnull=True
            ).update(logout_time=timezone.now())
            # Create a fresh session
            StudentSession.objects.create(
                student=student,
                login_time=timezone.now(),
            )
    except UserProfile.DoesNotExist:
        pass


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    """Fires every time any user logs out — including session expiry."""
    if user is None:
        return

    from .models import UserProfile, Student, StudentSession

    try:
        profile = UserProfile.objects.get(user=user)
        profile.is_online = False
        profile.last_seen = timezone.now()
        profile.save(update_fields=['is_online', 'last_seen'])

        if profile.role == 'student':
            try:
                student = Student.objects.get(user=user)
                StudentSession.objects.filter(
                    student=student,
                    logout_time__isnull=True
                ).update(logout_time=timezone.now())
            except Student.DoesNotExist:
                pass
    except UserProfile.DoesNotExist:
        pass
