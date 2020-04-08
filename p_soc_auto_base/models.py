"""
.. _base_models:

Django models for the base app

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

Abstract base model classes
"""
__updated__ = '2018_08_08'

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class EnabledManager(models.Manager):
    """
    Manager that only returns `active` objects.
    """
    def get_queryset(self):
        """
        override :meth:`models.Manager.get_queryset` to only return objects
        which are enabled.

        :return: all objects that are enabled.
        """
        return super().get_queryset().filter(enabled=True)


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

    # TODO why is this here?
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

    objects = models.Manager()
    """
    Default manager.

    Note first defined manager is always set as default, to ensure default is 
    'all objects' this manager should remain defined first.
    """

    active = EnabledManager()
    """
    Manager that only returns objects that are currently active.

    This manager should be used for most non-administrative tasks.
    """

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
        self.full_clean()

        super().save(*args, **kwargs)

    @classmethod
    def default(cls):
        """
        get the default instance for this model

        :returns: the default instance of this model or `None`
        """
        if not hasattr(cls, 'objects'):
            return None

        try:
            return cls.objects.filter(is_default=True).get()
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_default(cls):
        """
        Get the id for the default instance for this model

        Many models point to this as their 'default' for foreign keys, hence it
        must return an int. Refactoring to make a more clear distinction
        between this and default would require resetting all of those defaults.

        :returns: the default instance id of this model or `None`
        """
        try:
            return cls.default().id
        except AttributeError:
            return None

    class Meta:
        abstract = True


class Subscription(BaseModel):
    """
    Data model with all the details required to create and send an email
    message

    This :class:`django.db.models.Model` is used across all the applications
    running on the :ref:`SOC Automation Server`.
    """
    subscription = models.CharField('subscription', max_length=128, unique=True,
        db_index=True, blank=False, null=False)
    """
    string uniquely identifying a :class:`Subscription` instance
    """

    emails_list = models.TextField('subscribers', blank=False, null=False)
    """
    comma-separated string with the email addresses to which the email will be
    sent
    """

    from_email = models.CharField('from', max_length=255, blank=True, null=True,
        default=settings.DEFAULT_FROM_EMAIL)
    """
    email address to be placed in the `FROM` email header; default will be
    picked from :attr:`p_soc_auto.settings.DEFAULT_FROM_EMAIL`
    """

    template_dir = models.CharField('email templates directory', max_length=255,
        blank=False, null=False)
    """
    directory for `Templates
    <https://docs.djangoproject.com/en/2.2/topics/templates/>`_

    In most cases this is an `application_directory/templates/` directory.
    """

    template_name = models.CharField('email template name', max_length=64,
        blank=False, null=False)
    """
    the short name of the template file used to render this type of email

    The extension is picked from the configuration of the
    `django-templated-mail` package in `p_soc_auto.settings`.
    """

    template_prefix = models.CharField('email template prefix', max_length=64,
        blank=False, null=False, default='email/')
    """
    the subdirectory under :attr:`templatedir` where email templates are
    located
    """

    email_subject = models.TextField('email subject fragment', blank=True,
        null=True,
        help_text=('this is the conditional subject of the email template.'
                   ' it is normally just a fragment that will augmented'
                   ' by other variables'))
    """
    the strings to be used as the core of the email subject line

    The application will most probably prepend and/or append various other
    strings to the subject line.

    There is no limit on the length of the subject line but in this application
    but according to `RFC 2822
    <http://www.faqs.org/rfcs/rfc2822.html>`_, section 2.1.1, this field must
    not be longer than 998 characters, and should not be longer than
    78 characters (we are nowhere near respecting the later).

    This value is used as an email subject line only if the rendering template
    is invoked with a `context
    <https://docs.djangoproject.com/en/2.2/ref/templates/api/#rendering-a
    -context>`_
    that includes a reference to it.
    """

    alternate_email_subject = models.TextField('fallback email subject',
        blank=True, null=True,
        help_text='this is the non conditional subject of the email template.')
    """
    an alternate value for the core of the email subject line

    This value is subject to the same rules as :attr:`email_subject`.

    We include this value because in some cases the same template will render
    with different subject lines based on various conditions. E.g. if the
    :attr:`data is not ``None``, the subject line will include some references
    to the its content, otherwise the subject line would be like 'Move along,
    nothing to see here'.
    """

    headers = models.TextField('data headers', blank=False, null=False,
        default='common_name,expires_in,not_before,not_after')
    """
    a comma-separated list of field names to retrieve from the :attr:`data`
    `queryset`

    Note that if there are field names listed here that don't exist in the
    :attr:`data` `queryset` they will not be displayed.
    """

    tags = models.TextField('tags', blank=True, null=True,
        help_text=('email classification tags placed on the subject line'
                   ' and in the email body'))
    """
    a string af tags that will be pre-pended to the email subject line

    The application will not do any processing on this value. If one expects
    tags to look like [TAG1][TAG2], this value must be created using this
    pattern.
    """

    def __str__(self):
        return self.subscription

    class Meta:
        app_label = 'p_soc_auto_base'
