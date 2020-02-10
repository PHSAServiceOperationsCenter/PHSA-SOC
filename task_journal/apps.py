"""
.. _apps:

django apps module for the task_journal app

:module:    p_soc_auto.task_journal.apps

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TaskJournalConfig(AppConfig):
    """
    task_journal application class
    """
    name = 'task_journal'
    verbose_name = _(
        'PPHSA Service Operations Center Internal Task Execution Diary')

    def ready(self):
        """
        place holder for django style imports
        """
        pass
