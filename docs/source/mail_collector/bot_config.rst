.. _borg_remote_config:

Remote Configurations for :ref:`Mail Borg Client Application` instances
=======================================================================

While the ref:`Mail Borg Client Application` can use fully local configurations,
it is designed to pull its main configuration from the automation server.

Within the :ref:`Mail Collector Application` there are some components that
are responsible for defining, editing, maintaining, and delivering
configuration data to a :ref:`Mail Borg Client Application` instance upon
request.

.. _borg_client_config:

Configuration sample
--------------------

The configuration data is `JSON <https://www.json.org/>`_ encoded and a sample
is shown here.

.. code-block:: json

    [
        {
            "host_name":"bccss-t450s-04",
            "site":{"site":"over the rainbow"},
            "exchange_client_config":
                {
                    "config_name":"default configuration",
                    "exchange_accounts":
                        [
                            {
                                "smtp_address":"z-spexcm001-db01001@phsa.ca",
                                "domain_account":
                                    {
                                        "domain":"PHSABC",
                                        "username":"svc_SOCmailbox",
                                        "password":"goodluckwiththat"
                                    },
                                    "exchange_autodiscover":true,
                                    "autodiscover_server":null
                            },
                            {
                                "smtp_address":"z-spexcm001-db01002@phsa.ca",
                                "domain_account":
                                    {
                                        "domain":"PHSABC",
                                        "username":"svc_SOCmailbox",
                                        "password":"goodluckwiththat"
                                    },
                                    "exchange_autodiscover":true,
                                    "autodiscover_server":null
                            },
                        ],
                "debug":false,
                "autorun":true,
                "mail_check_period":"01:00:00",
                "ascii_address":true,
                "utf8_address":false,
                "check_mx":true,
                "check_mx_timeout":"00:00:05",
                "min_wait_receive":"00:00:03",
                "backoff_factor":3,
                "max_wait_receive":"00:02:00",
                "tags":null,
                "email_subject":"exchange monitoring message",
                "witness_addresses":
                    [],
                },
        },
    ]
    
Note that the configuration data is pulled from multiple tables as per the
:ref:`Data structure` diagram shown below.

Special configuration cases
---------------------------

If a bot is not known to the ``SOC Automation server``, it can still pull the
main configuration from the server but:

* The ``host_name`` key in sample above will contain the value 'host.not.exist'
  
  When the bot sends its first event to the ``SOC Automation server``, a
  record will be made of its name.
  
  **The ``SOC Automation server`` user must then change the record above by:**
  
  1. assigning an :class:`mail_collector.models.ExchangeCofiguration`
     instance to said bot
 
  2. assigning a valid :class:`mail_collector.models.MailSite` instance
     to said bot
     
  3. opening an RDP session to the bot host and clicking the ``Reload
     config from server`` button

* The ``site`` key in the sample above will be empty. The
  :ref:`Mail Borg Client Application` will populate this key with the value
  ``{'site': 'site.not.seen'}``

.. todo: `<https://trello.com/c/E2cSQpwA>`_

.. todo: `<https://trello.com/c/Vs0LWMD5>`_


Data structure
--------------

All the notes in the diagram below are written using Django jargon. The
**mail_collector** group label in the diagram maps to the
:ref:`Mail Collector Application`. Some notes in the diagram also reference
models defined in the :ref:`Citrus Borg Application`.

.. uml::
   :caption: Exchange client configuration data model
   
    scale 1080*1920
    
    package "mail_collector" <<Rectangle>> {
        
        abstract class BaseEmail {
            smtp_address
        }
        note top
            Defined in mail_collector.models.BaseEmail
        end note
        
        class MailSite {
            site
        }
        note left
            Defined in mail_collector.models.MailSite
            Inherits from citrus_borg.models.BorgSite
        end note
       
        class MailBot {
            host_name
            .. other fields ..
        }
        note right
            Defined in mail_collector.models.MailHost
            Inherits from citrus_borg.models.WinlogbeatHost
        end note

        class ExchangeConfiguration {
            ,, fields ..
            config_name
            is_default
            debug
            autorun
            mail_check_period
            ascii_address
            utf8_address
            check_mx
            check_mx_timeout
            min_wait_receive
            backoff_factor
            max_wait_receive
            tags
            email_subject
        }
        note right
            Defined in mail_collector.models.ExchangeAccount
        end note
        
        class WitnessEmail {
            smtp_address
        }
        note bottom
            Defined in mail_collector.models.WitnessEmail
            Inherits from mail_collector.models.BaseEmail
        end note
        
        class DomainAccount {
            .. fields ..
            domain
            username
            password
            is_default
            .. methods ..
            clean()
            save()
            {static} get_default()
        }
        note right
            Defined in mail_collector.models.DomainAccount
        end note
        
        class ExchangeAccount {
            exchange_autodiscover
            autodiscover_server
        }
        note right
            Defined in mail_collector.models.ExchangeAccount
        end note
        
        BaseEmail <|-- WitnessEmail
        
        BaseEmail <|-- ExchangeAccount
                   
        ExchangeAccount ||--o| DomainAccount
        note right on link
            Expressed with django.db.models.ForeignKey
            
            An Exchange account can be defined by just the email address but
            in most enterprise organizations an Exchange account must be
            mapped to a Windows domain account.
            In the latter cases the same Windows domain account can be used
            to access multiple Exchange accounts
        end note
        
        MailSite ||--o{ MailBot
        note left on link
            Expressed with django.db.models.ForeignKey
            
            A MailSite instance can have 0 or more MailHost instances
        end note
        
        MailBot ||--o| ExchangeConfiguration
        note right on link
            Expressed with django.db.models.ForeignKey
            
            A MailBot can use one ExchangeConfiguration instance.
            It is possible to change the ExchangeConfiguration instance
            used by a MailBot
        end note
        
        ExchangeConfiguration }|--o{ WitnessEmail
        note left on link
            Expressed with django.db.models.ManyToMany
            
            An ExchangeConfiguration can use 0 or more WitnessEmail instances
        end note
        
        ExchangeConfiguration }|--|{ ExchangeAccount
        note right on link
            Expressed with django.db.models.ManyToMany
            
            An ExchangeConfiguration must use at least one ExchangeAccount
            instance and it can use as many ExchamgeAccount instances as
            desired
        end note
          
    }
      