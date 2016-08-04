from __future__ import absolute_import, unicode_literals

from django.db.models import Q

from tracpro.contacts.models import ContactField
from tracpro.contacts.tasks import SyncOrgContacts
from tracpro.orgs_ext.tasks import OrgTask
from .models import Snapshot


class CreateSnapshots(OrgTask):
    def org_task(self, org):
        for tracker in org.trackers.all():
            contact_fields = ContactField.objects.filter(field=tracker.contact_field,
                                                         contact__in=tracker.region.contacts.all())
            for contact_field in contact_fields:
                Snapshot.objects.create(contact_field=contact_field, contact_field_value=contact_field.value)


class ApplyGroupRules(OrgTask):
    def org_task(self, org):
        SyncOrgContacts().delay(org.pk)

        temba_client = org.get_temba_client()
        for tracker in org.trackers.all():
            for group_rule in tracker.group_rules.all():
                # TODO: change __in
                snapshots = Snapshot.objects.filter(
                    contact_field__field=tracker.contact_field,
                    contact_field__contact__in=tracker.region.contacts.all()).filter(
                    Q(**{'contact_field_value__' + group_rule.condition: group_rule.get_threshold_value()}))

                group_rule_region = group_rule.region.uuid
                for snapshot in snapshots:
                    contact = snapshot.contact_field.contact
                    temba_contact = contact.as_temba()

                    fields = {str(f.field.key): str(f.value) for f in contact.contactfield_set.all()}
                    groups = temba_client.get_contact(uuid=temba_contact.uuid).groups
                    if group_rule.action == 'add':
                        groups.append(group_rule_region)
                    else:
                        if group_rule_region in groups:
                            groups.remove(group_rule_region)
                    temba_client.update_contact(uuid=temba_contact.uuid, name=temba_contact.name,
                                                urns=temba_contact.urns, fields=fields,
                                                groups=groups)
