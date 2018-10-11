# Generated by Django 2.1.1 on 2018-09-24 20:34

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('rules_engine', '0008_auto_20180924_1838'),
    ]

    operations = [
        migrations.CreateModel(
            name='Broadcast',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True, help_text='object creation time stamp', verbose_name='created on')),
                ('updated_on', models.DateTimeField(auto_now=True, db_index=True, help_text='object update time stamp', verbose_name='updated on')),
                ('enabled', models.BooleanField(db_index=True, default=True, help_text='if this field is checked out, the row will always be excluded from any active operation', verbose_name='enabled')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='notes')),
                ('broadcast', models.CharField(db_index=True, max_length=64, unique=True, verbose_name='broadcast method')),
                ('is_default', models.BooleanField(db_index=True, default=False, help_text='use this broadcast method as the default', verbose_name='is the default')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='notifications_broadcast_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='notifications_broadcast_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by')),
            ],
            options={
                'verbose_name': 'Broadcast Method',
                'verbose_name_plural': 'Broadcast Methods',
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True, help_text='object creation time stamp', verbose_name='created on')),
                ('updated_on', models.DateTimeField(auto_now=True, db_index=True, help_text='object update time stamp', verbose_name='updated on')),
                ('enabled', models.BooleanField(db_index=True, default=True, help_text='if this field is checked out, the row will always be excluded from any active operation', verbose_name='enabled')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='notes')),
                ('rule_msg', models.TextField(verbose_name='rule message')),
                ('ack_on', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='acknowledged at')),
                ('esc_ack_on', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='escalation acknowledged at')),
                ('notification_uuid', models.UUIDField(db_index=True, unique=True, verbose_name='UUID')),
                ('instance_pk', models.BigIntegerField(blank=True, db_index=True, null=True, verbose_name='notification object row identifier')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='notifications_notification_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by')),
                ('rule_applies', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='rules_engine.RuleApplies', verbose_name='raised by')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='notifications_notification_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NotificationLevel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True, help_text='object creation time stamp', verbose_name='created on')),
                ('updated_on', models.DateTimeField(auto_now=True, db_index=True, help_text='object update time stamp', verbose_name='updated on')),
                ('enabled', models.BooleanField(db_index=True, default=True, help_text='if this field is checked out, the row will always be excluded from any active operation', verbose_name='enabled')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='notes')),
                ('notification_level', models.CharField(db_index=True, max_length=16, unique=True, verbose_name='notification level')),
                ('is_default', models.BooleanField(db_index=True, default=False, help_text='use this notification level as the default', verbose_name='is the default')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='notifications_notificationlevel_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='notifications_notificationlevel_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by')),
            ],
            options={
                'verbose_name': 'Notification Level',
                'verbose_name_plural': 'Notification Levels',
            },
        ),
        migrations.CreateModel(
            name='NotificationResponse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True, help_text='object creation time stamp', verbose_name='created on')),
                ('updated_on', models.DateTimeField(auto_now=True, db_index=True, help_text='object update time stamp', verbose_name='updated on')),
                ('enabled', models.BooleanField(db_index=True, default=True, help_text='if this field is checked out, the row will always be excluded from any active operation', verbose_name='enabled')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='notes')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='notifications_notificationresponse_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by')),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='notifications.Notification')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='notifications_notificationresponse_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NotificationType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True, help_text='object creation time stamp', verbose_name='created on')),
                ('updated_on', models.DateTimeField(auto_now=True, db_index=True, help_text='object update time stamp', verbose_name='updated on')),
                ('enabled', models.BooleanField(db_index=True, default=True, help_text='if this field is checked out, the row will always be excluded from any active operation', verbose_name='enabled')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='notes')),
                ('notification_type', models.CharField(db_index=True, max_length=128, unique=True, verbose_name='Notification Type')),
                ('ack_within', models.DurationField(blank=True, db_index=True, default=datetime.timedelta(0, 7200), null=True, verbose_name='requires acknowledgement within')),
                ('escalate_within', models.DurationField(blank=True, db_index=True, default=datetime.timedelta(0, 14400), null=True, verbose_name='escalate if not acknowledged within')),
                ('expire_within', models.DurationField(blank=True, db_index=True, default=datetime.timedelta(6), null=True, verbose_name='expires after')),
                ('delete_if_expired', models.BooleanField(db_index=True, default=False, verbose_name='delete if expired')),
                ('is_default', models.BooleanField(db_index=True, default=False, help_text='use this notification type as the default', verbose_name='is the default')),
                ('subscribers', models.TextField(blank=True, help_text='send notifications of this type to these users. this will be replaced by a reference once a subscriptions application becomes available', null=True, verbose_name='rule subscribers')),
                ('escalation_subscribers', models.TextField(blank=True, help_text='send escalation notifications of this type to these users. this will be replaced by a reference once a subscriptions application becomes available', null=True, verbose_name='rule escalation subscribers')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='notifications_notificationtype_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by')),
            ],
            options={
                'verbose_name': 'Notification Type',
                'verbose_name_plural': 'Notification Types',
            },
        ),
        migrations.CreateModel(
            name='NotificationTypeBroadcast',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True, help_text='object creation time stamp', verbose_name='created on')),
                ('updated_on', models.DateTimeField(auto_now=True, db_index=True, help_text='object update time stamp', verbose_name='updated on')),
                ('enabled', models.BooleanField(db_index=True, default=True, help_text='if this field is checked out, the row will always be excluded from any active operation', verbose_name='enabled')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='notes')),
                ('broadcast', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='notifications.Broadcast', verbose_name='via')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='notifications_notificationtypebroadcast_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by')),
                ('notification_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='notifications.NotificationType', verbose_name='Send notifications of this type')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='notifications_notificationtypebroadcast_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by')),
            ],
            options={
                'verbose_name': 'Notification Type Broadcast Method',
                'verbose_name_plural': 'Notification Type Broadcast Methods',
            },
        ),
        migrations.AddField(
            model_name='notificationtype',
            name='notification_broadcast',
            field=models.ManyToManyField(through='notifications.NotificationTypeBroadcast', to='notifications.Broadcast', verbose_name='Send Notifications of this Type Via'),
        ),
        migrations.AddField(
            model_name='notificationtype',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='notifications_notificationtype_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by'),
        ),
        migrations.AlterUniqueTogether(
            name='notificationtypebroadcast',
            unique_together={('notification_type', 'broadcast')},
        ),
    ]