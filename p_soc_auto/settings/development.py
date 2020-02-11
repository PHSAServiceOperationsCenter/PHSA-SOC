"""
p_soc_auto.settings.development
-------------------------------

Development only Django settings for the :ref:`SOC Automation Server`

:copyright:

    Copyright 2018 - 2020 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
from p_soc_auto.settings.common import *

DEBUG = True
"""
Enable or disable debugging information
"""

ALLOWED_HOSTS = ['lvmsocdev01', 'lvmsocdev03', 'lvmsocq02',
                 'lvmsocdev01.healthbc.org', 'lvmsocdev03.healthbc.org',
                 'lvmsocq02.healthbc.org', ]
"""
hosts that can be used to run development servers
"""

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '5u7)@@#z0yr-$4q#enfc&20a6u6u-h1_nr^(z%fkqu3dx+y6jj'