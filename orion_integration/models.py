"""
orion_integration.models
------------------------

This module contains the :class:`django.db.models.Model` models for the
:ref:`Orion Integration Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Nov. 5, 2019

"""
import logging

from django.apps import apps
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from citrus_borg.dynamic_preferences_registry import get_preference
from p_soc_auto_base.models import BaseModel

from .orion import OrionClient


LOGGER = logging.getLogger('orion_integration_log')

# pylint:disable=R0903


class OrionCernerCSTNodeManager(models.Manager):
    """
    `Custom manager
    <https://docs.djangoproject.com/en/2.2/topics/db/managers/#custom-managers>`_
    class used in the :class:`OrionCernerCSTNode` model
    """

    def get_queryset(self):
        """
        override :meth:`django.db.models.Manager.get_queryset`

        See `Modifying a manager's initial QuerySet
        <https://docs.djangoproject.com/en/2.2/topics/db/managers/#modifying-a-manager-s-initial-queryset>`__
        in the `Django` docs.

        :returns: a :class:`django.db.models.query.QuerySet` with the
            :class:`OrionNode` instances that map to `Orion` nodes tagged as
            `Cerner-CST` nodes


        """
        return super().\
            get_queryset().filter(
                program_application__exact=get_preference(
                    'orionfilters__cerner_cst'))


class OrionDomainControllerNodeManager(models.Manager):
    """
    `Custom manager
    <https://docs.djangoproject.com/en/2.2/topics/db/managers/#custom-managers>`_
    class used in the :class:`OrionDomainControllerNode` model
    """

    def get_queryset(self):
        """
        override :meth:`django.db.models.Manager.get_queryset`

        See `Modifying a manager's initial QuerySet
        <https://docs.djangoproject.com/en/2.2/topics/db/managers/#modifying-a-manager-s-initial-queryset>`__
        in the `Django` docs.

        :returns: a :class:`django.db.models.query.QuerySet` with the
            :class:`OrionNode` instances that are `Windows domain
            controllers`

        """
        return OrionNode.objects.\
            filter(program_application_type=get_preference(
                'orionfilters__domaincontroller')).\
            exclude(enabled=False)

# pylint:enable=R0903


class OrionQueryError(Exception):
    """
    Custom :exc:`Exception` raised if a :class:`django.db.models.Model` that
    inherits from :class:`OrionBaseModel` model doesn't have an
    :attr:`orion_query` attribute

    The :attr:`orion_query` attribute is the `SWQL query
    <https://support.solarwinds.com/SuccessCenter/s/article/Use-SolarWinds-Query-Language-SWQL>`__
    that is used when populating and/or maintaining the model.

    """


class OrionMappingsError(Exception):
    """
    Custom :exc:`Exception` raised if a :class:`django.db.models.Model` that
    inherits from :class:`OrionBaseModel` model doesn't have an
    :attr:`orion_mappings` attribute

    The :attr:`orion_mappings` attribute is used for mapping the fields
    returned by an `SWQL query
    <https://support.solarwinds.com/SuccessCenter/s/article/Use-SolarWinds-Query-Language-SWQL>`__
    to the fields of the model.
    """


