MariaDB Details
===============

We are currently using MariaDB version 10.1.32.

The `MariaDB` root login is password protected (see
`<https://mariadb.com/kb/en/library/documentation/clients-utilities/mysql_secure_installation/>`_
). Contact `Serban Teodorescu <mailto:serban.teodorescu@phsa.ca>`_ or `James Reilly
<mailto:james.reilly@phsa.ca>`_ if you require root access to the `MariaDB` server.

The `USER` described under :attr:`p_soc_auto.settings.DATABASES` has full access
to the `database` used by the :ref:`SOC Automation Server` including `DROP
DATABASE` and `CREATE DATABASE` privileges.

If you are setting up a new host for either the whole :ref:`SOC Automation Server`,
or for a separate database server, see the `GRANT
<https://mariadb.com/kb/en/library/documentation/sql-statements-structure/sql-statements/account-management-sql-commands/grant/>`_
command.

Timezone Definitions
---------------------

Our system relies on timezone definitions being installed on the database, but
MariaDB does not install them by default. To install the timezone definitions
run the below command, supplying the username and password as described under
:attr:`p_soc_auto.settings.DATABASES` (or any other user that has permissions
to modify the database).

.. code-block::

 /usr/share/zoneinfo | mysql -u <username> -p mysql

For more information see the `MariaDB article on mysql_tzinfo_to_sql
<https://mariadb.com/kb/en/library/mysql_tzinfo_to_sql/>`_

MariaDB security
----------------

When we will move the database server to a separate host, we will have to configure
`TLS` connections. See MariaDB `Secure Connections Overview
<https://mariadb.com/kb/en/library/documentation/mariadb-administration/user-server-security/securing-mariadb/securing-mariadb-encryption/data-in-transit-encryption/secure-connections-overview/>`_
for details.

MariaDB scaling
---------------

This is going to be a complicated animal. `Django` doesn't support `MariaDB
Galera Clusters
<https://mariadb.com/kb/en/library/documentation/replication/galera-cluster/configuring-mariadb-galera-cluster/>`_
explicitly.

`Django` has some support for `Database Routing
<https://docs.djangoproject.com/en/2.2/topics/db/multi-db/#database-routers>`_ but
there is nothing there to suggest that any kind of controlled load-balancing would
be possible.

We may have to accept a `Hot StandBy` configuration to handle failovers and stop
worrying about load balancing.  