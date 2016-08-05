from __future__ import absolute_import, unicode_literals

import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class Tracker(models.Model):
    DAILY = datetime.timedelta(days=1)
    WEEKLY = datetime.timedelta(days=7)
    FORTNIGHTLY = datetime.timedelta(days=14)
    MONTHLY = datetime.timedelta(days=30)
    QUARTERLY = datetime.timedelta(days=90)
    REPORTING_PERIOD_CHOICES = (
        (DAILY, _('Daily')),
        (WEEKLY, _('Weekly')),
        (FORTNIGHTLY, _('Fortnightly')),
        (MONTHLY, _('Monthly')),
        (QUARTERLY, _('Quarterly'))
    )

    org = models.ForeignKey('orgs.Org', verbose_name=_("Org"), related_name='trackers')
    region = models.ForeignKey('groups.Region', verbose_name=_("Region"), related_name='trackers')
    contact_field = models.ForeignKey('contacts.DataField')
    reporting_period = models.DurationField(max_length=2, choices=REPORTING_PERIOD_CHOICES)
    minimum_group_threshold = models.IntegerField(null=True, blank=True)
    target_group_threshold = models.IntegerField()
    maximum_group_threshold = models.IntegerField(null=True, blank=True)
    group_threshold_emails = models.TextField()
    minimum_contact_threshold = models.IntegerField(null=True, blank=True)
    target_contact_threshold = models.IntegerField()
    maximum_contact_threshold = models.IntegerField(null=True, blank=True)
    contact_threshold_emails = models.TextField()
    emails = models.TextField()

    def clean_fields(self, exclude=None):
        super(Tracker, self).clean_fields(exclude)
        if self.minimum_group_threshold is None and self.maximum_group_threshold is None \
                and self.minimum_contact_threshold is None and self.maximum_contact_threshold is None:
            raise ValidationError("""At least one of these values is required:
            Minimum contact threshold, Maximum group threshold, Minimum contact threshold, Maximum contact threshold""")

        errors = {}
        if self.minimum_group_threshold is not None and (self.minimum_group_threshold > self.target_group_threshold):
            errors[
                'minimum_group_threshold'] = "The Minimum group threshold should be less than the Target group threshold"

        if self.maximum_group_threshold is not None and (self.maximum_group_threshold < self.target_group_threshold):
            errors[
                'maximum_group_threshold'] = "The Maximum group threshold should be greater than the Target group threshold"

        if self.minimum_contact_threshold is not None and \
                (self.minimum_contact_threshold > self.target_contact_threshold):
            errors['minimum_contact_threshold'] = "The Minimum contact threshold should be less than the Target contact threshold"

        if self.maximum_contact_threshold is not None and \
                (self.maximum_contact_threshold < self.target_contact_threshold):
            errors['maximum_contact_threshold'] = "The Maximum contact threshold should be greater than the Target contact threshold"
        raise ValidationError(errors)

    def __str__(self):
        return self.contact_field.label

    def __unicode__(self):
        return self.contact_field.label


@python_2_unicode_compatible
class GroupRule(models.Model):
    ACTION_CHOICES = (
        ('add', _('Add')),
        ('remove', _('Remove'))
    )
    CONDITION_CHOICES = (
        ('gt', _('Greater')),
        ('lt', _('Less'))
    )
    THRESHOLD_CHOICES = (
        ('GMax', _('Group Maximum')),
        ('GMin', _('Group Minimum')),
        ('CMax', _('Contact Maximum')),
        ('CMin', _('Contact Minimum'))
    )
    action = models.CharField(max_length=6, choices=ACTION_CHOICES)
    region = models.ForeignKey('groups.Region', verbose_name=_("Region"), related_name='group_rules')
    condition = models.CharField(max_length=7, choices=CONDITION_CHOICES)
    threshold = models.CharField(max_length=4, choices=THRESHOLD_CHOICES)
    tracker = models.ForeignKey(Tracker, verbose_name=_("Tracker"), related_name='group_rules')

    def __str__(self):
        return self.region.name

    def get_threshold_value(self):
        threshold_mapper = {
            'GMax': 'maximum_group_threshold',
            'GMin': 'minimum_group_threshold',
            'CMax': 'maximum_contact_threshold',
            'CMin': 'minimum_contact_threshold',
        }
        return getattr(self.tracker, threshold_mapper[self.threshold])


@python_2_unicode_compatible
class Snapshot(models.Model):
    contact_field = models.ForeignKey('contacts.ContactField', verbose_name=_("ContactField"), related_name='snapshots')
    contact_field_value = models.CharField(max_length=255, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s: %s (%s)' % (self.contact_field.field.label, self.contact_field_value, self.timestamp)
