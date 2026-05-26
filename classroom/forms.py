from django import forms
from .models import Student

LEARNING_LEVEL_CHOICES = [
    ('', '-- Select Learning Level --'),
    ('beginner',    'Beginner'),
    ('developing',  'Developing'),
    ('independent', 'Independent'),
]

PROGRESS_STATUS_CHOICES = [
    ('', '-- Select Status --'),
    ('not_started', 'Not Started'),
    ('in_progress', 'In Progress'),
    ('achieved',    'Achieved'),
]


class StudentForm(forms.ModelForm):

    learning_level = forms.ChoiceField(
        choices=LEARNING_LEVEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    progress_status = forms.ChoiceField(
        choices=PROGRESS_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # All progress fields are optional — default to 0 when blank
    progress_communication = forms.IntegerField(
        required=False, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'})
    )
    progress_motor = forms.IntegerField(
        required=False, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'})
    )
    progress_social = forms.IntegerField(
        required=False, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'})
    )
    progress_selfcare = forms.IntegerField(
        required=False, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'})
    )
    progress_academic = forms.IntegerField(
        required=False, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'})
    )

    class Meta:
        model  = Student
        fields = [
            'name', 'lrn', 'age', 'learning_level',
            'phone_number', 'email', 'address',
            'birth_certificate', 'profile_picture',
            'grading_type', 'progress_status', 'learning_goals', 'skills_focus',
            'progress_communication', 'progress_motor', 'progress_social',
            'progress_selfcare', 'progress_academic',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name',
                'minlength': '2',
            }),
            'lrn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12-digit LRN',
                'maxlength': '12',
                'pattern': '[0-9]{1,12}',
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '3', 'max': '25',
                'placeholder': 'Age',
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '09XX-XXX-XXXX',
                'maxlength': '15',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'student@email.com',
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Street, Barangay, City',
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png,image/gif',
            }),
            'birth_certificate': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'application/pdf,image/jpeg,image/png',
            }),
            'grading_type': forms.RadioSelect(),
            'learning_goals': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Improve communication, develop self-care skills...',
                'rows': 3,
            }),
            'skills_focus': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Communication, Motor Skills, Social Skills',
            }),
        }

    def clean_progress_communication(self):
        return self.cleaned_data.get('progress_communication') or 0

    def clean_lrn(self):
        lrn = (self.cleaned_data.get('lrn') or '').strip()
        if not lrn:
            return None
        if not lrn.isdigit():
            raise forms.ValidationError("LRN must contain numbers only.")

        duplicate_students = Student.objects.filter(lrn=lrn)
        if self.instance and self.instance.pk:
            duplicate_students = duplicate_students.exclude(pk=self.instance.pk)
        if duplicate_students.exists():
            raise forms.ValidationError("This LRN is already assigned to another student.")
        return lrn

    def clean_progress_motor(self):
        return self.cleaned_data.get('progress_motor') or 0

    def clean_progress_social(self):
        return self.cleaned_data.get('progress_social') or 0

    def clean_progress_selfcare(self):
        return self.cleaned_data.get('progress_selfcare') or 0

    def clean_progress_academic(self):
        return self.cleaned_data.get('progress_academic') or 0
