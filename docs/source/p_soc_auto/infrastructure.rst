SOC Automation Project Infrastructure
=====================================

Currently the majority of the SOC Automation Application is running on a single machine, lvmsoq01.
This includes the web front-end, the database, background processes, and storing logs.
There are laptops running data collection software at various sites we are interested in monitoring.
See the appropriate application's page for more information.

For testing we currently have lvmsocq02, which is updated with a database dump from lvmsoq01,
and then the next release candidate version is pulled from git to test before deploying to prod.

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
            component Ingestion
            note right
                Begins at citrus_borg.consumers.process_win_event
            end note
            component "Server-Based Monitoring" as SBM
            component "Interval Checks" as DBM
        }
        database soc_database

        logstash -> rabbitmq
        rabbitmq -> Ingestion
    }

    node email
    node Orion

    winlogbeat -> logstash
    Ingestion -> soc_database
    SBM -> soc_database
    soc_database -> DBM
    Ingestion -> email
    Ingestion -> Orion
    DBM -> email
    DBM -> Orion
    SBM -> email
    SBM -> Orion