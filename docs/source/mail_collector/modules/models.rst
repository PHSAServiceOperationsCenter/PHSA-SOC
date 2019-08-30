models
======

.. automodule:: mail_collector.models

.. autoclass:: mail_collector.models.MailHostManager
   :members: get_queryset
   
.. autoclass:: mail_collector.models.MailSiteManager
   :members: get_queryset

.. autoclass:: mail_collector.models.DomainAccount
   :members: clean, save, get_default

.. autoclass:: mail_collector.models.ExchangeAccount

.. autoclass:: mail_collector.models.WitnessEmail

.. autoclass:: mail_collector.models.ExchangeConfiguration
   :members: clean, save, get_default
   
.. autoclass:: mail_collector.models.MailSite
   :members: objects
   :show-inheritance:
   
.. autoclass:: mail_collector.models.MailHost
   :members: objects
   :show-inheritance:
   
.. autoclass:: mail_collector.models.MailBotLogEvent

.. autoclass:: mail_collector.models.MailBotMessage
   :show-inheritance:
   
.. autoclass:: mail_collector.models.ExchangeServer

.. autoclass:: mail_collector.models.ExchangeDatabase

.. autoclass:: mail_collector.models.MailBetweenDomains
