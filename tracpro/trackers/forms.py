from __future__ import unicode_literals

from django import forms
from django.forms.models import modelformset_factory

from tracpro.contacts.models import DataField
from .models import GroupRule, Tracker, Alert, AlertRule


class GroupRuleForm(forms.ModelForm):
    class Meta:
        model = GroupRule
        fields = ('id', 'action', 'region', 'condition', 'threshold')


GroupRuleFormSet = modelformset_factory(GroupRule, GroupRuleForm, can_delete=True)


class TrackerForm(forms.ModelForm):
    class Meta:
        model = Tracker
        fields = forms.ALL_FIELDS
        exclude = ('org', )

    def __init__(self, *args, **kwargs):
        super(TrackerForm, self).__init__(*args, **kwargs)
        self.fields['contact_field'].queryset = self.fields['contact_field'].queryset.filter(
            value_type=DataField.TYPE_NUMERIC)


class AlertRuleForm(forms.ModelForm):
    class Meta:
        model = AlertRule
        fields = ('id', 'flow', 'region', 'action', 'group')


AlertRuleFormSet = modelformset_factory(AlertRule, AlertRuleForm, can_delete=True)


class AlertForm(forms.ModelForm):
    class Meta:
        model = Alert
        fields = ('name',)