class OrionBaseModel(BaseModel, models.Model):
    """
    :class:`django.db.models.Model` base class for other `Model` classes in
    this module

    """
    orion_query = None
    """
    place-holder for the `SWQL query
    <https://support.solarwinds.com/SuccessCenter/s/article/Use-SolarWinds-Query-Language-SWQL>`__
    used for populating and/or maintaining the `model`
    """

    orion_mappings = []
    """
    place-holder for the mapping between the fields returned by an `SWQL query
    <https://support.solarwinds.com/SuccessCenter/s/article/Use-SolarWinds-Query-Language-SWQL>`__
    and the fields of the model
    """

    orion_id_query = None
    """
    place-holder for the `SWQL query
    <https://support.solarwinds.com/SuccessCenter/s/article/Use-SolarWinds-Query-Language-SWQL>`__
    used for querying the `Orion` server about a known `model` instance
    """

    orion_id = models.BigIntegerField(
        _('Orion Object Id'), db_index=True, unique=True, blank=False,
        help_text=_(
            'Use the value in this field to query the Orion server'))
    not_seen_since = models.DateTimeField(
        _('Not Seen Since'), db_index=True, blank=True, null=True,
        help_text=_(
            'populated if this Orion entity is not available anymore on'
            ' the Orion server'))

    def exists_in_orion(self):
        """
        verify that the `Orion` entity instance still matches on entity on the
        `Orion` server

        If the entity is present on the Orion server, reset the
        `not_seen_since` field and return `True`

        Otherwise, this method will try to delete the local entity and return
        `False`.

        :returns: `True` or `False`
        :rtype: bool

        :raises: :exc:`Exception` if the instance cannot be deleted

        """
        data = OrionClient.query(orion_query='%s = %s' % (self.orion_id_query,
                                                          self.orion_id))

        if data:
            self.not_seen_since = None
            self.save()
            return True

        try:
            self.delete()
        except Exception as error:  # pylint: disable=broad-except
            LOGGER.exception(str(error))

        LOGGER.info('removed orion entity %s. not found in Orion',
                    self.orion_id)

        return False

    # pylint:disable=R0914
    @classmethod
    def update_or_create_from_orion(cls, username=settings.ORION_USER):
        """
        update or create instances of :class:`django.db.models.Model` classes
        inheriting from this class using data from the `Orion`  server

        :arg str username: the :attr:`username` of the
            :class:`django.contrib.auth.models.User` instance when creating the
            model instance

            .. todO::

                We are picking the default value for this argument from the
                `Djanog` `settings` file. We need to use a dynamic preference
                instead.

        :raises:

            :exc:`OrionQueryError` if the :attr:`orion_query` attribute is not
            defined in the model

            :exc:`OrionMappingsError` if the :attr:`orion_mappings` attribute
            is not defined in the model

        :returns: a :class:`dictionary <dict>` with these keys

            * status

            * model: the `model` that executed this method

            * orion_rows: the number of rows returned by the `Orion` `REST`
              call

            * updated_records: the number of objects that have been updated
              during the `Orion` `REST` call

            * created_records: the number of objects that have been created
              during the `Orion` `REST` call

            * errored_records: the number of objects that threw an error
              during the `Orion` `REST` call
        """
        return_dict = dict(
            status='pending', model=cls._meta.verbose_name, orion_rows=0,
            updated_records=0, created_records=0, errored_records=0)
        if cls.orion_query is None:
            raise OrionQueryError(
                '%s is not providing a value for the Orion query'
                % cls._meta.label)

        if not cls.orion_mappings:
            raise OrionMappingsError(
                '%s is not providing a value for the Orion mappings'
                % cls._meta.label)

        user = cls.get_or_create_user(username)
        data = OrionClient.query(orion_query=cls.orion_query)
        return_dict['status'] = 'in progress'
        return_dict['orion_rows'] = len(data)
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
                    return_dict['updated_records'] += 1

                    # we do not want to use qs.update(88orion_mapping) because
                    # it bypasses the pre- and post-save signals
                    # thus, setattr in a loop
                    instance = qs.get()
                    for attr, value in orion_mapping.items():
                        setattr(instance, attr, value)

                else:
                    # it is a new instance
                    return_dict['created_records'] += 1
                    instance = cls(**orion_mapping)

                instance.save()

            except Exception as err:    # pylint:disable=W0703
                return_dict['errored_records'] += 1
                print('%s when acquiring Orion object %s' %
                      (str(err), orion_mapping))

        return_dict['status'] = 'done'

        return return_dict
    # pylint:enable=R0914

    class Meta:
        abstract = True


