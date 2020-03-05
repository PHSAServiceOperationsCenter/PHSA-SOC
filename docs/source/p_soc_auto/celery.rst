Celery Details
==============

See :ref:`Mail Collector Celery Details` for a more detailed description about
implementing ``Celery Tasks``.

We are using a dedicated `Celery
<https://docs.celeryproject.org/en/latest/index.html>`_
`worker <https://docs.celeryproject.org/en/latest/userguide/workers.html>`_
for each ``queue`` defined under the
:attr:`p_soc_auto.settings.CELERY_QUEUES` setting.

There is a dedicated `Celery
<https://docs.celeryproject.org/en/latest/index.html>`_
`worker <https://docs.celeryproject.org/en/latest/userguide/workers.html>`_ for
``email`` operations that is (or should be) shared between the ``Django``
applications defined by the :ref:`SOC Automation Server`.

There is a dedicated `Celery
<https://docs.celeryproject.org/en/latest/index.html>`_
`worker <https://docs.celeryproject.org/en/latest/userguide/workers.html>`_ for
each ``Django`` application defined by the :ref:`SOC Automation Server`.

There is also a dedicated `Celery
<https://docs.celeryproject.org/en/latest/index.html>`_
`worker <https://docs.celeryproject.org/en/latest/userguide/workers.html>`_ 
shared between the ``Django`` applications defined by the
:ref:`SOC Automation Server`.

Task scheduling in ``Celery``
-----------------------------

By design most of the `Celery tasks
<http://docs.celeryproject.org/en/latest/userguide/tasks.html>`_
implemented in the :ref:`SOC Automation Server` applications are not invoked
directly, they are invoked by an independent scheduling system.

The scheduling system is implemented using `Celery Periodic Tasks
<https://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html?highlight=beat>`_,
a.k.a. ``Celery Beat`` with `Custom Scheduler Classes
<https://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html?highlight=beat#id8>`_.

The ``Custom Scheduler Classes`` used by the :ref:`SOC Automation Server`
applications are implemented via the `django-celery-beat
<https://pypi.python.org/pypi/django-celery-beat/>`_ package. This package
allows us to store schedules in an ``SQL`` database, in this case, in the
:ref:`MariaDB database <MAriaDB Details>` used by the :ref:`SOC Automation
Server`. Another advantage provided by the `django-celery-beat
<https://pypi.python.org/pypi/django-celery-beat/>`_ package is the integration
with the `Django admin interface <https://docs.djangoproject.com/en/2.2/ref/contrib/admin/>`_.
This provided a very simple, if not very easy to use, Web console interface for
configuring ``Celery Periodic Tasks``. See `Periodic Tasks adminsitration
<../../../admin/django_celery_beat/>`_, `Periodic Tasks
<../../../admin/django_celery_beat/periodictask/>`_, `Crontabs
<../../../admin/django_celery_beat/crontabschedule/>`_, and `Intervals
<../../../admin/django_celery_beat/intervalschedule/>`_.

We recommend that all ``Celery Periodic Tasks`` used by the :ref:`SOC
Automation Server` be created by way of `Django Data Migrations
<https://docs.djangoproject.com/en/2.2/topics/migrations/#data-migrations>`_.
This will avoid labourious data entry operations by (potentially) untrained
``SOC`` personnel, and it will also ensure speedy deployments for new versions
of the :ref:`SOC Automation Server`. See `p_soc_auto_migration.migrations.0001_beats`
for an example.


The ``Celery Beat`` service
^^^^^^^^^^^^^^^^^^^^^^^^^^^

We have defined a dedicated *systemd Linux service* for running the
schedulers used by the :ref:`SOC Automation Server` :ref:`Celery Periodic Tasks
<Celery Details>`. The ``.service`` file for this *Linux* service is under
source control at :file:`configs/celery/phsa_celery_beat.service`.

.. literalinclude:: ../../../configs/celery/phsa_celery_beat.service
   :language: cfg

Environment Variables
---------------------

In order to communicate properly with Django we need to set certain environment values
(settings module, secret key, etc). Since the systemd service sets up its own environment
it is necessary to modify the celery service's configuration to contain this information.
Since this information may be private, or change from machine to machine, it cannot be
stored in the configuration that is committed to git.

Each celery service may have a directory (the name of the service with .d appended) where
it stores local configuration of that service. These files are all replaced with links to
a common override.conf to prevent copy paste errors. In this file there is a
``[Service]`` section which contains a series of ``Environment="<var_name>=<value>"`` lines
which ensure the local environment is properly set up when the service runs.

If you need to create the override links you can use the following process
(you may need to get elevated permissions, or use ``sudo``):

1. ``cd /etc/systemd/system`` to get to the folder that contains the systemd service definitions.
2. ``systemctl edit <service_name>`` will set up the override file and folder. Save and exit without modifying.
3. ``rm <service_name>.d/override.conf`` to remove the empty override file.
4. ``ln override.conf <service_name>.d/override.conf`` to create the link to the override.conf in the main folder.


Throttling the ``Celery Beat`` service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We have observed that sometimes, under production conditions, the
``Celery Beat`` service will start consuming a vary large amount of host
resources. We are controlling this by using the
`Monit <https://mmonit.com/monit/>`_ utility. The file describing this
operation the the `Monit <https://mmonit.com/monit/>`_ daemon is under source
control at :file:`configs/monit/celery-beat`. This file must be symlinked to */etc/monit.d/*.

.. literalinclude:: ../../../configs/monit/celery-beat
   :language: cfg


Monitoring ``Celery Tasks`` execution
-------------------------------------

Currently, we are monitoring *Celery Tasks* using `Flower
<https://docs.celeryproject.org/en/latest/userguide/monitoring.html?highlight=flower#flower-real-time-celery-web-monitor>`_.

The *Flower* service is exposed on the network address of the :ref:`SOC
Automation Server` on port 5555.

The *Flower* service runs as a *systemd Linux service* configured via the
source controlled file :file:`configs/celery/phsa_celery_flower.service`.

.. literalinclude:: ../../../configs/celery/phsa_celery_flower.service
   :language: cfg
   
See the usual suspects for enabling and controlling the *Flower* service.

`Celery` scaling
----------------

To be determined...

Celery security
---------------

At a minimum, we need to use non-default credentials in the
:attr:`p_soc_auto.settings.CELERY_BROKER_URL`.

`Celery` supports `SSL
<https://docs.celeryproject.org/en/latest/userguide/configuration.html#broker-use-ssl>`_
with the default transport (`pyamqp`) for the `AMPQ <https://www.amqp.org/>`_
protocol. Sill, enabling `SSL` between the `Celery workers` and the
:ref:`RabbitMQ Server` must be a separate, dedicated effort.
