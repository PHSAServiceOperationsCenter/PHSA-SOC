SOC Automation Server
=====================

The :ref:`SOC Automation Server` is a `Python <https://www.python.org/>`_
`Django <https://www.djangoproject.com/>`_ application server running against
a `MariaDB <https://mariadb.org/>`_ database server.

See :ref:`MariaDB Details` for more usage information the `MariaDB
<https://mariadb.org/>`_ database server.

The :ref:`SOC Automation Server` is exposed to the network by an `NGINX server
<https://nginx.org/en/download.html>`_ over `uWSGI
<https://uwsgi-docs.readthedocs.io/en/latest/>`_.

See :ref:`NGINX Details` for more usage information about the `NGINX server
<https://nginx.org/en/download.html>`_.

See :ref:`uWSGI Details` for more usage information about the  `uWSGI
<https://uwsgi-docs.readthedocs.io/en/latest/>`_ layer.

The :ref:`SOC Automation Server` supports asynchronous task execution via
`Celery <http://www.celeryproject.org/>`_.

See :ref:`Celery Details` for more usage information about `Celery
<http://www.celeryproject.org/>`_.

The :ref:`SOC Automation Server` supports content caching via `memcached
<https://memcached.org/>`_.

See :ref:`Memcached Details` for more usage information about `memcached
<https://memcached.org/>`_.

Off the shelf components are installed using the normal facilities provided
by the operating system of the :ref:`SOC Automation Server` host.
Currently, the :ref:`SOC Automation Server` is running on a `CentOS 7.5
<https://www.centos.org/>`_.


Django settings
---------------

See :ref:`Django settings module` for a detailed description of the
configuration used by the :ref:`SOC Automation Server`.

:Note:

    The :ref:`Django settings module` is mandatory reading for developers.

Building the SOC Automation documentation
-----------------------------------------

The documentation for this project using `Sphinx 
<https://www.sphinx-doc.org/en/2.0/>`_.

Special requirements
^^^^^^^^^^^^^^^^^^^^

The documentation includes UML diagrams. In order to automatically generate
these diagrams, the host needs to have these packages installed:

* `PlantUML <http://plantuml.com/index>`_:

  Is used to translate diagrams described using `UML 
  <https://www.uml.org/index.htm>`_ into images, in this particular case,
  into PNG imaged.
  
  On ``CentOS 7.5``, `PlantUML <http://plantuml.com/index>`_ is not available
  as a normal (yum or rpm) install. One must download the `plantuml.jar 
  <http://sourceforge.net/projects/plantuml/files/plantuml.jar/download>`_
  and place it in the :file:/usr/bin directory.
  
  See the ``plantuml`` variable in the :file:docs/source/conf.py for
  configuration details
  
* `GraphViz <https://www.graphviz.org/>`_:

  Is needed by `PlantUML <http://plantuml.com/index>`_ for rendering
  `class diagrams <http://plantuml.com/class-diagram>`_.
  
  Is available as a normal yum install on ``CentOS 7.5``
  
Serving the documentation
^^^^^^^^^^^^^^^^^^^^^^^^^

The documentation is being served over `HTML 
<https://en.wikipedia.org/wiki/HTML>`_ by the SOC Automation web server with
the ``soc_docs`` alias. See :file:/configs/nginx/nginx.conf for details.

:Note:

    There are entries in the docs that use `URL's 
    <https://en.wikipedia.org/wiki/URL>`_ relative to the ``soc_docs`` alias.
    Changes to the mechanism serving the docs will require updated 
    documentation sources.
    
Building the documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^

From the normal command line django dev environment, execute:

.. code-block:: bash

   (phsa_venv) phsa@lvmsocq02:~/p_soc_auto$ cd docs
   (phsa_venv) phsa@lvmsocq02:~/p_soc_auto/docs$ make clean
   Removing everything under 'build'...
   (phsa_venv) phsa@lvmsocq02:~/p_soc_auto/docs$ make html
   Running Sphinx v2.1.2
   making output directory... done
   loading intersphinx inventory from https://docs.python.org/3.6/objects.inv...
   loading intersphinx inventory from http://docs.djangoproject.com/en/2.2/_objects/...
   building [mo]: targets for 0 po files that are out of date
   building [html]: targets for 29 source files that are out of date
   updating environment: 29 added, 0 changed, 0 removed
   reading sources... [100%] ssl_cert_tracker/subscriptions
   looking for now-outdated files... none found
   pickling environment... done
   checking consistency... done
   preparing documents... done
   writing output... [100%] ssl_cert_tracker/subscriptions
   generating indices... genindex py-modindex
   highlighting module code... [100%] ssl_cert_tracker.models
   writing additional pages... search
   copying static files... done
   copying extra files... done
   dumping search index in English (code: en) ... done
   dumping object inventory... done
   build succeeded.
   
   The HTML pages are in build/html.
   (phsa_venv) phsa@lvmsocq02:~/p_soc_auto/docs$

   