class OrionNode(OrionBaseModel, models.Model):
    """
    :class:`django.db.models.Model` class with the representation of a node
    on the `Orion` server

    The reference for `Orion` nodes: `Orion Node
    <http://solarwinds.github.io/OrionSDK/schema/Orion.Nodes.html>`__

    """
    orion_id_query = ('SELECT NodeID FROM Orion.Nodes WHERE NodeID')
    """
    the `SWQL query
    <https://support.solarwinds.com/SuccessCenter/s/article/Use-SolarWinds-Query-Language-SWQL>`__
    used for verifying that an instance of this
    :class:`django.db.models.Model` model matches an `Orion` node
    """

    orion_query = (
        'SELECT ons.NodeID, ons.ObjectSubType, ons.IPAddress, ons.Caption,'
        ' ons.NodeDescription, ons.Description, ons.DNS, ons.Category,'
        ' ons.Vendor, ons.Location, ons.Status, ons.StatusDescription,'
        ' ons.MachineType, ons.NodeName, ons.DetailsUrl,'

        ' oncp.Address, oncp.Building, oncp.City, oncp.Closet, oncp.Comments,'
        ' oncp.DeviceType, oncp.HA, oncp.HardwareIncidentStatus,'
        ' oncp.IncidentStatus, oncp.Make, oncp.NodeOwner, oncp.OutOfBand,'
        ' oncp.ProgramApplication, oncp.ProgramApplicationType,'
        ' oncp.Provider, oncp.Region, oncp.Site, oncp.SiteContactName,'
        ' oncp.SiteHours, oncp.SitePhone, oncp.SiteType,'
        ' oncp.WANbandwidth, oncp.WANnode, oncp.WANProvider'
        ' FROM Orion.Nodes(nolock=true) ons'
        ' LEFT JOIN Orion.NodesCustomProperties(nolock=true) oncp'
        ' on ons.NodeID = oncp.NodeID'
    )
    """
    the `SWQL query
    <https://support.solarwinds.com/SuccessCenter/s/article/Use-SolarWinds-Query-Language-SWQL>`__
    used for creating or maintaining an instance of this
    :class:`django.db.models.Model` model from an `Orion` node
    """

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
                      ('details_url', 'DetailsUrl', None),
                      ('address', 'Address', None),
                      ('building', 'Building', None),
                      ('city', 'City', None),
                      ('closet', 'Closet', None),
                      ('comments', 'Comments', None),
                      ('device_type', 'DeviceType', None),
                      ('ha', 'HA', None),
                      ('hardware_incident_status', 'HardwareIncidentStatus',
                       None),
                      ('incident_status', 'IncidentStatus', None),
                      ('make', 'Make', None),
                      ('node_owner', 'NodeOwner', None),
                      ('out_of_band', 'OutOfBand', None),
                      ('program_application', 'ProgramApplication', None),
                      ('program_application_type', 'ProgramApplicationType',
                       None),
                      ('provider', 'Provider', None),
                      ('region', 'Region', None),
                      ('site', 'Site', None),
                      ('site_contact_name', 'SiteContactName', None),
                      ('site_hours', 'SiteHours', None),
                      ('site_phone', 'SitePhone', None),
                      ('site_type', 'SiteType', None),
                      ('wan_bandwidth', 'WANbandwidth', None),
                      ('wan_node', 'WANnode', None),
                      ('wan_provider', 'WANProvider', None))
    """
    mapping between this `model's` fields and data returned by the `SWQL query
    <https://support.solarwinds.com/SuccessCenter/s/article/Use-SolarWinds-Query-Language-SWQL>`__

    This attribute is a :class:`tuple` where each item represents a `model`
    field.
    Each item of the :class:`tuple` above is also a :class:`tuple` that
    contains 3 variables:

    * The first variable is the name of the :class:`model
      <django.db.models.Model>` field

    * The second variable is the name of the column in the `Orion Node schema
      <http://solarwinds.github.io/OrionSDK/schema/Orion.Nodes.html>`__.

      It is possible to mix schemas for multiple `Orion` related entities,
      e.g. `Orion Node
      <http://solarwinds.github.io/OrionSDK/schema/Orion.Nodes.html>`__ and
      `Orion Node Custom Properties
      <https://solarwinds.github.io/OrionSDK/schema/Orion.NodesCustomProperties.html>`__

    * The third column is used when the :class:`django.db.models.Model` field
      is a :class:`django.db.models.ForeignKey` field and it describes the
      `Related object
      <https://docs.djangoproject.com/en/2.2/topics/db/queries/#related-objects>`__
      using the `app_label.ModelName` convention

    """

    address = models.CharField(
        _('Address'), db_index=True, blank=True, max_length=254, null=True)
    building = models.CharField(
        _('Building'), db_index=True, blank=True, max_length=254, null=True)
    city = models.CharField(
        _('City'), db_index=True, blank=True, max_length=64, null=True)
    closet = models.CharField(
        _('Closet'), db_index=True, blank=True, max_length=254, null=True)
    comments = models.TextField(_('Comments'), blank=True, null=True)
    device_type = models.CharField(
        _('Device Type'), db_index=True, blank=True, max_length=64,
        null=True)
    ha = models.CharField(
        _('HA'), db_index=True, blank=True, max_length=32, null=True)
    hardware_incident_status = models.TextField(
        _('Hardware Incident Status'), blank=True, null=True)
    incident_status = models.TextField(
        _('Incident Status'), blank=True, null=True)
    make = models.CharField(
        _('Make'), db_index=True, blank=True, max_length=254, null=True)
    node_owner = models.CharField(
        _('Node Owner'), db_index=True, blank=True, max_length=254,
        null=True)
    out_of_band = models.CharField(
        _('out of band'), max_length=64, blank=True, null=True)
    program_application = models.CharField(
        _('program application'), db_index=True, blank=True, max_length=254,
        null=True)
    program_application_type = models.CharField(
        _('program application type'), db_index=True, blank=True,
        max_length=64, null=True)
    provider = models.CharField(
        _('provider'), db_index=True, blank=True,
        max_length=64, null=True)
    region = models.CharField(
        _('region'), db_index=True, blank=True,
        max_length=64, null=True)
    site = models.CharField(
        _('site'), db_index=True, blank=True, max_length=254,
        null=True)
    site_contact_name = models.CharField(
        _('site contact name'), db_index=True, blank=True, max_length=254,
        null=True)
    site_hours = models.CharField(
        _('site hours'), db_index=True, blank=True, max_length=254,
        null=True)
    site_phone = models.CharField(
        _('site phone'), db_index=True, blank=True, max_length=32,
        null=True)
    site_type = models.CharField(
        _('site type'), db_index=True, blank=True, max_length=32,
        null=True)
    wan_bandwidth = models.CharField(
        _('WAN bandwidth'), db_index=True, blank=True, max_length=32,
        null=True)
    wan_node = models.CharField(
        _('WAN node'), db_index=True, blank=True, max_length=32,
        null=True)
    wan_provider = models.CharField(
        _('WAN provider'), db_index=True, blank=True, max_length=254,
        null=True)
    node_caption = models.CharField(
        _('Node Caption'), db_index=True, blank=False,
        max_length=254, null=False)
    category = models.ForeignKey(
        'OrionNodeCategory', on_delete=models.CASCADE,
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
        _('DNS'), db_index=True, blank=True, null=True, max_length=254)
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
    def update_or_create_from_orion(cls):  # pylint:disable=W0221
        """
        overrides the :meth:`OrionBaseModel.update_or_create_from_orion`
        method to make sure that the `Related objects
        <https://docs.djangoproject.com/en/2.2/topics/db/queries/#related-objects>`__
        required for creating the instance are already available in
        :class:`OrionNodeCategory`

        This method basically calls a chain of
        :meth:`OrionBaseModel.update_or_create_from_orion`, one for each
        model required for referential integrity

        :returns: a list of the return results for each call in the chain
        :rtype: list
        """
        ret = []
        if not OrionNodeCategory.objects.count():
            result = OrionNodeCategory.update_or_create_from_orion()
            ret.append(result)

        result = super(OrionNode, cls).update_or_create_from_orion()
        ret.append(result)

        return ret

    def __str__(self):
        return self.node_caption

    class Meta:
        app_label = 'orion_integration'
        verbose_name = _('Orion Node')
        verbose_name_plural = _('Orion Nodes')


