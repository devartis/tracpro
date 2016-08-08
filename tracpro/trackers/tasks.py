from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from djcelery_transactions import task

from tracpro.contacts.models import Contact
from tracpro.contacts.tasks import SyncOrgContacts
from tracpro.orgs_ext.tasks import OrgTask
from .models import Snapshot


class CreateSnapshots(OrgTask):
    def org_task(self, org):
        for tracker in org.trackers.all():
            for contact_field in tracker.related_contact_fields():
                Snapshot.objects.create(contact_field=contact_field, contact_field_value=contact_field.value)


class ApplyGroupRules(OrgTask):
    def org_task(self, org):
        SyncOrgContacts().delay(org.pk)

        temba_client = org.get_temba_client()
        for tracker in org.trackers.all():
            for group_rule in tracker.group_rules.all():
                snapshots = tracker.related_snapshots().filter(
                    Q(**{'contact_field_value__' + group_rule.condition: group_rule.get_threshold_value()}))

                group_rule_region = group_rule.region.uuid
                for snapshot in snapshots:
                    contact = snapshot.contact_field.contact
                    temba_contact = contact.as_temba()

                    fields = {f.field.key: f.value for f in contact.contactfield_set.all() if f.value}
                    groups = temba_client.get_contact(uuid=temba_contact.uuid).groups
                    if group_rule.action == 'add':
                        groups.append(group_rule_region)
                    else:
                        if group_rule_region in groups:
                            groups.remove(group_rule_region)
                    temba_client.update_contact(uuid=temba_contact.uuid, name=temba_contact.name,
                                                urns=temba_contact.urns, fields=fields,
                                                groups=groups)


class SendAlertThresholdEmails(OrgTask):
    def org_task(self, org):
        for tracker in org.trackers.all():
            snapshots = tracker.related_snapshots()

            for snapshot in snapshots.filter(contact_field_value__lte=tracker.minimum_contact_threshold):
                msg = 'The value %s is less than minimum contact threshold' % snapshot.contact_field_value
                sent_alert_threshold_email(msg, tracker.contact_threshold_emails)

            for snapshot in snapshots.filter(contact_field_value__gte=tracker.maximum_contact_threshold):
                msg = 'The value %s is greater than maximum contact threshold' % snapshot.contact_field_value
                sent_alert_threshold_email(msg, tracker.contact_threshold_emails)

            total_group_sum = 0
            for value in snapshots.values_list('contact_field_value', flat=True):
                total_group_sum += int(value)
            if total_group_sum <= tracker.minimum_group_threshold:
                msg = 'The sum of the individual values %s is less than minimum group threshold' % total_group_sum
                sent_alert_threshold_email(msg, tracker.group_threshold_emails)
            if total_group_sum >= tracker.maximum_group_threshold:
                msg = 'The sum of the individual values %s is greater than maximum group threshold' % total_group_sum
                sent_alert_threshold_email(msg, tracker.group_threshold_emails)


def sent_alert_threshold_email(message, recipient_list):
    send_mail(
        subject="Alert thresholds are met",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list.split(', '),
        fail_silently=True)


class ReportEmails(OrgTask):
    def org_task(self, org):
        temba_client = org.get_temba_client()
        for tracker in org.trackers.all():
            send_report_email(tracker)

            contact_fields = tracker.related_contact_fields()
            for contact_field in contact_fields:
                contact_field.value = 0
                contact_field.save()

            for id in contact_fields.values_list('contact', flat=True).distinct():
                contact = Contact.objects.get(id=id)
                temba_contact = contact.as_temba()
                fields = {f.field.key: f.value for f in contact.contactfield_set.all() if f.value}
                groups = temba_client.get_contact(uuid=temba_contact.uuid).groups
                temba_client.update_contact(uuid=temba_contact.uuid, name=temba_contact.name,
                                            urns=temba_contact.urns, fields=fields,
                                            groups=groups)


def send_report_email(tracker):
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


@task
def create_occurrence_trigger_the_alert_action(contact):
    print "We should check if group membership has changed, and we have an alert related to this particular change."
