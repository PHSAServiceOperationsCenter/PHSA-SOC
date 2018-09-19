from django.forms import ModelForm
from dal import autocomplete

from .models import RuleApplies


class RuleAppliesForm(ModelForm):
    class Meta:
        model = RuleApplies
        exclude = []
        widgets = {
            'field_name':
            autocomplete.ListSelect2(url='autocomplete-field-name')
        }
