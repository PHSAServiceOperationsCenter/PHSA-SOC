"""
.. _base_models:

django models for the base app

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

Abstract base model classes
"""
__updated__ = '2018_08_08'

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.


class BaseModel(models.Model):
    """
    Abstract base model class

    All the fields defined in this class will show in :class:`Django models
    <django.db.models.Model>` inheriting from this class as if they were
    defined in the child class.
    """
    created_by = models.ForeignKey(
        get_user_model(), on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_created_by_related',
        verbose_name=_('created by'))
    """
    capture a reference to the user responsible for creating the database row

    See `User authentication in Django
    <https://docs.djangoproject.com/en/2.2/topics/auth/>`_ and `Referencing
    the User model <https://docs.djangoproject.com/en/2.2/topics/auth/customizing/#referencing-the-user-model>`_
    about details
    """
    updated_by = models.ForeignKey(
        get_user_model(), on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_updated_by_related',
        verbose_name=_('updated by'))
    """
    capture a reference to the user responsible for updating the database row
    """
    created_on = models.DateTimeField(
        _('created on'), db_index=True, auto_now_add=True,
        help_text=_('object creation time stamp'))
    """
    time stamp for database row creation
    """
    updated_on = models.DateTimeField(
        _('updated on'), db_index=True, auto_now=True,
        help_text=_('object update time stamp'))
    """
    time stamp for database row update
    """
    enabled = models.BooleanField(
        _('enabled'), db_index=True, default=True, null=False, blank=False,
        help_text=_('if this field is checked out, the row will always be'
                    ' excluded from any active operation'))
    """
    use this field to avoid deleting rows
    
    When this field is ``False``, any computation against the
    :class:`Django model <django.db.models.Model>` containing this field will
    treat the corresponding as if it doesn't exist
    """
    notes = models.TextField(_('notes'), null=True, blank=True)
    """
    always have a description or notes or details field in a
    :class:`Django model <django.db.models.Model>`
    """

    @classmethod
    def get_or_create_user(cls, username):
        """
        get or create a user

        If a user is created, they are not guaranteed to have any kind of
        privileges and or access permissions on the :ref:`SOC Automation
        Server`.

        When data is maintained using background processes, it is not
        almost obvious who the responsible user is.

        By convention, the background process must announce the user
        responsible for the data change and this method will make sure
        that this user exists.

        We are defining this method as a class method because we may have to
        call it from places where we don't have access to a model instance.

        :arg str username: the username to get or create

        :returns: an instance of the :class:`django.contrib.auth.models.User`
            model
        """
        user = get_user_model().objects.filter(username__iexact=username)
        if not user.exists():
            get_user_model().objects.create_user(username)

        return user.get()

    class Meta:
        abstract = True
