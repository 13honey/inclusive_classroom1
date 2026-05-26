from django.test import TestCase
from .forms import StudentForm
from .models import Student


class StudentFormTests(TestCase):
    def test_lrn_must_be_unique_when_present(self):
        Student.objects.create(name="Existing Student", age=10, lrn="123456789012")

        form = StudentForm(data={
            "name": "New Student",
            "age": 9,
            "lrn": "123456789012",
            "grading_type": "ungraded",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("lrn", form.errors)

    def test_blank_lrn_is_allowed_for_multiple_students(self):
        Student.objects.create(name="Existing Student", age=10, lrn=None)

        form = StudentForm(data={
            "name": "New Student",
            "age": 9,
            "lrn": "",
            "grading_type": "ungraded",
        })

        self.assertTrue(form.is_valid())
