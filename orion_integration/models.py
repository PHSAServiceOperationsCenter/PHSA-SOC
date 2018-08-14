"""
.. _models:

django models for the orion_integration app

:module:    p_soc_auto.orion_integration.models

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca
"""
__updated__ = '2018_08_08'

from django.apps import apps
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from p_soc_auto_base.models import BaseModel

from .orion import OrionClient


class OrionQueryError(Exception):
    """
    raise if the model doesn't have an orion_query attribute
    """
    pass


class OrionMappingsError(Exception):
    """
    raise if the model doesn't have an orion_mappings attribute
    """
    pass


class OrionBaseModel(BaseModel, models.Model):
    """
    most (if not all) Orion objects need an orion_id key that comes from the
    Orion server

    then we also need the fields from the BaseModel; let's use this as the
    base class for all the models here
    """
    orion_query = None
    orion_mappings = None

    orion_id = models.BigIntegerField(
        _('Orion Object Id'), db_index=True, unique=True, blank=False,
        help_text=_(
            'Use the value in this field to query the Orion server'))

    @classmethod
    def update_or_create_from_orion(cls, username=settings.ORION_USER):
        """
        class method to update or create orion model instances

        update or create entries in orion models using data from the Orion
        server

        :arg cls: the model class

            note that this method is defined in a base class so that it can
            be invoked from all the classes inheriting form that particular
            base class

            see notes about :var:`orion_query` and :var:`orion_mappings`. this
            method expects that the classes supporting it have those variables
            defined

        :raises:

            :exception:`OrionQueryError` if :var:`orion_query` is not
            defined in the calling model

            :exception:`OrionMappnngsError` if :var:`orion_mappings` is not
            defined in the calling class
        """
        if cls.orion_query is None:
            raise OrionQueryError(
                _('%s is not providing a value for the Orion query'
                  % cls._meta.label))

        if cls.orion_mappings is None:
            raise OrionMappingsError(
                _('%s is not providing a value for the Orion mappings'
                  % cls._meta.label))

        user = cls.get_or_create_user(username)
        data = OrionClient.populate_from_query(cls)
        for data_item in data:
            orion_mapping = dict()
            for mapping in cls.orion_mappings:
                if mapping[2] is None:
                    orion_mapping[mapping[0]] = data_item[mapping[1]]
                else:
                    app, model = mapping[2].split('.')
                    model = apps.get_model(app, model)
                    orion_mapping[mapping[0]] = model.objects.filter(
                        orion_id__exact=data_item[mapping[1]]).get()

            orion_mapping.update(updated_by=user, created_by=user)
            try:
                qs = cls.objects.filter(
                    orion_id__exact=orion_mapping['orion_id'])
                if qs.exists():
                    orion_mapping.pop('orion_id')
                    orion_mapping.pop('created_by', None)

                    qs.update(**orion_mapping)
                else:
                    cls.objects.update_or_create(**orion_mapping)
            except Exception as err:
                print('%s when acquiring Orion object %s' %
                      (str(err), orion_mapping))

    class Meta:
        abstract = True