class OrionCernerCSTNode(OrionNode):
    """
    Proxy `model` to show just the `Cerner CST` nodes

    see `Django proxy models
    <https://docs.djangoproject.com/en/2.2/topics/db/models/#proxy-models>`__
    """
    objects = OrionCernerCSTNodeManager()

    class Meta:
        proxy = True
        verbose_name = _('Orion Cerner CST Node')
        verbose_name_plural = _('Orion Cerner CST Nodes')


class OrionDomainControllerNode(OrionNode):
    """
    Proxy `model` to show just the `Windows domain controller` `Orion` nodes
    that are `enabled`

    see `Django proxy models
    <https://docs.djangoproject.com/en/2.2/topics/db/models/#proxy-models>`__
    """
    objects = OrionDomainControllerNodeManager()

    class Meta:
        proxy = True
        verbose_name = _('Windows domain controller')
        verbose_name_plural = _('Windows domain controllers')


class OrionNodeCategory(OrionBaseModel, models.Model):
    """
    :class:`django.db.models.Model` class with the representation of node
    categories on the `Orion` server

    The reference for `Orion` nodes: `Orion Node Categories
    <http://solarwinds.github.io/OrionSDK/schema/Orion.NodeCategories.html>`__

    """
    orion_id_query = (
        'SELECT CategoryID FROM Orion.NodeCategories WHERE CategoryID'
    )
    """
    the `SWQL` query for verifying that there is a matching category on the
    `Orion` server
    """

    orion_query = 'SELECT CategoryID, Description FROM Orion.NodeCategories'
    """
    the `SWQL` query used to populate this `model` from the `Orion` server
    """

    orion_mappings = (('orion_id', 'CategoryID', None),
                      ('category', 'Description', None))
    """
    mapping between this `model's` fields and data returned by the `SWQL` query
    """
    category = models.CharField(
        _('Orion Node Category'), db_index=True, unique=True, null=False,
        blank=False, max_length=254, help_text=_(
            'Orion Node Category Help'))

    def __str__(self):
        """
        return something meaningful
        """
        return self.category

    class Meta:
        app_label = 'orion_integration'
        verbose_name = _('Orion Node Category')
        verbose_name_plural = _('Orion Node Categories')


