from __future__ import absolute_import, unicode_literals

from random import randint

from tracpro.contacts.models import Contact, DataField
from tracpro.groups.models import Region
from tracpro.trackers.models import Tracker, GroupRule, Alert, AlertRule, ADD, REMOVE


def random_number():
    return str(randint(0, 10))


class DataGenerator(object):
    def __init__(self, org):
        self.org = org
        self.temba_client = org.get_temba_client()

        self.email = 'an_email@email.com'

        self.data_fields = org.datafield_set.filter(value_type=DataField.TYPE_NUMERIC)[0:3]

        self.flows = org.polls.all()[0:3]

        self.groups = org.groups.all()[0:6]
        self.regions = [Region.objects.get(uuid=group.uuid) for group in self.groups]

    def generate_data(self):
        self.create_contacts_and_sync()

        self.create_trackers_and_group_rules()

        self.create_alerts_and_alert_rules()

    def create_contacts_and_sync(self):
        self.temba_client.create_contact('Nick', urns=["tel:+5491100001101"],
                                         fields=self.random_fields_dict(), groups=[self.groups[0].uuid])
        self.temba_client.create_contact('Peter', urns=["tel:+5491100001102"],
                                         fields=self.random_fields_dict(), groups=[self.groups[0].uuid])
        self.temba_client.create_contact('Paul', urns=["tel:+5491100001103"],
                                         fields=self.random_fields_dict(), groups=[self.groups[0].uuid])
        self.temba_client.create_contact('Robert', urns=["tel:+5491100001104"],
                                         fields=self.random_fields_dict(), groups=[self.groups[0].uuid])
        self.temba_client.create_contact('Mary', urns=["tel:+5491100001105"],
                                         fields=self.random_fields_dict(), groups=[self.groups[1].uuid])
        self.temba_client.create_contact('Susan', urns=["tel:+5491100001106"],
                                         fields=self.random_fields_dict(), groups=[self.groups[1].uuid])
        self.temba_client.create_contact('Cecelia', urns=["tel:+5491100001107"],
                                         fields=self.random_fields_dict(), groups=[self.groups[1].uuid])
        self.temba_client.create_contact('Ann', urns=["tel:+5491100001108"],
                                         fields=self.random_fields_dict(), groups=[self.groups[1].uuid])
        self.temba_client.create_contact('Aaron', urns=["tel:+5491100001110"],
                                         fields=self.random_fields_dict(), groups=[self.groups[2].uuid])
        self.temba_client.create_contact('Alice', urns=["tel:+5491100001111"],
                                         fields=self.random_fields_dict(), groups=[self.groups[2].uuid])
        self.temba_client.create_contact('Albert', urns=["tel:+5491100001112"],
                                         fields=self.random_fields_dict(), groups=[self.groups[2].uuid])
        self.temba_client.create_contact('Amy', urns=["tel:+5491100001113"],
                                         fields=self.random_fields_dict(),
                                         groups=[self.groups[1].uuid, self.groups[2].uuid])
        Contact.objects.sync(self.org)

    def create_trackers_and_group_rules(self):
        tracker = Tracker.objects.create(org=self.org, region=self.regions[0], contact_field=self.data_fields[0],
                                         reporting_period=Tracker.DAILY,
                                         minimum_contact_threshold=3, minimum_group_threshold=52,
                                         target_contact_threshold=5, target_group_threshold=55,
                                         maximum_contact_threshold=8, maximum_group_threshold=65,
                                         group_threshold_emails=self.email, contact_threshold_emails=self.email,
                                         emails=self.email)
        self.create_group_rules_for(tracker, self.regions[0], self.regions[3])
        tracker = Tracker.objects.create(org=self.org, region=self.regions[1], contact_field=self.data_fields[1],
                                         reporting_period=Tracker.DAILY,
                                         minimum_contact_threshold=1, minimum_group_threshold=45,
                                         target_contact_threshold=4, target_group_threshold=50,
                                         maximum_contact_threshold=7, maximum_group_threshold=64,
                                         group_threshold_emails=self.email, contact_threshold_emails=self.email,
                                         emails=self.email)
        self.create_group_rules_for(tracker, self.regions[1], self.regions[4])
        tracker = Tracker.objects.create(org=self.org, region=self.regions[2], contact_field=self.data_fields[2],
                                         reporting_period=Tracker.DAILY,
                                         minimum_contact_threshold=2, minimum_group_threshold=55,
                                         target_contact_threshold=6, target_group_threshold=60,
                                         maximum_contact_threshold=9, maximum_group_threshold=70,
                                         group_threshold_emails=self.email, contact_threshold_emails=self.email,
                                         emails=self.email)
        self.create_group_rules_for(tracker, self.regions[2], self.regions[5])

    def create_group_rules_for(self, tracker, a_region, other_region):
        GroupRule.objects.create(action=REMOVE, region=a_region,
                                 condition=GroupRule.LESS, threshold=GroupRule.CONTACT_MINIMUM,
                                 tracker=tracker)
        GroupRule.objects.create(action=REMOVE, region=a_region,
                                 condition=GroupRule.LESS, threshold=GroupRule.GROUP_MINIMUM,
                                 tracker=tracker)
        GroupRule.objects.create(action=ADD, region=other_region,
                                 condition=GroupRule.GREATER, threshold=GroupRule.CONTACT_MAXIMUM,
                                 tracker=tracker)
        GroupRule.objects.create(action=ADD, region=other_region,
                                 condition=GroupRule.GREATER, threshold=GroupRule.GROUP_MAXIMUM,
                                 tracker=tracker)

    def create_alerts_and_alert_rules(self):
        alert = Alert.objects.create(org=self.org, name='Alert1')
        AlertRule.objects.create(alert=alert, flow=self.flows[0], region=self.regions[3],
                                 action=ADD, group=self.groups[3])
        alert = Alert.objects.create(org=self.org, name='Alert2')
        AlertRule.objects.create(alert=alert, flow=self.flows[1], region=self.regions[4],
                                 action=ADD, group=self.groups[4])
        alert = Alert.objects.create(org=self.org, name='Alert3')
        AlertRule.objects.create(alert=alert, flow=self.flows[2], region=self.regions[5],
                                 action=ADD, group=self.groups[5])

    def update_contacts(self):
        for contact in self.org.contacts.all():
            temba_contact = contact.as_temba()
            self.temba_client.update_contact(uuid=temba_contact.uuid, name=temba_contact.name, urns=temba_contact.urns,
                                             fields=self.random_fields_dict(), groups=temba_contact.groups)
        Contact.objects.sync(self.org)

    def random_fields_dict(self):
        return {data_field.label: random_number() for data_field in self.data_fields}
