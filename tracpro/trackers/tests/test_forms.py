from __future__ import unicode_literals

from tracpro.contacts.models import DataField
from tracpro.test import factories
from tracpro.test.cases import TracProTest
from tracpro.trackers.models import Tracker

from .. import forms


class TestTrackerForm(TracProTest):
    def setUp(self):
        super(TestTrackerForm, self).setUp()

        self.org = factories.Org()

        region = factories.Region()
        data_field = factories.DataField(value_type=DataField.TYPE_NUMERIC)
        # Data to pass to form for testing.
        self.data = {
            'region': region.pk,
            'contact_field': data_field.pk,
            'reporting_period': Tracker.WEEKLY,
            'minimum_group_threshold': 1000,
            'target_group_threshold': 2000,
            'maximum_group_threshold': 3000,
            'group_threshold_emails': 'test1@test.com',
            'minimum_contact_threshold': 10,
            'target_contact_threshold': 20,
            'maximum_contact_threshold': 30,
            'contact_threshold_emails': 'test2@test.com',
            'emails': 'test3@test.com',
        }

    def test_form_valid(self):
        form = forms.TrackerForm(data=self.data)
        self.assertTrue(form.is_valid())

    def test_validate_minimum_thresholds(self):
        self.data['minimum_group_threshold'] = 2500
        self.data['minimum_contact_threshold'] = 25
        form = forms.TrackerForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {
            'minimum_group_threshold': ["The Minimum group threshold should be less than the Target group threshold"],
            'minimum_contact_threshold': [
                "The Minimum contact threshold should be less than the Target contact threshold"],
        })

    def test_validate_maximum_thresholds(self):
        self.data['maximum_group_threshold'] = 1500
        self.data['maximum_contact_threshold'] = 15
        form = forms.TrackerForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {
            'maximum_group_threshold': [
                "The Maximum group threshold should be greater than the Target group threshold"],
            'maximum_contact_threshold': [
                "The Maximum contact threshold should be greater than the Target contact threshold"],
        })

    def test_invalid_choice(self):
        self.data['contact_field'] = factories.DataField(value_type=DataField.TYPE_TEXT).pk
        form = forms.TrackerForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {
            'contact_field': ['Select a valid choice. That choice is not one of the available choices.'],
        })