class OrionAPMApplication(OrionBaseModel, models.Model):
    """
    :class:`django.db.models.Model` class with the representation of
    applications on the `Orion` server. See `Server & Application Monitor
    <https://www.solarwinds.com/server-application-monitor>`__

    In our particular case, this structure contains data for isolating `Orion`
    nodes that provide services over `SSL` (which, admittedly, is not how
    the `Orion APM module
    <https://www.solarwinds.com/server-application-monitor>`__ should be used.
    After all, `SSL` is protocol, not an application.).

    The schema reference for the `Orion APM Application` component is
    available at `Orion.APM.Application
    <https://solarwinds.github.io/OrionSDK/schema/Orion.APM.Application.html>`__.

    """
    orion_id_query = (
        'SELECT ApplicationID FROM Orion.APM.Application WHERE ApplicationID'
    )
    """
    the `SWQL` query for verifying that there is a matching application on the
    `Orion` server
    """

    orion_query = (
        'SELECT ApplicationID, Name, NodeID, DetailsUrl, FullyQualifiedName,'
        ' Description, Status, StatusDescription FROM Orion.APM.Application'
    )
    """
    the `SWQL` query used to populate this `model` from the `Orion` server
    """

    orion_mappings = (('orion_id', 'ApplicationID', None),
                      ('application_name', 'Name', None),
                      ('node', 'NodeID', 'orion_integration.OrionNode'),
                      ('details_url', 'DetailsUrl', None),
                      ('full_name', 'FullyQualifiedName', None),
                      ('notes', 'Description', None),
                      ('status_orion_id', 'Status', None),
                      ('status', 'StatusDescription', None))
    """
    mapping between this `model's` fields and data returned by the `SWQL` query
    """

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
    def update_or_create_from_orion(cls):  # pylint:disable=W0221
        """
        overrides the :meth:`OrionBaseModel.update_or_create_from_orion`
        method to make sure that the `Related objects
        <https://docs.djangoproject.com/en/2.2/topics/db/queries/#related-objects>`__
        required for creating the instance are already available in
        :class:`OrionNode`

        :returns: a list of the return results for each call in the chain
        :rtype: list

        """
        ret = []
        if not OrionNode.objects.count():
            result = OrionNode.update_or_create_from_orion()
            ret.append(result)

        result = super(OrionAPMApplication, cls).update_or_create_from_orion()
        ret.append(result)

        return ret

    class Meta:
        app_label = 'orion_integration'
        verbose_name = 'Orion Application'
        verbose_name_plural = 'Orion Applications'
