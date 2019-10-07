Subscription Services
=====================

Subscriptions are used as a mechanism for rendering and addressing email messages.

The computations are the responsibility of the :class:`ssl_cert_tracker.lib.Email`
class.

All the metadata required for rendering an email message is stored in the
:class:`Subscription model <ssl_cert_tracker.models.Subscription>` shown below.

Each email type stored in the `Subscription model` needs to include a reference
to a `Django template
<https://docs.djangoproject.com/en/2.2/topics/templates/#the-django-template-language>`_
like the one below.

The workflow for rendering an email message is as follows:

* a `Celery task` invokes a `function` that generates the value for the `data` to
  be rendered. Note that there is a :attr:`data` attribute in the `email template`
  below
  
* the `Celery task` then invokes, directly or indirectly, an instance of the
  :class:`ssl_cert_tracker.lib.Email` clas. The constructor of this class will put
  together the `data` and the `extra_context` attributes of the email message
  with the `template` and other metadata defined in a
  :class:`ssl_cert_tracker.models.Subscription` instance
  
* the `Celery task` will then fire the :meth:`ssl_cert_tracker.lib.Email.send`
  method

Email template sample
---------------------

.. literalinclude:: ../../../mail_collector/templates/email/mail_events_by_bot.email
   :language: django
   
This particular template is used by the `Exchange Failed Send Receive By Bot
<../../../admin/ssl_cert_tracker/subscription/?q=Exchange+Failed+Send+Receive+By+Bot>`_
subscription.

The Subscription model
----------------------

.. autoclass:: ssl_cert_tracker.models.Subscription
   :members:
   :no-show-inheritance:
   
The Subscription `Django admin` interface
-----------------------------------------

.. autoclass:: ssl_cert_tracker.admin.SubscriptionAdmin
   :members: formfield_for_foreignkey, add_view, change_view, get_readonly_fields,
       has_add_permission, has_delete_permission