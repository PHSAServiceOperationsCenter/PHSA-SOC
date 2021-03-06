"""
p_soc_auto.dashboard
--------------------

This module contains the custom main dashboard class that replaces the
`Django Admin` home page.

See the `Grappelli Dashboard
<https://django-grappelli.readthedocs.io/en/latest/index.html#dashboard>`__
documentation for details.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""

from django.utils.translation import ugettext_lazy as _
from django.urls import reverse

from grappelli.dashboard import modules, Dashboard
from grappelli.dashboard.utils import get_admin_site_name


class CustomIndexDashboard(Dashboard):
    """
    Custom dashboard class
    """

    def init_with_context(self, context):
        site_name = get_admin_site_name(context)

        self.children.append(modules.Group(
            _('PHSA Service Operations Center Applications'),
            column=1, collapsible=False,
            children=[
                modules.ModelList(
                    _('Citrix Remote Monitoring'), collapsible=True,
                    css_classes=('collapse closed',),
                    models=('citrus_borg.models.*',)),
                modules.ModelList(
                    _('Exchange Remote Monitoring'), collapsible=True,
                    css_classes=('collapse closed',),
                    models=('mail_collector.models.*',)),
                modules.ModelList(
                    _('AD Controllers Monitoring'), collapsible=True,
                    css_classes=('collapse closed',),
                    models=('ldap_probe.models.*',)),
                modules.ModelList(
                    _('SSL Certificates Tracker'), collapsible=True,
                    css_classes=('collapse closed',),
                    models=('ssl_cert_tracker.models.*',),
                    exclude=('p_soc_auto_base.models.Subscription',)),
                modules.ModelList(
                    _('Orion Integration'), collapsible=True,
                    css_classes=('collapse closed',),
                    models=('orion_integration.models.*',)), ]))

        self.children.append(modules.Group(
            _('Administration'), column=2, collapsible=True,
            children=[
                modules.ModelList(
                    _('Authentication and Authorization'), collapsible=True,
                    models=('django.contrib.*',)),
                modules.ModelList(
                    _('Periodic Tasks Configuration'), collapsible=True,
                    models=('django_celery_beat.*',)),
                modules.ModelList(
                    _('Preferences'), collapsible=True,
                    models=('dynamic_preferences.*',)),
                modules.ModelList(
                    _('Email Subscriptions'), collapsible=True,
                    models=('p_soc_auto_base.models.Subscription',)),
                modules.RecentActions(
                    _('Recent Actions'), limit=5, collapsible=True,), ]))

        self.children.append(modules.LinkList(
            _('User guides'), column=3,
            children=[
                {'title': _('SOC Automation Documentation'),
                 'url': '/soc_docs/',
                 'external': False, },
                {'title': _('SOC Automation Source Control Documentation'),
                 'url': '/soc_docs/p_soc_auto/git.html',
                 'external': False, },
                {'title': ('Configuring SSL Alerts and SSL Monitoring on the'
                           ' Automation Server'),
                 'url': ('http://our.healthbc.org/sites/gateway/team/TSCSTHub/'
                         '_layouts/15/WopiFrame2.aspx?sourcedoc=/sites/gateway/'
                         'team/TSCSTHub/Shared Documents/Drafts/SOC - Procedural'
                         ' Guide - Configuring SSL alerts and monitoring on the'
                         ' Automation Server.doc&action=default'),
                 'external': True, },
                {'title': ('Exchange Monitoring Client'),
                 'url': ('http://our.healthbc.org/sites/gateway/team/TSCSTHub/'
                         '_layouts/15/WopiFrame2.aspx?sourcedoc=/sites/gateway/'
                         'team/TSCSTHub/Shared Documents/Drafts/SOC - Procedural'
                         ' Guide - Exchange Monitoring Client Version 2.'
                         'doc&action=default'),
                 'external': True, },
                {'title': ('Handling Emails From the Citrix Monitoring Automation'
                           ' Server'),
                 'url': ('http://our.healthbc.org/sites/gateway/team/TSCSTHub/'
                         '_layouts/15/WopiFrame2.aspx?sourcedoc=/sites/gateway/'
                         'team/TSCSTHub/Shared Documents/Drafts/SOC - Procedural'
                         ' Guide - Handling Emails From the Citrix Monitoring'
                         ' Automation Server.doc&action=default'),
                 'external': True, },
                {'title': "Other MOP's",
                 'url': ('http://our.healthbc.org/sites/gateway/team/TSCSTHub/'
                         'Shared Documents/Forms/AllItems.aspx?'
                         'RootFolder=%2fsites%2fgateway%2fteam%2fTSCSTHub%2fShared'
                         ' Documents%2fMethod of Procedures (MOPs)&Folder'
                         'CTID=0x01200049BD2FC3E2032F40A74A4A7D97D53F7A'),
                 'external': True},
                {'title': 'PHSA SOC SharePoint',
                 'url': ('http://our.healthbc.org/sites/gateway/team/TSCSTHub/'
                         'SitePages/Home.aspx'),
                 'external': True, }, ]))

        self.children.append(modules.LinkList(
            _('Support'), column=3,
            children=[
                {'title': _('Django Documentation'),
                    'url': 'http://docs.djangoproject.com/',
                    'external': True, },
                {'title': _('Grappelli Documentation'),
                    'url': 'http://packages.python.org/django-grappelli/',
                    'external': True, },
                {'title': _('Grappelli Google-Code'),
                    'url': 'http://code.google.com/p/django-grappelli/',
                    'external': True, }, ]))

        self.children.append(modules.Feed(
            _('Latest Django News'), column=3, limit=5,
            feed_url='http://www.djangoproject.com/rss/weblog/'))
