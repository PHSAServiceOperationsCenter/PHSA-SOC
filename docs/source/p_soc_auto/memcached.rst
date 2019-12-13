Memcached Details
=================

The `memcached <https://memcached.org/>`__ server is currently running on the
same host as the :ref:`SOC Automation Server`.

The configuration file used by the `memcached <https://memcached.org/>`__ server
is under source control. The path for this file is
``configs/memcached/memcached``.

.. literalinclude:: ../../../configs/memcached/memcached
   :language: cfg

Symlink or copy this file to the `memcached <https://memcached.org/>`__
environment file at ``/etc/sysconfig/memcached``.

The :ref:`SOC Automation Server` is connecting to the `memcached
<https://memcached.org/>`__ server using the setting described by the
:attr:`p_soc_auto.settings.CACHES` :class:`dictionary <dict>`.

Memcached scaling
-----------------

`Memcached <https://memcached.org/>`_ will scale horizontally out of the box.
In our case, once additional `memcached <https://memcached.org/>`_ instances
are running, we only need to add corresponding ``address, port`` tuples to the
:class:`LOCATION <list>` of the :attr:`p_soc_auto.settings.CACHES` setting.

Memcached security
------------------

This requires some more research.

`Memcached <https://memcached.org/>`__ supports `SASL
<https://github.com/memcached/memcached/wiki/SASLHowto>`__ but it is not clear
whether the :class:`django.core.cache.backends.memcached.PyLibMCCache` backend
will work with ``SASL``.

Here is an article about `How To Secure Memcached by Reducing Exposure
<https://www.digitalocean.com/community/tutorials/how-to-secure-memcached-by-reducing-exposure>`__.
But this article only talks about reducing the attack surface of a `Memcached
<https://memcached.org/>`__ cluster.
to 
