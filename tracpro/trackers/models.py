from __future__ import absolute_import, unicode_literals

import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Count
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from tracpro.contacts.models import ContactField
from tracpro.groups.models import Group


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
        if self.minimum_group_threshold is not None and (self.minimum_group_threshold >= self.target_group_threshold):
            errors[
                'minimum_group_threshold'] = "The Minimum group threshold should be less than the Target group threshold"

        if self.maximum_group_threshold is not None and (self.maximum_group_threshold <= self.target_group_threshold):
            errors[
                'maximum_group_threshold'] = "The Maximum group threshold should be greater than the Target group threshold"

        if self.minimum_contact_threshold is not None and \
                (self.minimum_contact_threshold >= self.target_contact_threshold):
            errors['minimum_contact_threshold'] = "The Minimum contact threshold should be less than the Target contact threshold"

        if self.maximum_contact_threshold is not None and \
                (self.maximum_contact_threshold <= self.target_contact_threshold):
            errors['maximum_contact_threshold'] = "The Maximum contact threshold should be greater than the Target contact threshold"
        raise ValidationError(errors)

    def __str__(self):
        return self.contact_field.label

    def __unicode__(self):
        return self.contact_field.label

    def related_snapshots(self):
        # TODO: change __in
        return Snapshot.objects.filter(contact_field__field=self.contact_field,
                                       contact_field__contact__in=self.region.contacts.all())

    def today_related_snapshots(self):
        today = datetime.date.today()
        return self.related_snapshots().filter(timestamp__year=today.year, timestamp__month=today.month,
                                               timestamp__day=today.day)

    def related_contact_fields(self):
        return ContactField.objects.filter(field=self.contact_field, contact__in=self.region.contacts.all())

    def get_str_reporting_period(self):
        return dict(Tracker.REPORTING_PERIOD_CHOICES)[self.reporting_period]

    def create_snapshots(self):
        for contact_field in self.related_contact_fields():
            Snapshot.objects.create(contact_field=contact_field, contact_field_value=contact_field.value)

    def apply_group_rules(self):
        modified_contacts = []
        for group_rule in self.group_rules.all():
            snapshots = self.related_snapshots().filter(
                Q(**{'contact_field_value__' + group_rule.condition: group_rule.get_threshold_value()}))

            for snapshot in snapshots:
                contact = snapshot.contact_field.contact
                group_rule.apply_for(contact)

                modified_contacts.append(contact)
        return set(modified_contacts)

    def reset_contact_fields(self):
        updated_contacts = []
        contact_fields = self.related_contact_fields()
        for contact_field in contact_fields:
            contact_field.value = 0
            contact_field.save()
            updated_contacts.append(contact_field.contact)
        return set(updated_contacts)

    def snapshots_below_or_at_minimum(self):
        return self.related_snapshots().filter(contact_field_value__lte=self.minimum_contact_threshold)

    def snapshots_over_or_at_maximum(self):
        return self.related_snapshots().filter(contact_field_value__gte=self.maximum_contact_threshold)

    def under_group_minimum(self):
        total_group_sum = self.total_group_sum()
        return total_group_sum <= self.minimum_group_threshold

    def over_group_maximum(self):
        total_group_sum = self.total_group_sum()
        return total_group_sum >= self.maximum_group_threshold

    def total_group_sum(self):
        total_group_sum = 0
        for value in self.related_snapshots().values_list('contact_field_value', flat=True):
            total_group_sum += int(value)
        return total_group_sum

    def today_snapshots_below_minimum(self):
        return self.today_related_snapshots().filter(contact_field_value__lt=self.minimum_contact_threshold)

    def today_snapshots_at_minimum(self):
        return self.today_related_snapshots().filter(contact_field_value=self.minimum_contact_threshold)

    def today_snapshots_between_minimum_and_maximum(self):
        return self.today_related_snapshots().filter(contact_field_value__gt=self.minimum_contact_threshold).filter(
            contact_field_value__lt=self.maximum_contact_threshold)

    def today_snapshots_at_maximum(self):
        return self.today_related_snapshots().filter(contact_field_value=self.maximum_contact_threshold)

    def today_snapshots_above_maximum(self):
        return self.today_related_snapshots().filter(contact_field_value__gt=self.maximum_contact_threshold)

    def today_snapshots_below_target(self):
        return self.today_related_snapshots().filter(contact_field_value__lt=self.target_contact_threshold)

    def today_snapshots_at_target(self):
        return self.today_related_snapshots().filter(contact_field_value=self.target_contact_threshold)

    def today_snapshots_above_target(self):
        return self.today_related_snapshots().filter(contact_field_value__gt=self.target_contact_threshold)

    def contact_actions_of_period(self, action):
        start_of_period = datetime.datetime.today() - self.reporting_period
        contact_actions = self.contact_actions.filter(timestamp__gt=start_of_period, action=action)
        return contact_actions.values('group__name').annotate(cant_contacts=Count('group'))

    def set_org(self, org):
        self.org = org
        self.save()


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

    def apply_for(self, contact):
        group = Group.objects.get(uuid=self.region.uuid)
        if self.action == 'add':
            contact.groups.add(group)
        else:
            contact.groups.remove(group)
        TrackerOccurrence.objects.get_or_create(action=self.action, contact=contact, group=group,
                                                tracker=self.tracker)

    def set_tracker(self, tracker):
        self.tracker = tracker
        self.save()


@python_2_unicode_compatible
class Snapshot(models.Model):
    contact_field = models.ForeignKey('contacts.ContactField', verbose_name=_("ContactField"), related_name='snapshots')
    contact_field_value = models.CharField(max_length=255, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s: %s (%s)' % (self.contact_field.field.label, self.contact_field_value, self.timestamp)


@python_2_unicode_compatible
class TrackerOccurrence(models.Model):
    ACTION_CHOICES = (
        ('add', _('Add')),
        ('remove', _('Remove'))
    )
    action = models.CharField(max_length=6, choices=ACTION_CHOICES)
    contact = models.ForeignKey('contacts.Contact', verbose_name=_('Contact'), related_name='contact_actions')
    group = models.ForeignKey('groups.Group', verbose_name=_('Group'), related_name='contact_actions')
    tracker = models.ForeignKey(Tracker, verbose_name=_("Tracker"), related_name='contact_actions')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s %s to %s' % (self.action, self.contact, self.group)


@python_2_unicode_compatible
class Alert(models.Model):
    org = models.ForeignKey('orgs.Org', verbose_name=_("Org"), related_name='alerts')
    name = models.CharField(verbose_name=_("Name"), max_length=128, help_text=_("The name of this alert"))

    def __str__(self):
        return self.name

    def set_org(self, org):
        self.org = org
        self.save()


@python_2_unicode_compatible
class AlertRule(models.Model):
    ACTION_CHOICES = (
        ('add', _('Add')),
        ('remove', _('Remove'))
    )

    alert = models.ForeignKey(Alert, related_name='alert_rules')
    flow = models.ForeignKey('polls.Poll', related_name='alert_rules')
    region = models.ForeignKey('groups.Region', verbose_name=_("Region"), related_name='alert_rules')
    action = models.CharField(max_length=6, choices=ACTION_CHOICES)
    group = models.ForeignKey('groups.Group', related_name='alert_rules')
    last_executed = models.DateTimeField(null=True)

    def __str__(self):
        return self.flow

    def set_alert(self, alert):
        self.alert = alert
        self.save()
