"""
ldap_probe.managers
-------------------

This module contains the :class:`django.db.models.Manager` managers for the
:ref:`Active Directory Services Monitoring Application`.

:copyright:

    Copyright 2020 Provincial Health Service Authority
    of British Columbia

"""
from django.db import models


# Managers only require the get_queryset method
# pylint: disable=too-few-public-methods
class LdapProbeLogFullBindManager(models.Manager):
    """
    custom :class:`django.db.models.Manager` used by the
    :class:`LdapProbeFullBindLog` model

    We have observed that the default set of `Windows` domain credentials
    will allow full LDAP binds for a limited number of `AD` controllers.
    By design LDAP probe data collected from these `AD` controllers will
    present with :attr:`LdapProbeLog.elapsed_bind` values that are not null.
    """

    def get_queryset(self):
        """
        override :meth:`django.db.models.Manager.get_queryset`

        See `Modifying a manager's initial QuerySet
        <https://docs.djangoproject.com/en/2.2/topics/db/managers/#modifying-a-manager-s-initial-queryset>`__
        in the `Django` docs.

        :returns: a :class:`django.db.models.query.QuerySet` with the
            :class:`LdapProbeLog` instances that contain timing data for
            `LDAP` full bind operations
        """
        return super().get_queryset().filter(elapsed_bind__isnull=False)


class LdapProbeLogAnonBindManager(models.Manager):
    """
    custom :class:`django.db.models.Manager` used by the
    :class:`LdapProbeAnonBindLog` model

    We have observed that the default set of `Windows` domain credentials
    will not allow full LDAP binds (see :class:`LdapProbeLogFullBindManager`)
    for most of `AD` controllers.
    By design LDAP probe data collected from these `AD` controllers will
    present with :attr:`LdapProbeLog.elapsed_anon_bind` values that are not
    null (`None` in `Python` speak).
    """

    def get_queryset(self):
        """
        override :meth:`django.db.models.Manager.get_queryset`

        See `Modifying a manager's initial QuerySet
        <https://docs.djangoproject.com/en/2.2/topics/db/managers/#modifying-a-manager-s-initial-queryset>`__
        in the `Django` docs.

        :returns: a :class:`django.db.models.query.QuerySet` with the
            :class:`LdapProbeLog` instances that contain timing data for
            `LDAP` anonymous bind operations
        """
        return super().get_queryset().filter(elapsed_anon_bind__isnull=False)


class LdapProbeLogFailedManager(models.Manager):
    """
    custom :class:`django.db.models.Manager` used by the
    :class:`LdapProbeLogFailed` model
    """

    def get_queryset(self):
        """
        override :meth:`django.db.models.Manager.get_queryset`

        See `Modifying a manager's initial QuerySet
        <https://docs.djangoproject.com/en/2.2/topics/db/managers/#modifying-a-manager-s-initial-queryset>`__
        in the `Django` docs.

        :returns: a :class:`django.db.models.query.QuerySet` with the
            :class:`LdapProbeLog` failed instances
        """
        return super().get_queryset().filter(failed=True)
