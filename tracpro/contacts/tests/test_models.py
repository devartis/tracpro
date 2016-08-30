from __future__ import absolute_import, unicode_literals

import datetime
from decimal import Decimal

import pytz

from temba_client.types import Contact as TembaContact

from django.test.utils import override_settings
from django.utils import timezone
from dash.utils.sync import ChangeType

from tracpro.polls.models import Response
from tracpro.test import factories
from tracpro.test.cases import TracProDataTest, TracProTest

from .. import models


class ContactTest(TracProDataTest):

    @override_settings(
        CELERY_ALWAYS_EAGER=True,
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        BROKER_BACKEND='memory',
    )
    def test_create(self):
        self.mock_temba_client.create_contact.return_value = TembaContact.create(
            uuid='C-007',
            name="Mo Polls",
            urns=['tel:078123'],
            groups=['G-001', 'G-005'],
            fields={},
            language='eng',
            modified_on=timezone.now(),
        )

        contact = factories.Contact(
            name="Mo Polls",
            org=self.unicef,
            created_by=self.user1,
            modified_by=self.user1,
            urn="tel:078123",
            region=self.region1,
            group=self.group1,
            language="eng",
        )

        self.assertEqual(contact.name, "Mo Polls")
        self.assertEqual(contact.urn, 'tel:078123')
        self.assertEqual(contact.region, self.region1)
        self.assertEqual(contact.language, 'eng')
        self.assertEqual(contact.created_by, self.user1)
        self.assertIsNotNone(contact.created_on)
        self.assertEqual(contact.modified_by, self.user1)
        self.assertIsNotNone(contact.modified_on)

        contact.push(ChangeType.created)

        # reload and check UUID was updated by push task
        contact.refresh_from_db()
        self.assertEqual(contact.uuid, 'C-007')

        self.assertEqual(self.mock_temba_client.create_contact.call_count, 1)

    def test_get_or_fetch(self):
        self.mock_temba_client.get_contact.return_value = TembaContact.create(
            uuid='C-007', name="Mo Polls",
            urns=['tel:078123'], groups=['G-001', 'G-005'],
            fields={},
            language='eng', modified_on=timezone.now())
        # get locally
        contact = models.Contact.get_or_fetch(self.unicef, 'C-001')
        self.assertEqual(contact.name, "Ann")

        # fetch remotely
        contact = models.Contact.get_or_fetch(self.unicef, 'C-009')
        self.assertEqual(contact.name, "Mo Polls")

    def test_kwargs_from_temba(self):
        modified_date = timezone.now()
        temba_contact = TembaContact.create(
            uuid='C-007',
            name="Jan",
            urns=['tel:123'],
            groups=['G-001', 'G-007'],
            fields={
                'gender': 'M',
            },
            language='eng',
            modified_on=modified_date,
        )

        kwargs = models.Contact.kwargs_from_temba(self.unicef, temba_contact)
        self.assertDictEqual(kwargs, {
            'uuid': 'C-007',
            'org': self.unicef,
            'name': "Jan",
            'urn': 'tel:123',
            'region': self.region1,
            'group': self.group5,
            'language': 'eng',
            'temba_modified_on': modified_date,
            '_data_field_values': {
                'gender': 'M',
            },
        })

        # try creating contact from them
        models.Contact.objects.create(**kwargs)

    def test_as_temba(self):
        temba_contact = self.contact1.as_temba()
        self.assertEqual(temba_contact.name, "Ann")
        self.assertEqual(temba_contact.urns, ['tel:1234'])
        self.assertEqual(temba_contact.fields, {})
        self.assertEqual(temba_contact.groups, ['G-005', 'G-001'])
        self.assertEqual(temba_contact.uuid, 'C-001')

    def test_by_org(self):
        self.assertEqual(len(models.Contact.objects.active().by_org(self.unicef)), 5)
        self.assertEqual(len(models.Contact.objects.active().by_org(self.nyaruka)), 1)

    def test_get_responses(self):
        date1 = datetime.datetime(2014, 1, 1, 7, tzinfo=pytz.UTC)
        date2 = datetime.datetime(2014, 1, 1, 8, tzinfo=pytz.UTC)
        pollrun1 = factories.UniversalPollRun(
            poll=self.poll1, conducted_on=date1)
        pollrun1_r1 = factories.Response(
            pollrun=pollrun1, contact=self.contact1,
            created_on=date1, updated_on=date1, status=Response.STATUS_COMPLETE)
        pollrun2 = factories.RegionalPollRun(
            poll=self.poll1, region=self.region1, conducted_on=date2)
        pollrun2_r1 = factories.Response(
            pollrun=pollrun2, contact=self.contact1,
            created_on=date2, updated_on=date2, status=Response.STATUS_EMPTY)

        self.assertEqual(list(self.contact1.get_responses().order_by('pk')),
                         [pollrun1_r1, pollrun2_r1])
        self.assertEqual(list(self.contact1.get_responses(include_empty=False).order_by('pk')),
                         [pollrun1_r1])

    @override_settings(
        CELERY_ALWAYS_EAGER=True,
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        BROKER_BACKEND='memory',
    )
    def test_delete(self):
        self.contact1.delete()
        self.assertFalse(self.contact1.is_active)

        self.assertEqual(self.mock_temba_client.delete_contact.call_count, 1)

    def test_str(self):
        self.assertEqual(str(self.contact1), "Ann")
        self.contact1.name = ""
        self.contact1.save()
        self.assertEqual(str(self.contact1), "1234")


