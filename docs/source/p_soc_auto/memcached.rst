Memcached Details
=================

The `memcached <https://memcached.org/>`_ server is currently running on the
same host as the :ref:`SOC Automation Server`.

The configuration file used by the `memcached <https://memcached.org/>`_ server
is under source control. The path for this file is
``configs/memcached/memcached``.

Symlink or copy this file to the `memcached <https://memcached.org/>`_
environment file at ``/etc/sysconfig/memcached``.