"""
Run this ONCE to clean up stale is_online flags and open sessions.

Usage:
    python manage.py shell < fix_stale_sessions.py

Or paste the contents into:
    python manage.py shell
"""

import django
from django.utils import timezone
from classroom.models import UserProfile, Student, StudentSession

print("=== Cleaning up stale online statuses ===\n")

# 1. Close all open StudentSession rows (no logout_time)
open_sessions = StudentSession.objects.filter(logout_time__isnull=True)
print(f"Found {open_sessions.count()} open session(s) with no logout time.")
for s in open_sessions:
    s.logout_time = s.login_time  # mark as instantly logged out
    s.save(update_fields=['logout_time'])
    print(f"  Closed session for: {s.student.name} (login: {s.login_time})")

# 2. Mark all student profiles as offline
stale = UserProfile.objects.filter(role='student', is_online=True)
print(f"\nFound {stale.count()} student(s) marked is_online=True.")
for p in stale:
    p.is_online = False
    p.save(update_fields=['is_online'])
    print(f"  Marked offline: {p.user.username}")

print("\n=== Done. All stale sessions cleared. ===")
print("Now log students back in fresh and the monitoring will be accurate.")