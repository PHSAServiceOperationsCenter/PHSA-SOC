NGINX Details
=============

The `NGINX server <https://nginx.org/en/download.html>`_ server is currently
running on the same host as the :ref:`SOC Automation Server`.

The configuration file used by the `NGINX
server <https://nginx.org/en/download.html>`_ server is under source control.
The path for this file is :file:`configs/nginx/nginx.conf`.

.. literalinclude:: ../../../configs/nginx/nginx.conf
   :language: nginx
     
Create a link to this file at :file:`/etc/nginx/nginx.conf`.
    
Nginx scaling
-------------

The configurations shown above is already ready for horizontal scaling of the
*Django* application server (see the *upstream django* directive).
It is possible to cascade this implementation by adding a layer of `NGINX
servers <https://nginx.org/en/download.html>`_ between the network access
point and the *Django* application server nodes.

It is also possible to configure the `NGINX server
<https://nginx.org/en/download.html>`_ as a reverse *SSL proxy* in order to
off-load *SSL* computations from the *Django* application server(s) to the
`NGINX server <https://nginx.org/en/download.html>`_.

See `Using nginx as HTTP load balancer
<https://nginx.org/en/docs/http/load_balancing.html>`_ for all the gory
details.

Nginx security
--------------
See `Configuring HTTPS servers
<https://nginx.org/en/docs/http/configuring_https_servers.html>`_.