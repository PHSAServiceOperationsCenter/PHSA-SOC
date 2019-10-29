"""
p_soc_auto.wsgi
---------------

The `WSGI <https://wsgi.readthedocs.io/en/latest/index.html>`__ configuration for
the :ref:`SOC AUtomation Server`.

It exposes the `WSGI <https://wsgi.readthedocs.io/en/latest/index.html>`__ callable
as a module-level variable named ``application``.

For more information on this file, see `How to deploy with WSGI
<https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/#how-to-deploy-with-wsgi>`__.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Oct. 29, 2019

"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "p_soc_auto.settings")

application = get_wsgi_application()
