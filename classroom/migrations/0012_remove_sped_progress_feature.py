from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('classroom', '0011_progresslabel_spedsubject_individuallearningplan_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ProgressLog',
        ),
        migrations.DeleteModel(
            name='ProgressAchievement',
        ),
        migrations.DeleteModel(
            name='IndividualLearningPlan',
        ),
        migrations.DeleteModel(
            name='ProgressLabel',
        ),
        migrations.DeleteModel(
            name='SPEDSubject',
        ),
    ]
