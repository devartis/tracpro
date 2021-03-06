from __future__ import absolute_import, unicode_literals

import datetime
from dash.utils.sync import ChangeType, sync_push_contact
from django.conf import settings
from django.core.mail import send_mail
from djcelery_transactions import task

from tracpro.contacts.models import Contact
from tracpro.orgs_ext.tasks import OrgTask


class CreateSnapshots(OrgTask):
    def org_task(self, org, **kwargs):
        for tracker in org.trackers.all():
            tracker.create_snapshots()


class ApplyGroupRules(OrgTask):
    def org_task(self, org, **kwargs):
        Contact.objects.sync(org)

        for tracker in org.trackers.all():
            updated_contacts = tracker.apply_group_rules()
            for contact in updated_contacts:
                sync_push_contact(org, contact, ChangeType.updated, contact.as_temba().groups)


class SendAlertThresholdEmails(OrgTask):
    def sent_alert_threshold_email(self, message, recipient_list):
        send_mail(
            subject="Alert thresholds are met",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list.split(', '),
            fail_silently=True)

    def org_task(self, org, **kwargs):
        for tracker in org.trackers.all():
            for snapshot in tracker.snapshots_below_or_at_minimum():
                msg = 'The value %s is less than minimum contact threshold' % snapshot.contact_field_value
                self.sent_alert_threshold_email(msg, tracker.contact_threshold_emails)

            for snapshot in tracker.snapshots_over_or_at_maximum():
                msg = 'The value %s is greater than maximum contact threshold' % snapshot.contact_field_value
                self.sent_alert_threshold_email(msg, tracker.contact_threshold_emails)

            total_group_sum = self.total_group_sum()
            if tracker.under_group_minimum():
                msg = 'The sum of the individual values %s is less than minimum group threshold' % total_group_sum
                self.sent_alert_threshold_email(msg, tracker.group_threshold_emails)

            if tracker.over_group_maximum():
                msg = 'The sum of the individual values %s is greater than maximum group threshold' % total_group_sum
                self.sent_alert_threshold_email(msg, tracker.group_threshold_emails)


class ReportEmails(OrgTask):
    def org_task(self, org, **kwargs):
        for tracker in org.trackers.filter(reporting_period=kwargs.get('period')):
            self.send_report_emails(tracker)

            updated_contacts = tracker.reset_contact_fields()
            for contact in updated_contacts:
                sync_push_contact(org, contact, ChangeType.updated, contact.as_temba().groups)

    def send_report_emails(self, tracker):
        msg = self.report_email_for(tracker, self.minimum_and_maximum_values(tracker))
        self.sent_report_email(tracker, msg)

        msg = self.report_email_for(tracker, self.target_values(tracker))
        self.sent_report_email(tracker, msg)

    def sent_report_email(self, tracker, msg):
        today = datetime.date.today()
        send_mail(
            subject="Reporting Period %s - %s" % (today - tracker.reporting_period, today),
            message=msg,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=tracker.emails.split(', '),
            fail_silently=True)

    def report_email_for(self, tracker, numbers):
        added = self.contacts_by_group(tracker.contact_actions_of_period('add'), 'added to')
        removed = self.contacts_by_group(tracker.contact_actions_of_period('remove'), 'removed from')
        msg = """
                Group: {group}
                Contact Field: {contact_field}

                {numbers}

                --------------------------------------------------

                In this reporting period:

                """.format(group=tracker.region.name, contact_field=tracker.contact_field.label, numbers=numbers)
        msg += added + removed
        return msg

    def contacts_by_group(self, contact_actions_by_group, action):
        contacts_by_group = ''
        for contact_action in contact_actions_by_group:
            contacts_by_group += '%s contacts %s %s\n' % (contact_action['cant_contacts'], action,
                                                          contact_action['group__name'])
        return contacts_by_group

    def minimum_and_maximum_values(self, tracker):
        below = tracker.today_snapshots_below_minimum().count()
        at_minimum = tracker.today_snapshots_at_minimum().count()
        between = tracker.today_snapshots_between_minimum_and_maximum().count()
        at_maximum = tracker.today_snapshots_at_maximum().count()
        above = tracker.today_snapshots_above_maximum().count()
        minimum_and_maximum_numbers = """
                Minimum : {minimum}
                Maximum: {maximum}

                {below} below the minimum value
                {at_minimum} at minimum value
                {between} between minimum and maximum value
                {at_maximum} at maximum value
                {above} above maximum value
                """.format(minimum=tracker.minimum_contact_threshold, maximum=tracker.maximum_contact_threshold,
                           below=below, at_minimum=at_minimum, between=between, at_maximum=at_maximum, above=above)
        return minimum_and_maximum_numbers

    def target_values(self, tracker):
        below_target = tracker.today_snapshots_below_target().count()
        at_target = tracker.today_snapshots_at_target().count()
        above_target = tracker.today_snapshots_above_target().count()
        target_numbers = """
                Target : {target}

                {below_target} below the target
                {at_target} at the target
                {above_target} above the target
                """.format(target=tracker.target_contact_threshold, below_target=below_target,
                           at_target=at_target, above_target=above_target)
        return target_numbers


@task
def create_occurrence_trigger_the_alert_action(contact):
    print "We should check if group membership has changed, and we have an alert related to this particular change."
