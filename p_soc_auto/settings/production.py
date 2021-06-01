"""
p_soc_auto.settings.production
------------------------------

Production only Django settings for the :ref:`SOC Automation Server`

:copyright:

    Copyright 2018 - 2020 Provincial Health Service Authority
    of British Columbia

"""
from p_soc_auto.settings.common import *

DEBUG = False
"""
Enable or disable debugging information
"""

ALLOWED_HOSTS = ['lvmsocq01', 'lvmsocq01.healthbc.org', ]
"""
hosts that can be used to run production servers
"""

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
