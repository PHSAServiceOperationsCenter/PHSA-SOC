SOC Automation Project
======================

The *SOC Automation Project* is a multi-component IT system used by the
*SOC* team.

All the components, whether off the shelf, or developed in house, can be
readily scaled horizontally via virtualization or containerization.

.. todo::

    We need to migrate the access point from `HTTP
    <https://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol>`_ to `HTTPS
    <https://en.wikipedia.org/wiki/HTTPS>`_.
    
    Currently, all the components of this project are communicating over
    insecure channels. We need to implement `SASL
    <https://en.wikipedia.org/wiki/Simple_Authentication_and_Security_Layer>`_
    and `TLS <https://en.wikipedia.org/wiki/Transport_Layer_Security>`_ based
    security protocols for inter-component communication.

.. toctree::
   :maxdepth: 2
   :caption: Components
   
   socauto.rst
   git.rst
   memcached.rst
   nginx.rst
   uwsgi.rst
   mariadb.rst
   celery.rst
   rabbitmq.rst
   logstash.rst
   winlogbeat.rst
   modules.rst

