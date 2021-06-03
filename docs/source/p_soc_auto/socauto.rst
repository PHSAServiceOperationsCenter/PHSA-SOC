SOC Automation Server
=====================

The :ref:`SOC Automation Server` is a `Django <https://www.djangoproject.com/>`_
application server running with a `MariaDB <https://mariadb.org/>`_ database.
It is exposed to the network by an `NGINX server
<https://nginx.org/en/download.html>`_ over `uWSGI
<https://uwsgi-docs.readthedocs.io/en/latest/>`_.
The :ref:`SOC Automation Server` supports asynchronous task execution via
`Celery <http://www.celeryproject.org/>`_, and content caching via `memcached
<https://memcached.org/>`_.

For more details see:

* :ref:`MariaDB Details`
* :ref:`NGINX Details`
* :ref:`uWSGI Details`
* :ref:`Celery Details`

Off the shelf components are installed using the normal facilities provided
by the operating system of the :ref:`SOC Automation Server` host.
Currently, the :ref:`SOC Automation Server` is running `CentOS 7.5
<https://www.centos.org/>`_.


Django settings
---------------

See the :mod:`Django settings <p_soc_auto.settings>` for a detailed description
of the configuration used by the :ref:`SOC Automation Server`.

By default the application runs with the settings in ``p_soc_auto.settings.development``.
To set up a server for production one must run ``systemctl edit uwsgi-phsa-soc-app`` as root.
In the override configuration file that is generated the following text must be added:

.. code-block::

    [Service]
    Environment="DJANGO_SETTINGS_MODULE=p_soc_auto.settings.production"

The same effect can be achieved by hardlinking to a configuration override file.
See :ref:`Celery Details` for more details.

Building the SOC Automation documentation
-----------------------------------------

The documentation for this project using `Sphinx <https://www.sphinx-doc.org/en/2.0/>`_.

Special requirements
^^^^^^^^^^^^^^^^^^^^

The documentation includes UML diagrams. In order to automatically generate
these diagrams, the host needs to have these packages installed:

* `PlantUML <http://plantuml.com/index>`_:

  Is used to translate diagrams described using `UML
  <https://www.uml.org/index.htm>`_ into images, in this particular case,
  into PNG images.

  On *CentOS 7.5*, `PlantUML <http://plantuml.com/index>`_ is not available
  as a normal (yum or rpm) install. One must download the `plantuml.jar
  <http://sourceforge.net/projects/plantuml/files/plantuml.jar/download>`_
  and place it in the :file:`/usr/bin` directory.

  See the ``plantuml`` variable in :file:`docs/source/conf.py` for
  configuration details.

* `GraphViz <https://www.graphviz.org/>`_:

  Is needed by `PlantUML <http://plantuml.com/index>`_ for rendering
  `class diagrams <http://plantuml.com/class-diagram>`_.

  Is available as a normal yum install on *CentOS 7.5*.

Serving the documentation
^^^^^^^^^^^^^^^^^^^^^^^^^

The documentation is being served over `HTML
<https://en.wikipedia.org/wiki/HTML>`_ by the SOC Automation web server with
the ``soc_docs`` alias. See :file:`/configs/nginx/nginx.conf` for details.

:Note:

    There are entries in the docs that use `URL's
    <https://en.wikipedia.org/wiki/URL>`_ relative to the ``soc_docs`` alias.
    Changes to the mechanism serving the docs will require updated
    documentation sources.

Building the documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^

Log-on to the machine you wish to build documentation on as phsa.
Ensure you are using the ``phsa_venv`` virtual environment (if not run ``workon phsa_venv``)
then run ``make_docs``.

For reference ``make_docs`` is an alias for the following list of commands:

.. code-block:: bash

    cd ~/p_soc_auto/docs
    make clean
    make html
    cd -
