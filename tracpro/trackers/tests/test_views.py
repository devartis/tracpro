# coding=utf-8
from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse

from tracpro.contacts.models import DataField
from tracpro.test import factories
from tracpro.test.cases import TracProDataTest
from tracpro.trackers.models import Tracker, GroupRule, ADD, REMOVE


class TrackerCRUDLTest(TracProDataTest):
    def setUp(self):
        super(TrackerCRUDLTest, self).setUp()
        factories.Tracker(org=self.unicef)

        self.region = factories.Region()
        data_field = factories.DataField(value_type=DataField.TYPE_NUMERIC)
        # Data to pass to form for testing.
        self.data = {
            'org': self.unicef.pk,
            'region': self.region.pk,
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

            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0'
        }
        self.data_for_formset = {
            'form-0-condition': GroupRule.GREATER,
            'form-0-action': ADD,
            'form-0-region': self.region.pk,
            'form-0-threshold': GroupRule.GROUP_MAXIMUM,
            'form-1-condition': GroupRule.LESS,
            'form-1-action': REMOVE,
            'form-1-region': self.region.pk,
            'form-1-threshold': GroupRule.GROUP_MINIMUM,
        }
        self.data_for_formset.update(self.data)

    def test_list(self):
        url = reverse('trackers.tracker_list')

        # log in as admin
        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

    def test_create_tracker(self):
        url = reverse('trackers.tracker_create')
        # Log in as an org administrator
        self.login(self.admin)
        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)

        # Submit with no fields entered
        response = self.url_post('unicef', url, {})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'region', 'This field is required.')

        # Submit with form data
        response = self.url_post('unicef', url, self.data)
        self.assertEqual(response.status_code, 302)

        # Check new Tracker created successfully
        tracker = Tracker.objects.all().last()
        self.assertEqual(tracker.reporting_period, Tracker.WEEKLY)

    def test_create_tracker_with_group_rules(self):
        url = reverse('trackers.tracker_create')
        # Log in as an org administrator
        self.login(self.admin)

        # Submit with form data
        response = self.url_post('unicef', url, self.data_for_formset)
        self.assertEqual(response.status_code, 302)

        # Check new GroupRules created successfully
        self.assertEqual(GroupRule.objects.count(), 2)

        group_rule1 = GroupRule.objects.all().first()
        group_rule2 = GroupRule.objects.all().last()
        self.assertEqual(group_rule1.action, ADD)
        self.assertEqual(group_rule1.condition, GroupRule.GREATER)
        self.assertEqual(group_rule1.region, self.region)
        self.assertEqual(group_rule1.threshold, GroupRule.GROUP_MAXIMUM)
        self.assertEqual(group_rule2.action, REMOVE)
        self.assertEqual(group_rule2.condition, GroupRule.LESS)
        self.assertEqual(group_rule2.region, self.region)
        self.assertEqual(group_rule2.threshold, GroupRule.GROUP_MINIMUM)

    def test_update_group_rule(self):
        # create
        url = reverse('trackers.tracker_create')
        self.login(self.admin)
        response = self.url_post('unicef', url, self.data_for_formset)
        self.assertEqual(response.status_code, 302)
        tracker = Tracker.objects.all().last()

        # update
        url = reverse('trackers.tracker_update', args=[tracker.pk])

        self.data_for_formset['form-1-action'] = ''
        response = self.url_post('unicef', url, self.data_for_formset)
        self.assertEqual(response.status_code, 200)
        self.assertFormsetError(response, 'group_rule_formset', 1, 'action', 'This field is required.')

    def test_update_tracker_with_group_rules(self):
        # create
        url = reverse('trackers.tracker_create')
        self.login(self.admin)
        response = self.url_post('unicef', url, self.data_for_formset)
        self.assertEqual(response.status_code, 302)
        tracker = Tracker.objects.all().last()
        group_rules_ids = list(tracker.group_rules.all().values_list('id', flat=True))

        # update
        url = reverse('trackers.tracker_update', args=[tracker.pk])

        changed_data = {'form-TOTAL_FORMS': '3',
                        'form-INITIAL_FORMS': '2',
                        'form-0-DELETE': 'on',
                        'form-1-DELETE': '',
                        'form-2-DELETE': '',
                        'form-0-id': group_rules_ids[0],
                        'form-1-id': group_rules_ids[1],
                        'form-2-id': '',
                        'form-1-action': ADD,
                        'form-2-action': REMOVE,
                        'form-2-condition': GroupRule.GREATER,
                        'form-2-region': self.region.pk,
                        'form-2-threshold': GroupRule.CONTACT_MAXIMUM
                        }

        self.data_for_formset.update(changed_data)

        response = self.url_post('unicef', url, self.data_for_formset)
        self.assertEqual(response.status_code, 302)

        # Check groups rules amount ( 1 created, 1 modified, 1 deleted )
        self.assertEqual(GroupRule.objects.count(), 2)

        # modified group rule
        group_rule1 = GroupRule.objects.all().first()
        self.assertEqual(group_rule1.action, ADD)

        # created group rule
        group_rule2 = GroupRule.objects.all().last()
        self.assertEqual(group_rule2.action, REMOVE)
        self.assertEqual(group_rule2.condition, GroupRule.GREATER)
        self.assertEqual(group_rule2.region, self.region)
        self.assertEqual(group_rule2.threshold, GroupRule.CONTACT_MAXIMUM)
