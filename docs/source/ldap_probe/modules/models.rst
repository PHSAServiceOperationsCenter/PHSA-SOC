.. automodule:: ldap_probe.models

.. autofunction:: ldap_probe.models._get_default_ldap_search_base

.. autofunction:: ldap_probe.models._get_default_warn_threshold

.. autofunction:: ldap_probe.models._get_default_err_threshold

.. autofunction:: ldap_probe.models._get_default_alert_threshold

.. autoclass:: ldap_probe.models.LDAPBindCred
   :show-inheritance:
   
.. autoclass:: ldap_probe.models.ADNodePerfBucket
   :show-inheritance:

.. autoclass:: ldap_probe.models.BaseADNode
   :show-inheritance:
   :members: sql_case_dns, sql_orion_anchor_field, get_node, annotate_orion_url,
       annotate_probe_details, report_probe_aggregates, report_perf_degradation
   
.. autoclass:: ldap_probe.models.OrionADNode
   :members: orion_admin_url, orion_url, report_bad_fqdn, report_duplicate_nodes
   :show-inheritance:
   
.. autoclass:: ldap_probe.models.NonOrionADNode
   :members: remove_if_in_orion
   :show-inheritance:

.. autoclass:: ldap_probe.models.LdapCredError
   :show-inheritance:
   

