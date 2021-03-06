# Generated by Django 2.2.6 on 2019-11-13 18:50

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import ldap_probe.models
import p_soc_auto_base.models
import p_soc_auto_base.utils
import re


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('orion_integration', '0014_oriondomaincontrollernode'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LDAPBindCred',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True, help_text='object creation time stamp', verbose_name='created on')),
                ('updated_on', models.DateTimeField(auto_now=True, db_index=True, help_text='object update time stamp', verbose_name='updated on')),
                ('enabled', models.BooleanField(db_index=True, default=True, help_text='if this field is checked out, the row will always be excluded from any active operation', verbose_name='enabled')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='notes')),
                ('is_default', models.BooleanField(db_index=True, default=False, verbose_name='default windows account')),
                ('domain', models.CharField(db_index=True, max_length=15, validators=[django.core.validators.RegexValidator(re.compile('^[-a-zA-Z0-9_]+\\Z'), "Enter a valid 'slug' consisting of letters, numbers, underscores or hyphens.", 'invalid')], verbose_name='windows domain')),
                ('username', models.CharField(db_index=True, max_length=64, validators=[django.core.validators.RegexValidator(re.compile('^[-a-zA-Z0-9_]+\\Z'), "Enter a valid 'slug' consisting of letters, numbers, underscores or hyphens.", 'invalid')], verbose_name='domain username')),
                ('password', models.CharField(max_length=64, verbose_name='password')),
                ('ldap_search_base', models.CharField(default=ldap_probe.models._get_default_ldap_search_base, max_length=128, verbose_name='DN search base')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ldap_probe_ldapbindcred_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ldap_probe_ldapbindcred_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by')),
            ],
            options={
                'verbose_name': 'LDAP Bind Credentials Set',
                'verbose_name_plural': 'LDAP Bind Credentials Sets',
            },
        ),
        migrations.CreateModel(
            name='OrionADNode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True, help_text='object creation time stamp', verbose_name='created on')),
                ('updated_on', models.DateTimeField(auto_now=True, db_index=True, help_text='object update time stamp', verbose_name='updated on')),
                ('enabled', models.BooleanField(db_index=True, default=True, help_text='if this field is checked out, the row will always be excluded from any active operation', verbose_name='enabled')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='notes')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ldap_probe_orionadnode_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by')),
                ('ldap_bind_cred', models.ForeignKey(default=p_soc_auto_base.models.BaseModelWithDefaultInstance.get_default, on_delete=django.db.models.deletion.PROTECT, to='ldap_probe.LDAPBindCred', verbose_name='LDAP Bind Credentials')),
                ('node', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='orion_integration.OrionDomainControllerNode', verbose_name='Orion Node for Domain Controller')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ldap_probe_orionadnode_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by')),
            ],
            options={
                'verbose_name': 'Domain Controller from Orion',
                'verbose_name_plural': 'Domain Controllers from Orion',
            },
        ),
        migrations.CreateModel(
            name='NonOrionADNode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True, help_text='object creation time stamp', verbose_name='created on')),
                ('updated_on', models.DateTimeField(auto_now=True, db_index=True, help_text='object update time stamp', verbose_name='updated on')),
                ('enabled', models.BooleanField(db_index=True, default=True, help_text='if this field is checked out, the row will always be excluded from any active operation', verbose_name='enabled')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='notes')),
                ('node_dns', models.CharField(db_index=True, help_text='The FQDN of the domain controller host. It must respect the rules specified in `RFC1123 <http://www.faqs.org/rfcs/rfc1123.html>`__, section 2.1', max_length=255, unique=True, verbose_name='FUlly Qualified Domain Name (FQDN)')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ldap_probe_nonorionadnode_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by')),
                ('ldap_bind_cred', models.ForeignKey(default=p_soc_auto_base.models.BaseModelWithDefaultInstance.get_default, on_delete=django.db.models.deletion.PROTECT, to='ldap_probe.LDAPBindCred', verbose_name='LDAP Bind Credentials')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ldap_probe_nonorionadnode_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by')),
            ],
            options={
                'verbose_name': 'Domain Controller not present in Orion',
                'verbose_name_plural': 'Domain Controllers not present in Orion',
            },
        ),
        migrations.CreateModel(
            name='LdapProbeLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=p_soc_auto_base.utils.get_uuid, unique=True, verbose_name='UUID')),
                ('elapsed_initialize', models.DurationField(blank=True, null=True, verbose_name='LDAP initialization duration')),
                ('elapsed_bind', models.DurationField(blank=True, null=True, verbose_name='LDAP bind duration')),
                ('elapsed_anon_bind', models.DurationField(blank=True, null=True, verbose_name='LDAP anonymous bind duration')),
                ('elapsed_read_root', models.DurationField(blank=True, null=True, verbose_name='LDAP read root DSE duration')),
                ('elapsed_searc_ext', models.DurationField(blank=True, null=True, verbose_name='LDAP extended search duration')),
                ('errors', models.TextField(blank=True, null=True, verbose_name='Errors')),
                ('ad_node', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ldap_probe.NonOrionADNode', verbose_name='AD controller')),
                ('ad_orion_node', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ldap_probe.OrionADNode', verbose_name='AD controller (Orion)')),
            ],
            options={
                'verbose_name': 'AD service probe',
                'verbose_name_plural': 'AD service probes',
            },
        ),
        migrations.AddIndex(
            model_name='ldapbindcred',
            index=models.Index(fields=['domain', 'username'], name='ldap_probe__domain_d72f9a_idx'),
        ),
        migrations.AddConstraint(
            model_name='ldapbindcred',
            constraint=models.UniqueConstraint(fields=('domain', 'username'), name='unique_account'),
        ),
    ]
