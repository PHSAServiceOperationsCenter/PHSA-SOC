SOC Automation Project Infrastructure
=====================================

Currently the majority of the SOC Automation Application is running on a single machine, lvmsoq01.
This includes the web front-end, the database, background processes, and storing logs.
There are laptops running data collection software at various sites we are interested in monitoring.
See the appropriate application's page for more information.

For testing we currently have lvmsocq02, which is updated with a database dump from lvmsoq01,
and then the next release candidate version is pulled from git to test before deploying to prod.

For development we have two machines, lvmsocdev01 and lvmsocdev03.