from __future__ import absolute_import, unicode_literals

from random import randint

from tracpro.contacts.models import Contact, DataField
from tracpro.groups.models import Group, Region
from tracpro.polls.models import Poll
from tracpro.trackers.models import Tracker, GroupRule, Alert, AlertRule, ADD, REMOVE


def random_number():
    return str(randint(0, 10))


def random_fields_dict():
    return {'number_of_ors_sachets': random_number(),
            'new_pregnancies': random_number(),
            'number_of_suspected_malaria_cases': random_number()
            }


class DataGenerator(object):
    def __init__(self, org):
        self.org = org
        self.temba_client = org.get_temba_client()

        self.email = 'an_email@email.com'

        self.malaria_data_field = DataField.objects.get(label='number of suspected malaria cases')
        self.pregnancies_data_field = DataField.objects.get(label='number of pregnancies')
        self.ors_data_field = DataField.objects.get(label='number of ors sachets')

        self.malaria_flow = Poll.objects.get(flow_uuid='39083dee-a682-4b6f-a253-7c25ee3d5036')
        self.pregnancies_flow = Poll.objects.get(flow_uuid='7f717bfb-05a3-489b-a14d-b4990e778287')
        self.ors_flow = Poll.objects.get(flow_uuid='2c91cd86-4064-49a4-81dc-96d195458177')

        self.group_1 = Group.objects.get(name='Group1')
        self.group_2 = Group.objects.get(name='Group2')
        self.group_3 = Group.objects.get(name='Group3')
        self.group_4 = Group.objects.get(name='Group4')
        self.group_5 = Group.objects.get(name='Group5')
        self.group_6 = Group.objects.get(name='Group6')
        self.region_1 = Region.objects.get(uuid=self.group_1.uuid)
        self.region_2 = Region.objects.get(uuid=self.group_2.uuid)
        self.region_3 = Region.objects.get(uuid=self.group_3.uuid)
        self.region_4 = Region.objects.get(uuid=self.group_4.uuid)
        self.region_5 = Region.objects.get(uuid=self.group_5.uuid)
        self.region_6 = Region.objects.get(uuid=self.group_6.uuid)

    def generate_data(self):
        self.create_contacts_and_sync()

        self.create_trackers_and_group_rules()

        self.create_alerts_and_alert_rules()

    def create_contacts_and_sync(self):
        self.temba_client.create_contact('Nick', urns=["tel:+5491100001101"],
                                         fields=random_fields_dict(), groups=[self.group_1.uuid])
        self.temba_client.create_contact('Peter', urns=["tel:+5491100001102"],
                                         fields=random_fields_dict(), groups=[self.group_1.uuid])
        self.temba_client.create_contact('Paul', urns=["tel:+5491100001103"],
                                         fields=random_fields_dict(), groups=[self.group_1.uuid])
        self.temba_client.create_contact('Robert', urns=["tel:+5491100001104"],
                                         fields=random_fields_dict(), groups=[self.group_1.uuid])
        self.temba_client.create_contact('Mary', urns=["tel:+5491100001105"],
                                         fields=random_fields_dict(), groups=[self.group_2.uuid])
        self.temba_client.create_contact('Susan', urns=["tel:+5491100001106"],
                                         fields=random_fields_dict(), groups=[self.group_2.uuid])
        self.temba_client.create_contact('Cecelia', urns=["tel:+5491100001107"],
                                         fields=random_fields_dict(), groups=[self.group_2.uuid])
        self.temba_client.create_contact('Ann', urns=["tel:+5491100001108"],
                                         fields=random_fields_dict(), groups=[self.group_2.uuid])
        self.temba_client.create_contact('Aaron', urns=["tel:+5491100001110"],
                                         fields=random_fields_dict(), groups=[self.group_3.uuid])
        self.temba_client.create_contact('Alice', urns=["tel:+5491100001111"],
                                         fields=random_fields_dict(), groups=[self.group_3.uuid])
        self.temba_client.create_contact('Albert', urns=["tel:+5491100001112"],
                                         fields=random_fields_dict(), groups=[self.group_3.uuid])
        self.temba_client.create_contact('Amy', urns=["tel:+5491100001113"],
                                         fields=random_fields_dict(), groups=[self.group_2.uuid, self.group_3.uuid])
        Contact.objects.sync(self.org)

    def create_trackers_and_group_rules(self):
        tracker = Tracker.objects.create(org=self.org, region=self.region_1, contact_field=self.malaria_data_field,
                                         reporting_period=Tracker.DAILY,
                                         minimum_contact_threshold=3, minimum_group_threshold=52,
                                         target_contact_threshold=5, target_group_threshold=55,
                                         maximum_contact_threshold=8, maximum_group_threshold=65,
                                         group_threshold_emails=self.email, contact_threshold_emails=self.email,
                                         emails=self.email)
        self.create_group_rules_for(tracker, self.region_1, self.region_4)
        tracker = Tracker.objects.create(org=self.org, region=self.region_2, contact_field=self.pregnancies_data_field,
                                         reporting_period=Tracker.DAILY,
                                         minimum_contact_threshold=1, minimum_group_threshold=45,
                                         target_contact_threshold=4, target_group_threshold=50,
                                         maximum_contact_threshold=7, maximum_group_threshold=64,
                                         group_threshold_emails=self.email, contact_threshold_emails=self.email,
                                         emails=self.email)
        self.create_group_rules_for(tracker, self.region_2, self.region_5)
        tracker = Tracker.objects.create(org=self.org, region=self.region_3, contact_field=self.ors_data_field,
                                         reporting_period=Tracker.DAILY,
                                         minimum_contact_threshold=2, minimum_group_threshold=55,
                                         target_contact_threshold=6, target_group_threshold=60,
                                         maximum_contact_threshold=9, maximum_group_threshold=70,
                                         group_threshold_emails=self.email, contact_threshold_emails=self.email,
                                         emails=self.email)
        self.create_group_rules_for(tracker, self.region_3, self.region_6)

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
        alert = Alert.objects.create(org=self.org, name='Malaria')
        AlertRule.objects.create(alert=alert, flow=self.malaria_flow, region=self.region_4,
                                 action=ADD, group=self.group_4)
        alert = Alert.objects.create(org=self.org, name='Pregnancies')
        AlertRule.objects.create(alert=alert, flow=self.pregnancies_flow, region=self.region_5,
                                 action=ADD, group=self.group_5)
        alert = Alert.objects.create(org=self.org, name='Ors')
        AlertRule.objects.create(alert=alert, flow=self.ors_flow, region=self.region_6,
                                 action=ADD, group=self.group_6)

    def update_contacts(self):
        for contact in self.org.contacts.all():
            temba_contact = contact.as_temba()
            self.temba_client.update_contact(uuid=temba_contact.uuid, name=temba_contact.name, urns=temba_contact.urns,
                                             fields=random_fields_dict(), groups=temba_contact.groups)
        Contact.objects.sync(self.org)
