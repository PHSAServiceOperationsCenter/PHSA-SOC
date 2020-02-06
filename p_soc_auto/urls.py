"""
p_soc_auto.urls
---------------

This module contains the `URL` configuration for the :ref:`SOC Automation Server`.

The `urlpatterns` list routes URLs to views. For more information please see:
`URL dispatcher
<https://docs.djangoproject.com/en/2.2/topics/http/urls/#url-dispatcher>`__.

Examples:

* Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')

* Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')

* Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path(r'admin/doc/', include('django.contrib.admindocs.urls')),
    path(r'grappelli/', include('grappelli.urls')),
    path(r'admin/', admin.site.urls),
    path(r'mail_collector/', include('mail_collector.urls')),
    url(r'^', include('templated_email.urls', namespace='templated_email')),
]
