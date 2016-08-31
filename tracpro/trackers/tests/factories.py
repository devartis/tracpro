from __future__ import unicode_literals

import factory
import factory.fuzzy

from tracpro.test.factory_utils import FuzzyEmail
from .. import models


class Tracker(factory.django.DjangoModelFactory):
    org = factory.SubFactory("tracpro.test.factories.Org")
    region = factory.SubFactory("tracpro.test.factories.Region")
    contact_field = factory.SubFactory("tracpro.test.factories.DataField")
    reporting_period = factory.fuzzy.FuzzyChoice(c[0] for c in models.Tracker.REPORTING_PERIOD_CHOICES)
    minimum_group_threshold = factory.fuzzy.FuzzyInteger(0)
    target_group_threshold = factory.fuzzy.FuzzyInteger(0)
    maximum_group_threshold = factory.fuzzy.FuzzyInteger(0)
    group_threshold_emails = FuzzyEmail()
    minimum_contact_threshold = factory.fuzzy.FuzzyInteger(0)
    target_contact_threshold = factory.fuzzy.FuzzyInteger(0)
    maximum_contact_threshold = factory.fuzzy.FuzzyInteger(0)
    contact_threshold_emails = FuzzyEmail()
    emails = FuzzyEmail()

    class Meta:
        model = models.Tracker


class GroupRule(factory.django.DjangoModelFactory):
    region = factory.SubFactory("tracpro.test.factories.Region")
    tracker = factory.SubFactory("tracpro.test.factories.Tracker")
    action = factory.fuzzy.FuzzyChoice(c[0] for c in models.GroupRule.ACTION_CHOICES)
    condition = factory.fuzzy.FuzzyChoice(c[0] for c in models.GroupRule.CONDITION_CHOICES)
    threshold = factory.fuzzy.FuzzyChoice(c[0] for c in models.GroupRule.THRESHOLD_CHOICES)

    class Meta:
        model = models.GroupRule


class Snapshot(factory.django.DjangoModelFactory):
    contact_field = factory.SubFactory("tracpro.test.factories.ContactField")
    contact_field_value = factory.fuzzy.FuzzyText()

    class Meta:
        model = models.Snapshot


class TrackerOccurrence(factory.django.DjangoModelFactory):
    contact = factory.SubFactory("tracpro.test.factories.Contact")
    group = factory.SubFactory("tracpro.test.factories.Group")
    tracker = factory.SubFactory("tracpro.test.factories.Tracker")
    action = factory.fuzzy.FuzzyChoice(c[0] for c in models.TrackerOccurrence.ACTION_CHOICES)

    class Meta:
        model = models.TrackerOccurrence


class Alert(factory.django.DjangoModelFactory):
    org = factory.SubFactory("tracpro.test.factories.Org")
    name = factory.fuzzy.FuzzyText()

    class Meta:
        model = models.Alert


class AlertRule(factory.django.DjangoModelFactory):
    alert = factory.SubFactory("tracpro.test.factories.Alert")
    flow = factory.SubFactory("tracpro.test.factories.Poll")
    region = factory.SubFactory("tracpro.test.factories.Region")
    group = factory.SubFactory("tracpro.test.factories.Group")
    action = factory.fuzzy.FuzzyChoice(c[0] for c in models.AlertRule.ACTION_CHOICES)

    class Meta:
        model = models.AlertRule
