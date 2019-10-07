.. automodule:: ssl_cert_tracker.admin

.. autoclass:: ssl_cert_tracker.admin.SSLCertTrackerBaseAdmin
   :members: formfield_for_foreignkey, add_view, change_view, has_add_permission,
       get_readonly_fields
       
.. autoclass:: ssl_cert_tracker.admin.SslCertificateAdmin
   :members: is_trusted
   :show-inheritance:
   
.. autoclass:: ssl_cert_tracker.admin.SslCertificateIssuerAdmin
   :members: link_field
   
.. autoclass:: ssl_cert_tracker.admin.SslProbePortAdmin
   :members: has_add_permission
   :show-inheritance:
   
.. autoclass:: ssl_cert_tracker.admin.SslExpiresInAdmin
   :members: expires_in_days
   :show-inheritance:
   
.. autoclass:: ssl_cert_tracker.admin.SslHasExpiredAdmin
   :members: has_expired_days_ago
   :show-inheritance:
   
.. autoclass:: ssl_cert_tracker.admin.SslNotYetValidAdmin
   :members: valid_in_days
   :show-inheritance: