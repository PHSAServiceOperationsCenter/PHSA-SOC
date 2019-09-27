Abstract `Django` models
========================

See `Django abstract models
<https://docs.djangoproject.com/en/2.2/topics/db/models/#abstract-base-classes>`_
for a detailed explanation about abstract models.

We are using `abstract models` to make sure that we can provide history
related fields for any `Django model` defined by the :ref:`SOC Automation
Server` without duplicating these fields all over the place.

.. automodule:: p_soc_auto_base.models

.. autoclass:: p_soc_auto_base.models.BaseModel
   :members:
   :undoc-members:
   :no-show-inheritance:
   
