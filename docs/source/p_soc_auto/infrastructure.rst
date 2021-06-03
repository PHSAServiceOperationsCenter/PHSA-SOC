SOC Automation Project Infrastructure
=====================================

Currently the majority of the SOC Automation Application is running on a single machine, lvmsoq01.
This includes the web front-end, the database, background processes, and storing logs.
There are laptops running data collection software at various sites we are interested in monitoring.
See the appropriate application's page for more information.

For testing we have lvmsocq02. To prepare for testing a database dump is copied from lvmsoq01,
and the next release candidate version is pulled using git.

.. note:: Remember to migrate the changes to the Django database schema before running the new version of the code.

For development we have two machines, lvmsocdev01 and lvmsocdev03.

.. uml::
    :caption: SOC Automation Architecture

    scale 1080*1920

    node "SOC Bot" {
        component application
        note right
            The only application currently is a Citrix monitor
        end note
        component "Windows Log" as WindowsLog
        component winlogbeat
        application -> WindowsLog
        WindowsLog -> winlogbeat
    }

    node "SOC Automation Server (lvmsocq01)" {
        component logstash
        component rabbitmq
        package Django {
            component "WinEvent Consumers" as Ingestion
            component "Locally Run Monitoring Scripts" as SBM
            component "Periodic Database Checks" as DBM
        }
        database soc_database

        logstash -> rabbitmq
        rabbitmq -> Ingestion
    }

    node Alerts {
        node email
        node Orion
    }

    winlogbeat -> logstash
    Django <--> soc_database
    soc_database -> DBM
    Django -> Alerts