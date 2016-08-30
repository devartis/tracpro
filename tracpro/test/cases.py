from __future__ import unicode_literals

import mock
import redis

from dash.orgs.models import Org

from temba_client.client import TembaClient
from temba_client.types import Contact as TembaContact

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from tracpro.polls.models import Question

from . import factories


class TracProTest(TestCase):
    """Base class for all test cases in TracPro."""

    def setUp(self):
        self.clear_cache()

        # Mock the RapidPro client for all tests at all times
        # so that the tests never reach out to the API server.
        self.mock_temba_client = mock.Mock(spec=TembaClient)
        self.patcher = mock.patch.object(Org, 'get_temba_client')
        self.mock_get_temba_client = self.patcher.start()
        self.mock_get_temba_client.return_value = self.mock_temba_client
        # Mock get_contact method of temba_client for "set_groups_to_new_contact" Contact signal
        self.mock_temba_client.get_contact.return_value = TembaContact.create(groups=[])

        super(TracProTest, self).setUp()

    def tearDown(self):
        super(TracProTest, self).tearDown()
        self.patcher.stop()

    def assertLoginRedirect(self, response, subdomain, next_url):
        url = '{}?next={}'.format(reverse('users.user_login'), next_url)
        return self.assertRedirects(response, url, subdomain)

    def assertRedirects(self, response, url, subdomain=None, **kwargs):
        if subdomain:
            kwargs.setdefault('host', '{}.testserver'.format(subdomain))
        return super(TracProTest, self).assertRedirects(response, url, **kwargs)

    def clear_cache(self):
        # we are extra paranoid here and actually hardcode redis to 'localhost'
        # and '10' Redis 10 is our testing redis db
        r = redis.StrictRedis(host='localhost', db=10)
        r.flushdb()

    def create_admin(self, org, full_name, email):
        user = User.create(
            None, full_name, email, password=email, change_password=False)
        user.org_admins.add(org)
        return user

    def create_user(self, org, full_name, email, regions):
        return User.create(
            org, full_name, email, password=email, change_password=False,
            regions=regions)

    def login(self, user):
        result = self.client.login(username=user.username, password=user.username)
        self.assertTrue(
            result, "Couldn't login as %(user)s / %(user)s" % dict(user=user.username))

    def switch_region(self, region):
        session = self.client.session
        key = '{org}:region_id'.format(org=region.org.pk)
        session[key] = region.pk
        session.save()

    def url_get(self, subdomain, *args, **kwargs):
        if subdomain:
            kwargs.setdefault('HTTP_HOST', "{}.testserver".format(subdomain))
        return self.client.get(*args, **kwargs)

    def url_post(self, subdomain, *args, **kwargs):
        if subdomain:
            kwargs.setdefault('HTTP_HOST', "{}.testserver".format(subdomain))
        return self.client.post(*args, **kwargs)


class TracProDataTest(TracProTest):
    """Common data set-up."""

    def setUp(self):
        super(TracProDataTest, self).setUp()

        self.superuser = User.objects.create_superuser(
            username="root", email="super@user.com", password="root")

        # some orgs
        self.unicef = factories.Org(
            name="UNICEF", timezone="Asia/Kabul", subdomain="unicef")
        self.nyaruka = factories.Org(
            name="Nyaruka", timezone="Africa/Kigali", subdomain="nyaruka")

        # some admins for those orgs
        self.admin = self.create_admin(self.unicef, "Richard", "admin@unicef.org")
        self.eric = self.create_admin(self.nyaruka, "Eric", "eric@nyaruka.com")

        # some regions
        self.region1 = factories.Region(org=self.unicef, name="Kandahar", uuid='G-001')
        self.region2 = factories.Region(org=self.unicef, name="Khost", uuid='G-002')
        self.region3 = factories.Region(org=self.unicef, name="Kunar", uuid='G-003')
        self.region4 = factories.Region(org=self.nyaruka, name="Kigali", uuid='G-004')

        # some users in those regions
        self.user1 = self.create_user(
            self.unicef, "Sam Sims", "sam@unicef.org", regions=[self.region1])
        self.user2 = self.create_user(
            self.unicef, "Sue", "sue@unicef.org", regions=[self.region2, self.region3])
        self.user3 = self.create_user(
            self.nyaruka, "Nic", "nic@nyaruka.com", regions=[self.region4])

        # some reporting groups
        self.group1 = factories.Group(org=self.unicef, name="Farmers", uuid='G-005')
        self.group2 = factories.Group(org=self.unicef, name="Teachers", uuid='G-006')
        self.group3 = factories.Group(org=self.unicef, name="Doctors", uuid='G-007')
        self.group4 = factories.Group(org=self.nyaruka, name="Programmers", uuid='G-008')
        self.group5 = factories.Group(org=self.unicef, name="Kandahar", uuid='G-001')

        # some contacts
        self.contact1 = factories.Contact.create(
            org=self.unicef, name="Ann", urn='tel:1234', uuid='C-001',
            region=self.region1, group=self.group1, groups=(self.group1, self.group5))
        self.contact2 = factories.Contact(
            org=self.unicef, name="Bob", urn='tel:2345', uuid='C-002',
            region=self.region1, group=self.group1)
        self.contact3 = factories.Contact(
            org=self.unicef, name="Cat", urn='tel:3456', uuid='C-003',
            region=self.region1, group=self.group2)
        self.contact4 = factories.Contact(
            org=self.unicef, name="Dan", urn='twitter:danny', uuid='C-004',
            region=self.region2, group=self.group2)
        self.contact5 = factories.Contact(
            org=self.unicef, name="Eve", urn='twitter:evee', uuid='C-005',
            region=self.region3, group=self.group3)
        self.contact6 = factories.Contact(
            org=self.nyaruka, name="Norbert", urn='twitter:n7', uuid='C-006',
            region=self.region4, group=self.group4)

        # a poll with some questions
        self.poll1 = factories.Poll(
            org=self.unicef, name="Farm Poll", flow_uuid='F-001')
        self.poll1_question1 = factories.Question(
            poll=self.poll1,
            question_type=Question.TYPE_NUMERIC,
            name="Number of sheep",
            order=1,
            ruleset_uuid='RS-001',
        )
        self.poll1_question2 = factories.Question(
            poll=self.poll1,
            question_type=Question.TYPE_OPEN,
            name="How is the weather?",
            order=2,
            ruleset_uuid='RS-002',
        )

        # and a poll for the other org
        self.poll2 = factories.Poll(
            org=self.nyaruka, name="Code Poll", flow_uuid='F-002')
        self.poll2_question1 = factories.Question(
            poll=self.poll2,
            question_type=Question.TYPE_NUMERIC,
            name="Number of bugs",
            order=1,
            ruleset_uuid='RS-003',
        )
