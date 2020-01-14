.. automodule:: ldap_probe.admin

.. autoclass:: ldap_probe.admin.LdapProbeBaseAdmin
   :show-inheritance:
   :members: formfield_for_foreignkey
   
.. autoclass:: ldap_probe.admin.OrionADNodeAdmin
   :show-inheritance:
   :members: has_add_permission, has_delete_permission, show_node_caption,
       node_dns, show_orion_admin_url, show_orion_url, ip_address, site,
       location
       
.. autoclass:: ldap_probe.admin.NonOrionADNodeAdmin
   :show-inheritance:

.. autoclass:: ldap_probe.admin.LDAPBindCredAdmin
   :show-inheritance:
   :members: show_account, formfield_for_dbfield
   
.. autoclass:: ldap_probe.admin.LdapProbeLogAdminBase
   :show-inheritance:
   :members: has_add_permission, has_delete_permission, get_readonly_fields
   
.. autoclass:: ldap_probe.admin.LdapProbeLogFailedAdmin
   :show-inheritance:

.. autoclass:: ldap_probe.admin.LdapProbeFullBindLogAdmin
   :show-inheritance:

.. autoclass:: ldap_probe.admin.LdapProbeAnonBindLogAdmin
   :show-inheritance:
   
.. autoclass:: ldap_probe.admin.LdapCredErrorAdmin
   :show-inheritance:

