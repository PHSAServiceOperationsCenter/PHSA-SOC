# Generated by Django 2.0.7 on 2018-08-14 15:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OrionNode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True, help_text='object creation time stamp', verbose_name='created on')),
                ('updated_on', models.DateTimeField(auto_now_add=True, db_index=True, help_text='object update time stamp', verbose_name='updated on')),
                ('enabled', models.BooleanField(db_index=True, default=True, verbose_name='enabled')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='notes')),
                ('orion_id', models.BigIntegerField(db_index=True, help_text='Use the value in this field to query the Orion server', unique=True, verbose_name='Orion Object Id')),
                ('node_caption', models.CharField(db_index=True, max_length=254, verbose_name='Node Caption')),
                ('ip_address', models.GenericIPAddressField(db_index=True, protocol='IPv4', verbose_name='IP Address')),
                ('node_name', models.TextField(verbose_name='Node Name')),
                ('node_dns', models.CharField(db_index=True, max_length=254, verbose_name='DNS')),
                ('node_description', models.TextField(verbose_name='Orion Node Description')),
                ('vendor', models.CharField(blank=True, db_index=True, max_length=254, null=True, verbose_name='Vendor')),
                ('location', models.CharField(blank=True, db_index=True, max_length=254, null=True, verbose_name='Location')),
                ('machine_type', models.CharField(blank=True, db_index=True, help_text='this needs to become a foreign key', max_length=254, null=True, verbose_name='Machine Type')),
                ('status', models.CharField(db_index=True, max_length=254, verbose_name='Node Status')),
                ('status_orion_id', models.BigIntegerField(db_index=True, default=0, help_text='This will probably changes but that is how they do it for the moment; boohoo', verbose_name='Orion Node Status Id')),
                ('details_url', models.TextField(blank=True, null=True, verbose_name='Node Details URL')),
            ],
            options={
                'verbose_name': 'Orion Node',
                'verbose_name_plural': 'Orion Nodes',
            },
        ),
        migrations.CreateModel(
            name='OrionNodeCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True, help_text='object creation time stamp', verbose_name='created on')),
                ('updated_on', models.DateTimeField(auto_now_add=True, db_index=True, help_text='object update time stamp', verbose_name='updated on')),
                ('enabled', models.BooleanField(db_index=True, default=True, verbose_name='enabled')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='notes')),
                ('orion_id', models.BigIntegerField(db_index=True, help_text='Use the value in this field to query the Orion server', unique=True, verbose_name='Orion Object Id')),
                ('category', models.CharField(db_index=True, help_text='Orion Node Category Help', max_length=254, unique=True, verbose_name='Orion Node Category')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orion_integration_orionnodecategory_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orion_integration_orionnodecategory_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by')),
            ],
            options={
                'verbose_name': 'Orion Node Category',
                'verbose_name_plural': 'Orion Node Categories',
            },
        ),
        migrations.AddField(
            model_name='orionnode',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='orion_integration.OrionNodeCategory', verbose_name='Orion Node Category'),
        ),
        migrations.AddField(
            model_name='orionnode',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orion_integration_orionnode_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by'),
        ),
        migrations.AddField(
            model_name='orionnode',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orion_integration_orionnode_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by'),
        ),
    ]
