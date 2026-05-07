from django.contrib import admin
from .models import (
    UserProfile, Student, Classification, Task,
)

admin.site.register(UserProfile)
admin.site.register(Student)
admin.site.register(Classification)
admin.site.register(Task)
