Active Directory Services Monitoring Application
================================================

This application is monitoring network nodes that provide `Active Directory
Domain Services
<https://docs.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview>`__.
Through out the documentation for this application, we will mostly refer to
`Active Directory Domain Services` by using the abbreviation `AD`.

The application is collecting monitoring data by way of sending periodic
`LDAP <https://ldap.com/>`__ connection requests to each network node known
to be an `AD` controller.
 

.. toctree::
   :maxdepth: 2
   
   alerts.rst
   reports.rst
   ad_data.rst
   ldap.rst
   settings.rst
   celery.rst
   modules.rst

