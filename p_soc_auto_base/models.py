"""
.. _base_models:

Django models for the base app

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

Abstract base model classes
"""
__updated__ = '2018_08_08'

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.


class BaseModel(models.Model):
    """
    Abstract base model class

    All the fields defined in this class will show in :class:`Django models
    <django.db.models.Model>` inheriting from this class as if they were
    defined directly in the child class.

    See `Abstract base classes
    <https://docs.djangoproject.com/en/2.2/topics/db/models/#abstract-base-classes>`__
    in the `Django` docs.
    """
    created_by = models.ForeignKey(
        get_user_model(), on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_created_by_related',
        verbose_name=_('created by'))
    """
    capture a reference to the user responsible for creating the database row

    See `User authentication in Django
    <https://docs.djangoproject.com/en/2.2/topics/auth/>`_ and `Referencing
    the User model
    <https://docs.djangoproject.com/en/2.2/topics/auth/customizing/#referencing-the-user-model>`__
    about details.
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
    treat it as if it doesn't exist.
    """
    notes = models.TextField(_('notes'), null=True, blank=True)
    """
    always have a description/notes/details field in a
    :class:`Django model <django.db.models.Model>`.
    """

    @classmethod
    def get_or_create_user(cls, username):
        """
        get or create a user

        If a user is created, they are not guaranteed to have any kind of
        privileges and/or access permissions on the :ref:`SOC Automation
        Server`.

        When data is maintained using background processes, it is not
        always obvious who the responsible user is.

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


class BaseModelWithDefaultInstance(BaseModel, models.Model):
    """
    Abstract model class that extends :class:`BaseModel` with support for
    a default instance

    A default instance is the most used instance in a (non-abstract)
    :class:`model <django.db.models.Model>`. A :class:`model
    <django.db.models.Model>` can only have one default instance. It is
    acceptable to have :class:`models <django.db.models.Model>` inheriting
    from this class that do not have a default instance.
    """
    is_default = models.BooleanField(
        _('Default Instance'),
        db_index=True, blank=False, null=False, default=False,
        help_text=_(
            'If set, then this row will be preferred by the application.'
            ' Note there can only be one default row in the table.'))
    """
    if this field is set to `True` in a :class:`model
    <django.db.models.Model>` inheriting from this class, the instance
    containing the field is considered to be the `default` instance
    """

    def clean(self):
        """
        override :meth:`django.db.models.Model.clean` to
        make sure that only one instance is the default instance

        The default/non-default state of an instance is tracked using the
        :attr:`is_default` attribute. This method is looking through all
        the saved instances and is raising an error if there already
        is a default instance present in the model.

        :raises: :exc:`django.core.exceptions.ValidationError`
        """
        if not self.is_default:
            return

        if self._meta.model.objects.filter(is_default=True).\
                exclude(pk=self.pk).exists():
            raise ValidationError(
                {'is_default': _('A default %s already exists'
                                 % self._meta.model_name.title())}
            )

        return

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        """
        override :meth:`django.db.models.Model.save` to invoke
        :meth:`django.db.models.Model.full_clean`, otherwise the
        :meth:`clean` will not be invoked.
        """
        try:
            self.full_clean()
        except ValidationError as error:
            raise error

        super().save(*args, **kwargs)

    @classmethod
    def get_default(cls):
        """
        get the default instance for this model

        :returns: the id of the default instance of this model or `None`
        """
        if not hasattr(cls, 'objects'):
            return None

        try:
            return cls.objects.filter(is_default=True).get().id
        except cls.DoesNotExist:
            return None

    class Meta:
        abstract = True
