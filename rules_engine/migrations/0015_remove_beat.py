# Generated by Django 2.1.4 on 2019-03-21 20:32

from django.db import migrations


def remove_beats(apps, schema_editor):
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')

    PeriodicTask.objects.filter(task__icontains='rules_engine').all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('rules_engine', '0014_auto_20181018_1522'),
    ]

    operations = [
        migrations.RunPython(remove_beats,
                             reverse_code=migrations.RunPython.noop)

    ]