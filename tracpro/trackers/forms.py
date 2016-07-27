from __future__ import unicode_literals

from django import forms
from django.forms.models import modelformset_factory

from .models import GroupRule


class GroupRuleForm(forms.ModelForm):
    class Meta:
        model = GroupRule
        fields = ('action', 'region', 'condition', 'threshold')


GroupRuleFormSet = modelformset_factory(GroupRule, GroupRuleForm)
