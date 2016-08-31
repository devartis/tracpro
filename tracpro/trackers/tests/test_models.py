# coding=utf-8
from __future__ import absolute_import, unicode_literals

from tracpro.test import factories
from tracpro.test.cases import TracProDataTest
from tracpro.trackers.models import Tracker, TrackerOccurrence, Snapshot
from tracpro.trackers.tests.factories import Alert, AlertRule


class TestTracker(TracProDataTest):
    def test_str(self):
        """Smoke test for string representation."""
        region_name = 'Narnia'
        region = factories.Region(name=region_name)
        label = 'Tracker1'
        contact_field = factories.DataField(label=label)
        tracker = factories.Tracker(region=region, contact_field=contact_field, reporting_period=Tracker.DAILY)
        self.assertEqual(str(tracker), '%s - %s' % (region_name, label))

    def test_snapshots_creation(self):
        data_field = factories.DataField(org=self.unicef)
        tracker = factories.Tracker(org=self.unicef, contact_field=data_field, region=self.region1)

        contact_field1 = factories.ContactField(contact=self.contact1, field=data_field, value=5)
        contact_field2 = factories.ContactField(contact=self.contact2, field=data_field, value=10)

        tracker.create_snapshots()
        self.assertEqual(Snapshot.objects.count(), 2)

        snapshot = Snapshot.objects.all().first()
        self.assertEqual(snapshot.contact_field, contact_field2)
        self.assertEqual(snapshot.contact_field_value, '10')
        snapshot = Snapshot.objects.all().last()
        self.assertEqual(snapshot.contact_field, contact_field1)
        self.assertEqual(snapshot.contact_field_value, '5')

    def test_reset_contact_fields(self):
        data_field = factories.DataField(org=self.unicef)
        tracker = factories.Tracker(org=self.unicef, contact_field=data_field, region=self.region1)

        factories.ContactField(contact=self.contact1, field=data_field)
        factories.ContactField(contact=self.contact2, field=data_field)
        factories.ContactField(contact=self.contact3, field=data_field)

        tracker.reset_contact_fields()

        for contact_field in tracker.related_contact_fields():
            self.assertEqual(contact_field.value, '0')


class GroupRuleTracker(TracProDataTest):
    def test_apply_group_rule_for_add_action(self):
        action = 'add'
        group = factories.Group(uuid='abc')
        region = factories.Region(uuid='abc')

        tracker = factories.Tracker(org=self.unicef)
        group_rule = factories.GroupRule(action=action, region=region, tracker=tracker)

        alert = Alert(org=self.unicef)
        alert_rule = AlertRule(alert=alert, action=action, group=group)

        contact = factories.Contact()
        group_rule.apply_for(contact)

        self.assertEqual(TrackerOccurrence.objects.count(), 1)

        tracker_occurrence = TrackerOccurrence.objects.all().first()
        self.assertEqual(tracker_occurrence.contact, contact)
        self.assertEqual(tracker_occurrence.tracker, tracker)
        self.assertIn(alert_rule, tracker_occurrence.alert_rules.all())

        self.assertIn(contact, group.all_contacts.all())

    def test_apply_group_rule_for_remove_action(self):
        action = 'remove'
        group = factories.Group(uuid='abc')
        region = factories.Region(uuid='abc')
        tracker = factories.Tracker(org=self.unicef)
        group_rule = factories.GroupRule(action=action, region=region, tracker=tracker)

        alert = Alert(org=self.unicef)
        alert_rule = AlertRule(alert=alert, action=action, group=group)

        contact = factories.Contact()
        group_rule.apply_for(contact)

        self.assertEqual(TrackerOccurrence.objects.count(), 1)

        tracker_occurrence = TrackerOccurrence.objects.all().first()
        self.assertEqual(tracker_occurrence.contact, contact)
        self.assertEqual(tracker_occurrence.tracker, tracker)
        self.assertIn(alert_rule, tracker_occurrence.alert_rules.all())

        self.assertNotIn(contact, group.all_contacts.all())
