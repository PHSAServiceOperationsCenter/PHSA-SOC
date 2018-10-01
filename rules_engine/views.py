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
        pk = self.forwarded.get('content_type', None)
        if pk is None:
            return ['search failed']

        content = ContentType.objects.get(pk=int(pk))

        return [field.name for field in
                [
                    field for field in
                    content.get_all_objects_for_this_type().
                    first()._meta.get_fields() if field.concrete
                ]
                if not (field.is_relation or field.primary_key)]
