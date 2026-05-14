from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Classification(models.Model):
    CLASSIFICATION_CHOICES = (
        ('hearing_impairment', 'Hearing Impairment'),
        ('visual_impairment', 'Visual Impairment'),
        ('down_syndrome', 'Down Syndrome'),
        ('multiple_disability', 'Multiple Disability'),
    )
    name = models.CharField(max_length=50, choices=CLASSIFICATION_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.get_name_display()


class Subject(models.Model):
    ICON_CHOICES = [
        ('🗣️', 'Communication'),
        ('🤲', 'Motor Skills'),
        ('🧠', 'Cognitive'),
        ('👥', 'Social Skills'),
        ('🪥', 'Self-Care'),
        ('📖', 'Academic'),
        ('🎨', 'Creative Arts'),
        ('🏃', 'Physical'),
        ('📚', 'General'),
    ]
    name        = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon        = models.CharField(max_length=10, default='📚')
    color       = models.CharField(max_length=20, default='#2563eb', help_text='Hex color e.g. #2563eb')
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='subjects_created')
    created_at  = models.DateTimeField(auto_now_add=True)
    students    = models.ManyToManyField('Student', blank=True, related_name='subjects')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Student(models.Model):

    GRADING_CHOICES = [
        ('graded', 'Graded'),
        ('ungraded', 'Ungraded'),
    ]
    LEARNING_LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('developing', 'Developing'),
        ('independent', 'Independent'),
    ]
    PROGRESS_STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('achieved', 'Achieved'),
    ]

    # ── Core Fields ──────────────────────────────────────────────────────────
    user             = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_students',
    )
    name             = models.CharField(max_length=100)
    lrn              = models.CharField(max_length=12, unique=True, blank=True, null=True, verbose_name="LRN")
    age              = models.IntegerField()
    grade_level      = models.CharField(max_length=50, blank=True, default='')
    classifications  = models.ManyToManyField(Classification, blank=True)
    phone_number     = models.CharField(max_length=15, blank=True, null=True)
    email            = models.EmailField(max_length=100, blank=True, null=True)
    address          = models.TextField(blank=True, null=True)
    birth_certificate= models.FileField(upload_to='birth_certificates/', blank=True, null=True)
    enrolled_date    = models.DateField(auto_now_add=True)
    profile_picture  = models.ImageField(upload_to='student_pictures/', blank=True, null=True)

    # ── Grading ──────────────────────────────────────────────────────────────
    grading_type = models.CharField(
        max_length=20,
        choices=GRADING_CHOICES,
        default='ungraded',
        help_text='SPED learners are typically ungraded',
    )

    # ── SPED Learning Profile ─────────────────────────────────────────────
    learning_level  = models.CharField(max_length=20, choices=LEARNING_LEVEL_CHOICES, blank=True, null=True)
    progress_status = models.CharField(max_length=20, choices=PROGRESS_STATUS_CHOICES, blank=True, null=True)
    learning_goals  = models.TextField(blank=True, null=True)
    skills_focus    = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="Comma-separated e.g. Communication, Motor Skills"
    )

    # ── Skills Progress (0–100) ───────────────────────────────────────────
    progress_communication = models.IntegerField(default=0)
    progress_motor         = models.IntegerField(default=0)
    progress_social        = models.IntegerField(default=0)
    progress_selfcare      = models.IntegerField(default=0)
    progress_academic      = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Task(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    )
    student     = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='tasks')
    subject     = models.ForeignKey('Subject', on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    deadline    = models.DateTimeField()
    attachment  = models.FileField(upload_to='task_attachments/', blank=True, null=True)
    video_url   = models.URLField(blank=True, null=True, verbose_name="YouTube/Video Link")
    video_file  = models.FileField(upload_to='task_videos/', blank=True, null=True)
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    output_file = models.FileField(upload_to='task_outputs/', blank=True, null=True)
    completed_at= models.DateTimeField(blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tasks_created')

    def __str__(self):
        return f"{self.title} - {self.student.name}"


class TaskEvaluation(models.Model):
    """
    Stores the post-completion evaluation filled by the student
    or parent/guardian right after a task is marked as done.
    One evaluation per task (OneToOne).
    """

    ENJOYMENT_CHOICES = [
        (1, 'Did not enjoy'),
        (2, 'Okay'),
        (3, 'Liked it'),
        (4, 'Really liked it'),
        (5, 'Loved it'),
    ]
    DIFFICULTY_CHOICES = [
        ('easy',      'Easy'),
        ('little',    'A little hard'),
        ('very_hard', 'Very hard'),
    ]
    EFFORT_CHOICES = [
        ('alone',     'I did it by myself'),
        ('some_help', 'I needed some help'),
        ('lot_help',  'I needed a lot of help'),
    ]
    FEELING_CHOICES = [
        ('happy',      'Happy'),
        ('okay',       'Okay'),
        ('frustrated', 'Frustrated'),
    ]
    PARTICIPATION_CHOICES = [
        ('active',       'Active'),
        ('okay',         'Okay'),
        ('encouraged',   'Needed encouragement'),
    ]

    task        = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='evaluation')
    submitted_at= models.DateTimeField(auto_now_add=True)

    # Q1 — enjoyment rating (1–5 stars)
    enjoyment   = models.IntegerField(choices=ENJOYMENT_CHOICES, null=True, blank=True)

    # Q2 — difficulty
    difficulty  = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, blank=True)

    # Q3 — effort level
    effort      = models.CharField(max_length=20, choices=EFFORT_CHOICES, blank=True)

    # Q4 — feeling
    feeling     = models.CharField(max_length=20, choices=FEELING_CHOICES, blank=True)

    # Q5 — parent/guardian participation (optional)
    participation = models.CharField(max_length=20, choices=PARTICIPATION_CHOICES, blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Evaluation for '{self.task.title}' — {self.task.student.name}"

    @property
    def enjoyment_label(self):
        return dict(self.ENJOYMENT_CHOICES).get(self.enjoyment, '—')

    @property
    def stars(self):
        return '⭐' * (self.enjoyment or 0)


class TaskRecording(models.Model):
    task         = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='recordings')
    student      = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='task_recordings')
    subject      = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name='task_recordings')
    video_file   = models.FileField(upload_to='task_recordings/')
    recorded_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"Recording for '{self.task.title}' - {self.student.name}"


class TeacherFeedback(models.Model):
    student        = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='feedbacks')
    teacher        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='feedbacks_given')
    observation    = models.TextField()
    recommendation = models.TextField(blank=True, null=True)
    date           = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Feedback for {self.student.name} by {self.teacher.username}"

    @property
    def teacher_name(self):
        return self.teacher.username if self.teacher else "Teacher"


# ── Student Session Tracking ─────────────────────────────────────────────────

class StudentSession(models.Model):
    student    = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='sessions')
    login_time = models.DateTimeField()
    logout_time= models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-login_time']

    @property
    def duration(self):
        if self.logout_time and self.login_time:
            diff  = self.logout_time - self.login_time
            total = int(diff.total_seconds())
            h, rem = divmod(total, 3600)
            m, s   = divmod(rem, 60)
            if h:   return f"{h}h {m}m"
            elif m: return f"{m}m {s}s"
            else:   return f"{s}s"
        return None

    def __str__(self):
        return f"{self.student.name} — {self.login_time.strftime('%Y-%m-%d %H:%M')}"
