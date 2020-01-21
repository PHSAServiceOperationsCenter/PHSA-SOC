# Generated by Django 2.1.1 on 2018-11-22 23:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('citrus_borg', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='winlogevent',
            name='created_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='citrus_borg_winlogevent_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='winlogevent',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, db_index=True, default=django.utils.timezone.now, help_text='object creation time stamp', verbose_name='created on'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='winlogevent',
            name='enabled',
            field=models.BooleanField(db_index=True, default=True, help_text='if this field is checked out, the row will always be excluded from any active operation', verbose_name='enabled'),
        ),
        migrations.AddField(
            model_name='winlogevent',
            name='is_expired',
            field=models.BooleanField(db_index=True, default=False, verbose_name='event has expired'),
        ),
        migrations.AddField(
            model_name='winlogevent',
            name='notes',
            field=models.TextField(blank=True, null=True, verbose_name='notes'),
        ),
        migrations.AddField(
            model_name='winlogevent',
            name='updated_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='citrus_borg_winlogevent_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='winlogevent',
            name='updated_on',
            field=models.DateTimeField(auto_now=True, db_index=True, help_text='object update time stamp', verbose_name='updated on'),
        ),
    ]
