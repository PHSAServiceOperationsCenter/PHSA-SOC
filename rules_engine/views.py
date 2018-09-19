"""
.. _views:

django views for the rules_engine app

:module:    p_soc_auto.rules_engine.views

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    sep. 19, 2018

"""
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render
from dal import autocomplete

from .models import RuleApplies


class RuleAppliesAutocomplete(autocomplete.Select2ListView):
    """
    class view for providing autocomplete functionality in the
    :class:`rules_engine.forms.RuleAppliesForm`
    """

    def get_list(self):
        """
        :returns:
            a list of fields for the model extracted from the
            :attr:`rules_engine.models.RuleApplies.content_type`

        """
        pk = int(self.request.META.get('HTTP_REFERER').split('/')[6])
        model_for_pk = RuleApplies.objects.get(pk=pk).content_type.model
        content = ContentType.objects.get(model=model_for_pk)

        return [field.name for field in content.
                get_all_objects_for_this_type().first()._meta.get_fields()
                if not field.primary_key and not field.is_relation]

# Create your views here.
