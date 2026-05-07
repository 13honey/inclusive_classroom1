from django.utils import timezone
from django.conf import settings
from .models import UserProfile, Student, StudentSession


class OnlineStatusMiddleware:
    """
    Updates last_seen and is_online=True on every authenticated request.
    This is what powers the stale-session detection in close_stale_sessions().
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                profile = UserProfile.objects.get(user=request.user)
                profile.is_online = True
                profile.last_seen = timezone.now()
                profile.save(update_fields=['is_online', 'last_seen'])
            except UserProfile.DoesNotExist:
                pass

        return self.get_response(request)


def close_stale_sessions():
    """
    Marks offline any student who hasn't made a request in ONLINE_TIMEOUT_SECONDS.
    Also closes their open StudentSession row with the last_seen time as logout.

    Called on every monitoring page load and every /monitoring/status/ API poll.
    """
    timeout_seconds = getattr(settings, 'ONLINE_TIMEOUT_SECONDS', 300)
    cutoff = timezone.now() - timezone.timedelta(seconds=timeout_seconds)

    stale_profiles = UserProfile.objects.filter(
        role='student',
        is_online=True,
        last_seen__lt=cutoff,
    )

    for profile in stale_profiles:
        profile.is_online = False
        profile.save(update_fields=['is_online'])

        try:
            student = Student.objects.get(user=profile.user)
            open_session = StudentSession.objects.filter(
                student=student,
                logout_time__isnull=True,
            ).order_by('-login_time').first()

            if open_session:
                open_session.logout_time = profile.last_seen  # use last activity as logout time
                open_session.save(update_fields=['logout_time'])
        except Student.DoesNotExist:
            pass