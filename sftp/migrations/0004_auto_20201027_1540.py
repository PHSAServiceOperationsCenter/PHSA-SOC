# Generated by Django 2.2.6 on 2020-10-27 22:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import p_soc_auto_base.utils


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sftp', '0003_auto_20201022_1522'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='sftpuploadlog',
            options={'ordering': ['-created'], 'verbose_name': 'SFTP Upload Log'},
        ),
        migrations.RenameField(
            model_name='sftpuploadlog',
            old_name='created_on',
            new_name='created',
        ),
        migrations.RemoveField(
            model_name='sftpuploadlog',
            name='uuid',
        ),
        migrations.AddField(
            model_name='sftpuploadlog',
            name='created_by',
            field=models.ForeignKey(default=p_soc_auto_base.utils.get_default_user_id, on_delete=django.db.models.deletion.PROTECT, related_name='sftp_sftpuploadlog_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by'),
        ),
        migrations.AddField(
            model_name='sftpuploadlog',
            name='enabled',
            field=models.BooleanField(db_index=True, default=True, help_text='if this field is checked out, the row will always be excluded from any active operation', verbose_name='enabled'),
        ),
        migrations.AddField(
            model_name='sftpuploadlog',
            name='notes',
            field=models.TextField(blank=True, null=True, verbose_name='notes'),
        ),
        migrations.AddField(
            model_name='sftpuploadlog',
            name='updated_by',
            field=models.ForeignKey(default=p_soc_auto_base.utils.get_default_user_id, on_delete=django.db.models.deletion.PROTECT, related_name='sftp_sftpuploadlog_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by'),
        ),
        migrations.AddField(
            model_name='sftpuploadlog',
            name='updated_on',
            field=models.DateTimeField(auto_now=True, db_index=True, help_text='object update time stamp', verbose_name='updated on'),
        ),
    ]