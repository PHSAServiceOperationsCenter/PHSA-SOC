Active Directory Services Monitoring Application Settings
=========================================================

Static settings
---------------

There are no entries specific to this application in the :mod:`Django
settings module <p_soc_auto.settings>`.

User configurable settings
--------------------------

All dynamic user preferences used by this application are part of the
:attr:`citrus_borg.dynamic_preferences_registry.ldap_probe` section. Here is
a list of these preferences:

* :class:`citrus_borg.dynamic_preferences_registry.LdapSearchBaseDNDefault`

* :class:`citrus_borg.dynamic_preferences_registry.LdapServiceUser`

* :class:`citrus_borg.dynamic_preferences_registry.LdapExpireProbeLogEntries`

* :class:`citrus_borg.dynamic_preferences_registry.LdapDeleteExpiredProbeLogEntries`

* :class:`citrus_borg.dynamic_preferences_registry.LdapErrorAlertSubscription`

* :class:`citrus_borg.dynamic_preferences_registry.LdapErrorReportSubscription`

* :class:`citrus_borg.dynamic_preferences_registry.LdapNonOrionADNodesReportSubscription`

* :class:`citrus_borg.dynamic_preferences_registry.LdapOrionADNodesFQDNReportSubscription`

* :class:`citrus_borg.dynamic_preferences_registry.LdapOrionADNodesDupesReportSubscription`

* :class:`citrus_borg.dynamic_preferences_registry.LdapPerfAlertSubscription`

* :class:`citrus_borg.dynamic_preferences_registry.LdapPerfAlertThreshold`

* :class:`citrus_borg.dynamic_preferences_registry.LdapPerfWarnThreshold`

* :class:`citrus_borg.dynamic_preferences_registry.LdapReportPeriod`

These preferences can be accessed from the `LDAP dynamic preferences section
</../../../admin/dynamic_preferences/globalpreferencemodel/?q=ldap>`__
