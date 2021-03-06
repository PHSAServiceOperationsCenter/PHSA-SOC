# Generated by Django 2.2.6 on 2020-04-20 16:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import p_soc_auto_base.utils


class Migration(migrations.Migration):

    dependencies = [
        ('citrus_borg', '0031_auto_20200311_0913'),
    ]

    operations = [
    migrations.AlterField(
            model_name='allowedeventsource',
            name='created_by',
            field=models.ForeignKey(default=p_soc_auto_base.utils.get_default_user_id, on_delete=django.db.models.deletion.PROTECT, related_name='citrus_borg_allowedeventsource_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by'),
        ),
        migrations.AlterField(
            model_name='allowedeventsource',
            name='updated_by',
            field=models.ForeignKey(default=p_soc_auto_base.utils.get_default_user_id, on_delete=django.db.models.deletion.PROTECT, related_name='citrus_borg_allowedeventsource_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by'),
        ),
        migrations.AlterField(
            model_name='borgsite',
            name='created_by',
            field=models.ForeignKey(default=p_soc_auto_base.utils.get_default_user_id, on_delete=django.db.models.deletion.PROTECT, related_name='citrus_borg_borgsite_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by'),
        ),
        migrations.AlterField(
            model_name='borgsite',
            name='updated_by',
            field=models.ForeignKey(default=p_soc_auto_base.utils.get_default_user_id, on_delete=django.db.models.deletion.PROTECT, related_name='citrus_borg_borgsite_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by'),
        ),
        migrations.AlterField(
            model_name='eventcluster',
            name='created_by',
            field=models.ForeignKey(default=p_soc_auto_base.utils.get_default_user_id, on_delete=django.db.models.deletion.PROTECT, related_name='citrus_borg_eventcluster_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by'),
        ),
        migrations.AlterField(
            model_name='eventcluster',
            name='updated_by',
            field=models.ForeignKey(default=p_soc_auto_base.utils.get_default_user_id, on_delete=django.db.models.deletion.PROTECT, related_name='citrus_borg_eventcluster_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by'),
        ),
        migrations.AlterField(
            model_name='knownbrokeringdevice',
            name='created_by',
            field=models.ForeignKey(default=p_soc_auto_base.utils.get_default_user_id, on_delete=django.db.models.deletion.PROTECT, related_name='citrus_borg_knownbrokeringdevice_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by'),
        ),
        migrations.AlterField(
            model_name='knownbrokeringdevice',
            name='updated_by',
            field=models.ForeignKey(default=p_soc_auto_base.utils.get_default_user_id, on_delete=django.db.models.deletion.PROTECT, related_name='citrus_borg_knownbrokeringdevice_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by'),
        ),
        migrations.AlterField(
            model_name='windowslog',
            name='created_by',
            field=models.ForeignKey(default=p_soc_auto_base.utils.get_default_user_id, on_delete=django.db.models.deletion.PROTECT, related_name='citrus_borg_windowslog_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by'),
        ),
        migrations.AlterField(
            model_name='windowslog',
            name='updated_by',
            field=models.ForeignKey(default=p_soc_auto_base.utils.get_default_user_id, on_delete=django.db.models.deletion.PROTECT, related_name='citrus_borg_windowslog_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by'),
        ),
        migrations.AlterField(
            model_name='winlogbeathost',
            name='created_by',
            field=models.ForeignKey(default=p_soc_auto_base.utils.get_default_user_id, on_delete=django.db.models.deletion.PROTECT, related_name='citrus_borg_winlogbeathost_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by'),
        ),
        migrations.AlterField(
            model_name='winlogbeathost',
            name='updated_by',
            field=models.ForeignKey(default=p_soc_auto_base.utils.get_default_user_id, on_delete=django.db.models.deletion.PROTECT, related_name='citrus_borg_winlogbeathost_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by'),
        ),
        migrations.AlterField(
            model_name='winlogevent',
            name='created_by',
            field=models.ForeignKey(default=p_soc_auto_base.utils.get_default_user_id, on_delete=django.db.models.deletion.PROTECT, related_name='citrus_borg_winlogevent_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by'),
        ),
        migrations.AlterField(
            model_name='winlogevent',
            name='updated_by',
            field=models.ForeignKey(default=p_soc_auto_base.utils.get_default_user_id, on_delete=django.db.models.deletion.PROTECT, related_name='citrus_borg_winlogevent_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by'),
        ),
    ]
