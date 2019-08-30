admin
=====

.. automodule:: mail_collector.admin

.. autoclass:: mail_collector.admin.MailConfigAdminBase
   :members: formfield_for_foreignkey

.. autoclass:: mail_collector.admin.DomainAccountAdmin
   :members: show_account, formfield_for_dbfield

.. autoclass:: mail_collector.admin.ExchangeAccountAdmin

.. autoclass:: mail_collector.admin.WitnessEmailAdmin

.. autoclass:: mail_collector.admin.ExchangeConfigurationAdmin
   :members: count_exchange_accounts, count_witnesses

.. autoclass:: mail_collector.admin.MailBotAdmin
   :members: has_add_permission, has_delete_permission,
             formfield_for_foreignkey

.. autoclass:: mail_collector.admin.MailSiteAdmin

.. autoclass:: mail_collector.admin.MailBetweenDomainsAdmin
   :members: show_link

.. autoclass:: mail_collector.admin.MailBotLogEventAdmin
   :members: show_site, get_actions
   :show-inheritance:

.. autoclass:: mail_collector.admin.MailHostAdmin
   :members: has_add_permission
   :show-inheritance:

.. autoclass:: mail_collector.admin.MailBotMessageAdmin
   :members: show_site, event_uuid, event_group_id, event_type,
             event_status, event_message, source_host, event_body,
             mail_account, event_registered_on, get_actions
   :show-inheritance:

.. autoclass:: mail_collector.admin.ExchangeServerAdmin
   :members: has_add_permission, has_delete_permission
   :show-inheritance:

.. autoclass:: mail_collector.admin.ExchangeDatabaseAdmin
   :members: formfield_for_foreignkey
   :show-inheritance:
