Configuring :ref:`Mail Borg Client Application` instances remotely
==================================================================

While the ref:`Mail Borg Client Application` can use fully local configurations,
it is designed to pull its main configuration from the automation server.

Within the :ref:`Mail Collector Application` there are some components that
are responsible for defining, editing, maintaining, and delivering
configuration data to a :ref:`Mail Borg Client Application` instance upon
request.

Data structure
--------------

All the notes in the diagram below are written using Django jargon. The
**mail_collector** group label in the diagram maps to the
:ref:`Mail Collector Application`. Some notes in the diagram also reference
models defined in the :ref:`Citrus Borg Application`.

When populating and serializing this data structure to JSON, we will obtain
something like this **change to a link to the REST call**.

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
      