class TestContactField(TracProTest):

    def _test_get_value(self, value_type, tests):
        contact_field = factories.ContactField(field__value_type=value_type)

        # get_value() will return None if value is None, regardless of type.
        contact_field.value = None
        self.assertEqual(contact_field.get_value(), None)

        # Set the value field directly, then test what get_value() returns.
        for value, expected in tests:
            contact_field.value = value
            self.assertEqual(contact_field.get_value(), expected)

    def test_get_value_text(self):
        """Value is returned as-is when data field type is textual."""
        self._test_get_value(models.DataField.TYPE_TEXT, (
            ("\u2603", "\u2603"),
            ("hello", "hello"),
            ("2015-09-15T21:32:56.349186", "2015-09-15T21:32:56.349186"),
            ("2015-09-15T21:32:56.349186+00:00", "2015-09-15T21:32:56.349186+00:00"),
            ("1.1", "1.1"),
            ("1", "1"),
        ))

    def test_get_value_state(self):
        """Value is returned as-is when data field type is textual."""
        self._test_get_value(models.DataField.TYPE_STATE, (
            ("\u2603", "\u2603"),
            ("hello", "hello"),
            ("2015-09-15T21:32:56.349186", "2015-09-15T21:32:56.349186"),
            ("2015-09-15T21:32:56.349186+00:00", "2015-09-15T21:32:56.349186+00:00"),
            ("1.1", "1.1"),
            ("1", "1"),
        ))

    def test_get_value_district(self):
        """Value is returned as-is when data field type is textual."""
        self._test_get_value(models.DataField.TYPE_DISTRICT, (
            ("\u2603", "\u2603"),
            ("hello", "hello"),
            ("2015-09-15T21:32:56.349186", "2015-09-15T21:32:56.349186"),
            ("2015-09-15T21:32:56.349186+00:00", "2015-09-15T21:32:56.349186+00:00"),
            ("1.1", "1.1"),
            ("1", "1"),
        ))

    def test_get_value_numeric(self):
        """If value cannot be cast as a Decimal, None is returned."""
        self._test_get_value(models.DataField.TYPE_NUMERIC, (
            ("\u2603", None),
            ("hello", None),
            ("2015-09-15T21:32:56.349186", None),
            ("2015-09-15T21:32:56.349186+00:00", None),
            ("1.1", Decimal("1.1")),
            ("1", Decimal("1")),
        ))

    def test_get_value_datetime(self):
        """If value cannot be parsed as a datetime, None is returned."""
        self._test_get_value(models.DataField.TYPE_DATETIME, (
            ("\u2603", None),
            ("hello", None),
            ("2015-09-15T21:32:56.349186",
             datetime.datetime(2015, 9, 15, 21, 32, 56, 349186)),
            ("2015-09-15T21:32:56.349186+00:00",
             datetime.datetime(2015, 9, 15, 21, 32, 56, 349186, tzinfo=pytz.UTC)),
            ("1.1", None),
            ("1", None),
        ))

    def test_set_value(self):
        """set_value() serializes values as unicode."""
        contact_field = factories.ContactField()

        contact_field.set_value(None)
        self.assertEqual(contact_field.value, None)

        contact_field.set_value("\u2603")
        self.assertEqual(contact_field.value, "\u2603")

        contact_field.set_value("hello")
        self.assertEqual(contact_field.value, "hello")

        contact_field.set_value(datetime.datetime(2015, 9, 15, 21, 32, 56, 349186))
        self.assertEqual(contact_field.value, "2015-09-15T21:32:56.349186")

        contact_field.set_value(datetime.datetime(2015, 9, 15, 21, 32, 56, 349186, tzinfo=pytz.UTC))
        self.assertEqual(contact_field.value, "2015-09-15T21:32:56.349186+00:00")

        contact_field.set_value(1.1)
        self.assertEqual(contact_field.value, "1.1")

        contact_field.set_value(1)
        self.assertEqual(contact_field.value, "1")

    def test_str(self):
        """Smoke test for string representation."""
        contact_field = factories.ContactField(
            contact__name="Sam",
            field__label="Data Field",
            value="hello",
        )
        self.assertEqual(str(contact_field), "Sam Data Field: hello")
