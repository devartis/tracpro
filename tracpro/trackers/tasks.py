from __future__ import absolute_import, unicode_literals

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
        Contact.objects.sync()

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
            for snapshot in tracker.snapshots_below_minimum():
                msg = 'The value %s is less than minimum contact threshold' % snapshot.contact_field_value
                self.sent_alert_threshold_email(msg, tracker.contact_threshold_emails)

            for snapshot in tracker.snapshots_over_maximum():
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

    def send_report_email(self, tracker):
        msg = """This is a %s report email.

            Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas.
            Vestibulum tortor quam, feugiat vitae, ultricies eget, tempor sit amet, ante. Donec eu libero
            sit amet quam egestas semper. Aenean ultricies mi vitae est. Mauris placerat eleifend leo.
            Quisque sit amet est et sapien ullamcorper pharetra. Vestibulum erat wisi, condimentum sed,
            commodo vitae, ornare sit amet, wisi. Aenean fermentum, elit eget tincidunt condimentum, eros
            ipsum rutrum orci, sagittis tempus lacus enim ac dui. Donec non enim in turpis pulvinar
            facilisis. Ut felis. Praesent dapibus, neque id cursus faucibus, tortor neque egestas augue, eu
            vulputate magna eros eu erat. Aliquam erat volutpat. Nam dui mi, tincidunt quis, accumsan
            porttitor, facilisis luctus, metus""" % tracker.get_str_reporting_period()
        send_mail(
            subject="Report",
            message=msg,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=tracker.emails.split(', '),
            fail_silently=True)    

    def org_task(self, org, **kwargs):
        for tracker in org.trackers.filter(reporting_period=kwargs.get('period')):
            self.send_report_email(tracker)

            updated_contacts = tracker.reset_contact_fields()
            for contact in updated_contacts:
                sync_push_contact(org, contact, ChangeType.updated, contact.as_temba().groups)


@task
def create_occurrence_trigger_the_alert_action(contact):
    print "We should check if group membership has changed, and we have an alert related to this particular change."
