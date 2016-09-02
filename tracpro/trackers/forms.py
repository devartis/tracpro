from __future__ import unicode_literals

from django import forms
from django.forms.models import modelformset_factory

from tracpro.contacts.models import DataField
from .models import GroupRule, Tracker, Alert, AlertRule


class GroupRuleForm(forms.ModelForm):
    class Meta:
        model = GroupRule
        fields = ('id', 'action', 'region', 'condition', 'threshold')

    def __init__(self, *args, **kwargs):
        super(GroupRuleForm, self).__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


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

        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class AlertRuleForm(forms.ModelForm):
    class Meta:
        model = AlertRule
        fields = ('id', 'flow', 'region', 'action', 'group')

    def __init__(self, *args, **kwargs):
        super(AlertRuleForm, self).__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


AlertRuleFormSet = modelformset_factory(AlertRule, AlertRuleForm, can_delete=True)


class AlertForm(forms.ModelForm):
    class Meta:
        model = Alert
        fields = ('name',)

    def __init__(self, *args, **kwargs):
        super(AlertForm, self).__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

