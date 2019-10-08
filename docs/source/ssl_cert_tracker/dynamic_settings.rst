SSL Certificate Tracker Dynamic Preferences
===========================================

* `Destination Email Addresses When In Debug Mode
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=to_emails>`__:
  
  In :attr:`p_soc_auto.settings.DEBUG` mode, it is not desirable to flood
  production email inboxes with :ref:`SOC Automation Server` emails. The
  :class:`ssl_cert_tracker.lib.Email` constructor will automatically replace the
  destination email addresses in a :class:`ssl_cert-tracker.models.Subscription`
  instance with the the value of this dynamic preference
  
  Defined in :class:`citrus_borg.dynamic_preferences_registry.EmailToWhenDebug`
  
* `Originating Email Address When in Debug Mode
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=from_email>`__:
  
  Same as above but for the originating email address
 
  Defined in :class:`citrus_borg.dynamic_preferences_registry.EmailFromWhenDebug`