class OrionNode(OrionBaseModel, models.Model):
    """
    reference:
    `Orion Node<http://solarwinds.github.io/OrionSDK/schema/Orion.Nodes.html>`_

    """
    #: the Orion query used to populate this model
    orion_query = (
        'SELECT NodeID, ObjectSubType, IPAddress, Caption, NodeDescription,'
        ' Description, DNS,Category, Vendor, Location, Status,'
        ' StatusDescription, MachineType, NodeName, DetailsUrl'
        ' FROM Orion.Nodes')
    #: mapping between model fields and data returned by the Orion query
    #: must be a 3 variables tuple: the first variable is the name of the
    #: field, the second variable is the name of the column in the Orion
    #: schema, and the third column describes a foreign key mapping
    #: if necessary; it is formatted as app_lable.ModelName and it will
    #: prepare a Model.objects.filter().get() to retrieve the foreign key
    orion_mappings = (('orion_id', 'NodeID', None),
                      ('node_caption', 'Caption', None),
                      ('sensor', 'ObjectSubType', None),
                      ('category', 'Category',
                       'orion_integration.OrionNodeCategory'),
                      ('ip_address', 'IPAddress', None),
                      ('node_name', 'NodeDescription', None),
                      ('notes', 'Description', None),
                      ('node_dns', 'DNS', None),
                      ('vendor', 'Vendor', None),
                      ('location', 'Location', None),
                      ('machine_type', 'MachineType', None),
                      ('status_orion_id', 'Status', None),
                      ('status', 'StatusDescription', None),
                      ('details_url', 'DetailsUrl', None))
    node_caption = models.CharField(
        _('Node Caption'), db_index=True,  blank=False,
        max_length=254, null=False)
    category = models.ForeignKey(
        'OrionNodeCategory', on_delete=models.PROTECT,
        verbose_name=_('Orion Node Category'))
    sensor = models.CharField(
        _('Sensor'), db_index=True, blank=False, null=False, max_length=16,
        default='ICMP', help_text=_('Maps to Orion.Nodes.ObjectSubtype'))
    ip_address = models.GenericIPAddressField(
        _('IP Address'), db_index=True, blank=False, null=False,
        protocol='IPv4')
    node_name = models.TextField(
        _('Node Name'), blank=False, null=False)
    node_dns = models.CharField(
        _('DNS'), db_index=True, blank=False, null=False, max_length=254)
    node_description = models.TextField(_('Orion Node Description'))
    vendor = models.CharField(
        _('Vendor'), db_index=True, blank=True, null=True, max_length=254)
    location = models.CharField(
        _('Location'), db_index=True, blank=True, null=True, max_length=254)
    machine_type = models.CharField(
        _('Machine Type'), db_index=True, blank=True, null=True,
        max_length=254, help_text=_('this needs to become a foreign key'))
    status = models.CharField(
        _('Node Status'), max_length=254, db_index=True,
        blank=False, null=False)
    status_orion_id = models.BigIntegerField(
        _('Orion Node Status Id'), db_index=True, blank=False, default=0,
        help_text=_(
            'This will probably changes but that is how they do it for the'
            ' moment; boohoo'))
    details_url = models.TextField(
        _('Node Details URL'), blank=True, null=True)

    @classmethod
    def update_or_create_from_orion(cls):
        """
        override :method:`OrionBaseModel.update_or_create_from_orion` to make
        sure that the foreign keys are already available in
        :class:`OrionNodeCategory`
        """
        if not OrionNodeCategory.objects.count():
            OrionNodeCategory.update_or_create_from_orion()
        super(OrionNode, cls).update_or_create_from_orion()

    class Meta:
        app_label = 'orion_integration'
        verbose_name = 'Orion Node'
        verbose_name_plural = 'Orion Nodes'


class OrionNodeCategory(OrionBaseModel, models.Model):
    """
    query:
    SELECT Description FROM Orion.NodeCategories
    """
    orion_query = 'SELECT CategoryID, Description FROM Orion.NodeCategories'
    orion_mappings = (('orion_id', 'CategoryID', None),
                      ('category', 'Description', None))
    category = models.CharField(
        _('Orion Node Category'), db_index=True, unique=True, null=False,
        blank=False, max_length=254, help_text=_(
            'Orion Node Category Help'))

    class Meta:
        app_label = 'orion_integration'
        verbose_name = _('Orion Node Category')
        verbose_name_plural = _('Orion Node Categories')


class OrionAPMApplication(OrionBaseModel, models.Model):
    """
    Application monitored by Orion
    """
    orion_query = (
        'SELECT ApplicationID, Name, NodeID, DetailsUrl, FullyQualifiedName,'
        ' Description, Status, StatusDescription FROM Orion.APM.Application')
    orion_mappings = (('orion_id', 'ApplicationID', None),
                      ('application_name', 'Name', None),
                      ('node', 'NodeID', 'orion_integration.OrionNode'),
                      ('details_url', 'DetailsUrl', None),
                      ('full_name', 'FullyQualifiedName', None),
                      ('notes', 'Description', None),
                      ('status_orion_id', 'Status', None),
                      ('status', 'StatusDescription', None))

    application_name = models.CharField(
        _('Application Name'), max_length=254, db_index=True, blank=False,
        null=False, help_text=_(
            'The application name as reported by Orion.APM.Application'))
    node = models.ForeignKey(
        'OrionNode', on_delete=models.CASCADE, verbose_name=_('Orion Node'),
        help_text=_('The node where the application is running'))
    details_url = models.TextField(
        _('Application Details URL'), blank=True, null=True)
    full_name = models.TextField(
        _('Application Fully Qualified Name'), blank=True, null=True)
    status = models.CharField(
        _('Node Status'), max_length=254, db_index=True,
        blank=False, null=False)
    status_orion_id = models.BigIntegerField(
        _('Orion Node Status Id'), db_index=True, blank=False, default=0,
        help_text=_(
            'This will probably changes but that is how they do it for the'
            ' moment; boohoo'))

    @classmethod
    def update_or_create_from_orion(cls):
        """
        override :method:`OrionBaseModel.update_or_create_from_orion` to make
        sure that the foreign keys are already available in
        :class:`OrionNodeCategory`
        """
        if not OrionNode.objects.count():
            OrionNode.update_or_create_from_orion()
        super(OrionAPMApplication, cls).update_or_create_from_orion()

    class Meta:
        app_label = 'orion_integration'
        verbose_name = 'Orion Application'
        verbose_name_plural = 'Orion Applications'
