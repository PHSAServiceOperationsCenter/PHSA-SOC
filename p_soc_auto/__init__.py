"""
.. _p_soc_auto:

django project p_soc_auto

:module:    p_soc_auto

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    nov. 16, 2018

"""
from .celery import app as celery_app

__all__ = ('celery_app',)
__version__ = '0.6.1-dev'
