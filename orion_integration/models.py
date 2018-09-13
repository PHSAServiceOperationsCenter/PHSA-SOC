"""
.. _models:

django models for the orion_integration app

:module:    p_soc_auto.orion_integration.models

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

"""
from django.apps import apps
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from p_soc_auto_base.models import BaseModel

from .orion import OrionClient

# pylint:disable=R0903


class OrionCernerCSTNodeManager(models.Manager):
    """
    django custom manager that adds a filter on Cerner-CST by default
    """

    def get_queryset(self):
        """
        override the default get_queryset() method

        when using `django.queryset.objects` this method makes sure
        that a filter is applied without having to explicitly call
        :method:`django.queryset.filter`
        """
        return super().\
            get_queryset().filter(program_application__exact='Cerner-CST')
# pylint:enable=R0903


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
    use this class as the parent for all the models that are caching Orion
    entities

    most (if not all) Orion objects need an orion_id key that comes from the
    Orion server; this class provides that field
    """
    orion_query = None
    orion_mappings = []
    orion_id_query = None

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
        is this orion entity instance still available on the orion server?

        if the entity is present on the Orion server, just return

        if this is the first time the orion entity is not available on the
        Orion server, set the :var:`not_seen_since` to
        ``django.utils.timezone.now``.

        if this is not the first time the entity has not been seen, return

        if the orion entity is seen again, reset the :var:`not_seen_since`
        to ``None``

        uses an orion query looking for the orion entity identified by
        the :var:`orion_id.` value of the instance. the query needs to be
        defined in :var:`orion_id_query`

        :returns: a ``tuple`` with the first member being "exists" or
                  "not seen since: :attr:`not_seen_since`" and the
                  instance ``values_list``

        """
        data = OrionClient.query(orion_query='%s = %s' % (self.orion_id_query,
                                                          self.orion_id))

        if data:
            self.not_seen_since = None
            self.save()
            return ('exists',
                    list(self._meta.model.objects.
                         filter(pk=self.pk).values_list()))

        if not self.not_seen_since:
            self.not_seen_since = timezone.now()
            self.save()

        return ('not seen since: %s' % self.not_seen_since,
                list(self._meta.model.objects.
                     filter(pk=self.pk).values_list()))

    # pylint:disable=R0914
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

        :returns: a ``dict`` with these keys
                :key status:
                :key model:
                :key orion_rows: the number of rows returned by the Orion call
                :key updated_records: the number of objects that have been
                                      updated during the Orion call
                :key created_records: the number of objects that have been
                                      created during the Orion call
                :key errored_records: the number of objects that
                                      threw an error during the Orion call
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

                    qs.update(**orion_mapping)
                else:
                    _, created = cls.objects.update_or_create(
                        **orion_mapping)
                    if created:
                        return_dict['created_records'] += 1
                    else:
                        return_dict['updated_records'] += 1
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
    reference:
    `Orion Node<http://solarwinds.github.io/OrionSDK/schema/Orion.Nodes.html>`_

    """
    #: the Orion query to verify if objects from this model exist in Orion
    orion_id_query = ('SELECT NodeID FROM Orion.Nodes WHERE NodeID')

    #: the Orion query used to populate this model
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
    def update_or_create_from_orion(cls):  # pylint:disable=W0221
        """
        override :method:`OrionBaseModel.update_or_create_from_orion` to make
        sure that the foreign keys are already available in
        :class:`OrionNodeCategory`

        this basically calls a chain of
        :method:`OrionBaseModel.update_or_create_from_orion`, one for each
        model required for referential integrity

        :returns: a list of the returns for each call in the chain
        :rtype: ``list`` of ``dict``
        """
        ret = []
        if not OrionNodeCategory.objects.count():
            result = OrionNodeCategory.update_or_create_from_orion()
            ret.append(result)

        result = super(OrionNode, cls).update_or_create_from_orion()
        ret.append(result)

        return ret

    class Meta:
        app_label = 'orion_integration'
        verbose_name = 'Orion Node'
        verbose_name_plural = 'Orion Nodes'


class OrionCernerCSTNode(OrionNode):
    """
    proxy model to show just the Cerner CST nodes

    see
    `Django proxy models<https://docs.djangoproject.com/en/2.1/topics/db/models/#proxy-models>`_
    """
    objects = OrionCernerCSTNodeManager()

    class Meta:
        proxy = True
        verbose_name = 'Orion Cerner CST Node'
        verbose_name_plural = 'Orion Cerner CST Nodes'


class OrionNodeCategory(OrionBaseModel, models.Model):
    """
    query:
    SELECT Description FROM Orion.NodeCategories
    """
    orion_id_query = (
        'SELECT CategoryID FROM Orion.NodeCategories WHERE CategoryID'
    )
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
    orion_id_query = (
        'SELECT ApplicationID FROM Orion.APM.Application WHERE ApplicationID'
    )
    orion_query = (
        'SELECT ApplicationID, Name, NodeID, DetailsUrl, FullyQualifiedName,'
        ' Description, Status, StatusDescription FROM Orion.APM.Application'
    )
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
    def update_or_create_from_orion(cls):  # pylint:disable=W0221
        """
        override :method:`OrionBaseModel.update_or_create_from_orion` to make
        sure that the foreign keys are already available in
        :class:`OrionNodeCategory`

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
