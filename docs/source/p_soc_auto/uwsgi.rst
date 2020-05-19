uWSGI Details
=============

The `uWSGI project <https://uwsgi-docs.readthedocs.io/en/latest/index.html>`_
doesn't exactly explain what ``uWSGI`` is. The easiest way to think of
``uWSGI`` is to consider it a ``Web server`` module. In ``NGINX``, the
module would be `ngx_http_uwsgi_module
<https://nginx.org/en/docs/http/ngx_http_uwsgi_module.html>`_. The purpose
of such a module is to allow applications developed in an arbitrary programming
language to be executed within the context of a ``Web server``.

Within the :ref:`SOC Automation Project`, the :ref:`SOC Automation Server` is
running via `uWSGI <https://uwsgi-docs.readthedocs.io/en/latest/index.html>`_
in the context of the :ref:`NGINX server <NGINX details>`.

The ``uWSGI`` module is configured via the source-controlled file located
under ``/configs/uwsgi/uwsgi.ini``.

.. literalinclude:: ../../../configs/uwsgi/uwsgi.ini
   :language: cfg

The ``Django`` application server is running as a `systemd
<https://www.freedesktop.org/wiki/Software/systemd/>`_ ``Linux service`` via
an ``uWSGI`` wrapper as shown by the source-controlled
``configs/uwsgi/uwsgi-phsa-soc-app.service`` file.

.. literalinclude:: ../../../configs/uwsgi/uwsgi-phsa-soc-app.service
   :language: cfg

See :ref:`Using custom systemd services <The phsa_celery_mail_collector.service file>`
for details about making this file available to ``systemd``.

To control the ``PHSA Service Operations Center uWSGI app`` service,
use the `systemctl
<https://www.freedesktop.org/software/systemd/man/systemctl.html#>`_
command line utility.

.. note::

    We are currently using a custom uwsgi executable. When setting up a
    new system copy the uwsgi file located on lvmsocq01 to /usr/bin.

.. todo::

    Use the default uWSGI repositories for CentOS.