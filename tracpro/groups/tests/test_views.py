from __future__ import unicode_literals

import json

from dateutil.relativedelta import relativedelta

from django.core.urlresolvers import reverse
from django.utils import timezone

from tracpro.polls import models as polls
from tracpro.test import factories
from tracpro.test.cases import TracProDataTest, TracProTest

from .. import models


class TestSetRegion(TracProTest):
    url_name = "set-region"

    def setUp(self):
        super(TestSetRegion, self).setUp()
        self.org = factories.Org()
        self.region = factories.Region(org=self.org)

        self.user = factories.User()
        self.user.regions.add(self.region)

        self.login(self.user)

    @property
    def session_key(self):
        return '{org}:region_id'.format(org=self.org.pk)

    def set_region(self, data):
        return self.url_post(self.org.subdomain, reverse(self.url_name), data)

    def test_unauthenticated(self):
        """Unauthenticated users cannot set a region."""
        self.client.logout()
        response = self.set_region({'region': self.region.pk})
        self.assertLoginRedirect(response, self.org.subdomain, reverse(self.url_name))
        self.assertFalse(self.session_key in self.client.session)

    def test_get(self):
        """Set region view does not allow GET."""
        response = self.url_get(self.org.subdomain, reverse(self.url_name))
        self.assertEqual(response.status_code, 405)
        self.assertFalse(self.session_key in self.client.session)

    def test_no_region(self):
        """Set region view requires `region` POST parameter."""
        response = self.set_region({})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.session_key in self.client.session)

    def test_all_not_admin(self):
        """Non-admin user cannot set region to "All regions"."""
        response = self.set_region({'region': 'all'})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.session_key in self.client.session)

    def test_all(self):
        """Admin user can set region to "All regions"."""
        self.org.administrators.add(self.user)
        response = self.set_region({'region': 'all'})
        self.assertRedirects(
            response, reverse('home.home'), self.org.subdomain,
            fetch_redirect_response=False)
        self.assertIsNone(self.client.session[self.session_key])

    def test_non_existant(self):
        """Cannot set a non-existant region."""
        response = self.set_region({'region': '1234'})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.session_key in self.client.session)

    def test_not_in_user_regions(self):
        """Cannot set a region the user doesn't have access to."""
        another_region = factories.Region(org=self.org)
        response = self.set_region({'region': another_region.pk})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.session_key in self.client.session)

    def test_set_region(self):
        """Set region_id variable in the session."""
        response = self.set_region({'region': self.region.pk})
        self.assertRedirects(
            response, reverse('home.home'), self.org.subdomain,
            fetch_redirect_response=False)
        self.assertEqual(self.client.session[self.session_key], str(self.region.pk))

    def test_next_invalid(self):
        """Should not redirect to an invalid `next` URL."""
        response = self.set_region({
            'region': self.region.pk,
            'next': 'http://example.com/',
        })
        self.assertRedirects(
            response, reverse('home.home'), self.org.subdomain,
            fetch_redirect_response=False)

    def test_next(self):
        """Should redirect to custom `next` URL."""
        response = self.set_region({
            'region': self.region.pk,
            'next': '/admin/',
        })
        self.assertRedirects(
            response, '/admin/', self.org.subdomain,
            fetch_redirect_response=False)


class TestToggleSubregions(TracProTest):
    url_name = "toggle-subregions"
    session_key = "include_subregions"

    def setUp(self):
        super(TestToggleSubregions, self).setUp()
        self.org = factories.Org()
        self.user = factories.User()
        self.login(self.user)

    def toggle_subregions(self, data):
        return self.url_post(self.org.subdomain, reverse(self.url_name), data)

    def test_unauthenticated(self):
        """Unauthenticated users cannot toggle subregion data."""
        self.client.logout()
        response = self.toggle_subregions({'include_subregions': '0'})
        self.assertLoginRedirect(response, self.org.subdomain, reverse(self.url_name))
        self.assertFalse(self.session_key in self.client.session)

    def test_get(self):
        """Toggle subregion view does not allow GET."""
        response = self.url_get(self.org.subdomain, reverse(self.url_name))
        self.assertEqual(response.status_code, 405)
        self.assertFalse(self.session_key in self.client.session)

    def test_no_include_subregions(self):
        """Toggle subregion view requires `include_subregions` POST parameter."""
        response = self.toggle_subregions({})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.session_key in self.client.session)

    def test_invalid_value(self):
        """`include_subregions` value must be '0' or '1'."""
        response = self.toggle_subregions({'include_subregions': 'asdf'})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.session_key in self.client.session)

    def test_include_subregions(self):
        """`include_subregions` value of '1' sets parameter to True."""
        response = self.toggle_subregions({'include_subregions': '1'})
        self.assertRedirects(
            response, reverse('home.home'), self.org.subdomain,
            fetch_redirect_response=False)
        self.assertTrue(self.client.session['include_subregions'])

    def test_exclude_subregions(self):
        """`include_subregions` value of '0' sets parameter to False."""
        response = self.toggle_subregions({'include_subregions': '0'})
        self.assertRedirects(
            response, reverse('home.home'), self.org.subdomain,
            fetch_redirect_response=False)
        self.assertFalse(self.client.session['include_subregions'])

    def test_next_invalid(self):
        """Should not redirect to an invalid `next` URL."""
        response = self.toggle_subregions({
            'include_subregions': '0',
            'next': 'http://example.com/',
        })
        self.assertRedirects(
            response, reverse('home.home'), self.org.subdomain,
            fetch_redirect_response=False)

    def test_next(self):
        """Should redirect to custom `next` URL."""
        response = self.toggle_subregions({
            'include_subregions': '0',
            'next': '/admin/',
        })
        self.assertRedirects(
            response, '/admin/', self.org.subdomain,
            fetch_redirect_response=False)


class TestRegionList(TracProDataTest):
    url_name = "groups.region_list"

    def test_list_non_admin(self):
        self.login(self.user1)  # not an admin
        url = reverse(self.url_name)
        response = self.url_get('unicef', url)
        self.assertLoginRedirect(response, "unicef", url)

    def test_list_admin(self):
        self.login(self.admin)
        response = self.url_get('unicef', reverse(self.url_name))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 3)


class TestRegionMostActive(TracProDataTest):
    url_name = "groups.region_most_active"

    def test_most_active(self):
        five_weeks_ago = timezone.now() - relativedelta(weeks=5)
        five_days_ago = timezone.now() - relativedelta(days=5)

        pollrun = factories.RegionalPollRun(
            poll=self.poll1,
            conducted_on=five_weeks_ago,
        )

        # empty response in last month for contact in region #1
        factories.Response(
            pollrun=pollrun, contact=self.contact1,
            created_on=five_days_ago, updated_on=five_days_ago,
            status=polls.Response.STATUS_EMPTY)

        # partial response not in last month for contact in region #2
        factories.Response(
            pollrun=pollrun, contact=self.contact4,
            created_on=five_weeks_ago, updated_on=five_weeks_ago,
            status=polls.Response.STATUS_PARTIAL)

        # partial response in last month for contact in region #2
        factories.Response(
            pollrun=pollrun, contact=self.contact4,
            created_on=five_days_ago, updated_on=five_days_ago,
            status=polls.Response.STATUS_PARTIAL)

        # 2 complete responses in last month for contact in region #3
        factories.Response(
            pollrun=pollrun, contact=self.contact5,
            created_on=five_days_ago, updated_on=five_days_ago,
            status=polls.Response.STATUS_COMPLETE)

        factories.Response(
            pollrun=pollrun, contact=self.contact5,
            created_on=five_days_ago, updated_on=five_days_ago,
            status=polls.Response.STATUS_COMPLETE)

        # log in as a non-administrator
        self.login(self.user1)

        response = self.url_get('unicef', reverse(self.url_name))
        results = json.loads(response.content)['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], self.region3.pk)
        self.assertEqual(results[0]['name'], self.region3.name)
        self.assertEqual(results[0]['response_count'], 2)
        self.assertEqual(results[1]['id'], self.region2.pk)
        self.assertEqual(results[1]['name'], self.region2.name)
        self.assertEqual(results[1]['response_count'], 1)


class TestRegionUpdateAll(TracProTest):
    url_name = "groups.region_update_all"

    def setUp(self):
        super(TestRegionUpdateAll, self).setUp()

        self.user = factories.User()
        self.login(self.user)

        self.org = factories.Org(name="Test", subdomain="test")
        self.org.administrators.add(self.user)

    def assertErrorResponse(self, data, message):
        """Assert that the data causes an error with the given message."""
        response = self.url_post("test", reverse(self.url_name), data=data)
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content.decode("utf-8"))
        self.assertFalse(content['success'])
        self.assertEqual(content['status'], 400)
        self.assertEqual(content['message'], message)

    def assertSuccessResponse(self, data, expected_structure):
        """Assert that regions are successfully updated."""
        response = self.url_post("test", reverse(self.url_name), data=data)
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content.decode("utf-8"))
        self.assertTrue(content['success'])
        self.assertEqual(content['status'], 200)
        self.assertEqual(
            content['message'],
            "Test regions have been updated.")

        new_structure = self.get_structure(models.Region.get_all(self.org))
        self.assertDictEqual(expected_structure, new_structure)

    def get_structure(self, regions):
        """Create a dict to represent current region parents and boundaries."""
        structure = {}
        for region in regions:
            structure[region.pk] = [region.parent_id, region.boundary_id]
        return structure

    def make_regions(self):
        """Create a collection of nested regions."""
        self.region_uganda = factories.Region(
            org=self.org, name="Uganda", parent=None,
            boundary=factories.Boundary(org=self.org))
        self.region_kampala = factories.Region(
            org=self.org, name="Kampala", parent=self.region_uganda,
            boundary=factories.Boundary(org=self.org))
        self.region_makerere = factories.Region(
            org=self.org, name="Makerere", parent=self.region_kampala,
            boundary=factories.Boundary(org=self.org))
        self.region_entebbe = factories.Region(
            org=self.org, name="Entebbe", parent=self.region_uganda,
            boundary=factories.Boundary(org=self.org))

        self.region_kenya = factories.Region(
            org=self.org, name="Kenya", parent=None,
            boundary=factories.Boundary(org=self.org))
        self.region_nairobi = factories.Region(
            org=self.org, name="Nairobi", parent=self.region_kenya,
            boundary=factories.Boundary(org=self.org))
        self.region_mombasa = factories.Region(
            org=self.org, name="Mombasa", parent=self.region_kenya,
            boundary=factories.Boundary(org=self.org))

        self.region_no_boundary = factories.Region(
            org=self.org, name="No Boundary", parent=None,
            boundary=None)

        self.region_inactive = factories.Region(
            org=self.org, name="Inactive", parent=self.region_nairobi,
            is_active=False)

        return models.Region.get_all(self.org)

    def test_unauthenticated(self):
        """View requires authentication."""
        self.client.logout()
        url = reverse(self.url_name)
        response = self.url_get("test", url)
        self.assertLoginRedirect(response, "test", url)

    def test_no_org(self):
        """View must be used with a specific org."""
        response = self.url_get(None, reverse(self.url_name))
        self.assertRedirects(response, reverse("orgs_ext.org_chooser"))

    def test_no_perms(self):
        """View requires that the user is an org administrator."""
        self.org.administrators.remove(self.user)
        url = reverse(self.url_name)
        response = self.url_get("test", url)
        self.assertLoginRedirect(response, "test", url)

    def test_editor(self):
        """View requires that the user is an org administrator."""
        self.org.administrators.remove(self.user)
        self.org.editors.add(self.user)
        url = reverse(self.url_name)
        response = self.url_get("test", url)
        self.assertLoginRedirect(response, "test", url)

    def test_viewer(self):
        """View requires that the user is an org administrator."""
        self.org.administrators.remove(self.user)
        self.org.viewers.add(self.user)
        url = reverse(self.url_name)
        response = self.url_get("test", url)
        self.assertLoginRedirect(response, "test", url)

    def test_get(self):
        """View is post-only."""
        response = self.url_get("test", reverse(self.url_name))
        self.assertEqual(response.status_code, 405)

    def test_post_no_data(self):
        """View requires that data is sent in the `data` parameter."""
        self.assertErrorResponse(
            data={},
            message="No data was provided in the `data` parameter.")

    def test_post_invalid_json_data(self):
        """View requires valid JSON data in the `data` parameter."""
        self.assertErrorResponse(
            data={'data': "invalid"},
            message="Data must be valid JSON.")

    def test_post_wrong_type(self):
        """View requires a JSON-encoded dictionary in the `data` parameter."""
        self.assertErrorResponse(
            data={'data': json.dumps("Wrong type")},
            message="Data must be a dict that maps region id to "
                    "(parent id, boundary id).")

    def test_post_wrong_value_type(self):
        """View requires each dictionary key to be a list with two items."""
        regions = self.make_regions()
        structure = self.get_structure(regions)
        structure[regions.first().pk] = None
        self.assertErrorResponse(
            data={'data': json.dumps(structure)},
            message="All data values must be of the format "
                    "(parent id, boundary id).")

    def test_post_extra_regions(self):
        """Submitted data should provide data for all regions in the org."""
        other_region = factories.Region()  # another org
        regions = self.make_regions()
        structure = self.get_structure(regions)
        structure[other_region.pk] = [None, None]
        self.assertErrorResponse(
            data={'data': json.dumps(structure)},
            message="Data must map region id to parent id for every region "
                    "in this org.")

    def test_post_missing_regions(self):
        """Submitted data should provide data for all regions in the org."""
        regions = self.make_regions()
        structure = self.get_structure(regions)
        structure.pop(regions.first().pk)
        self.assertErrorResponse(
            data={'data': json.dumps(structure)},
            message="Data must map region id to parent id for every region "
                    "in this org.")

    def test_post_inactive_regions(self):
        """Submitted data should not include info about inactive regions."""
        regions = self.make_regions()
        structure = self.get_structure(regions)
        structure[self.region_inactive.pk] = [None, None]
        self.assertErrorResponse(
            data={'data': json.dumps(structure)},
            message="Data must map region id to parent id for every region "
                    "in this org.")

    def test_post_invalid_region(self):
        """Submitted data should not include info about invalid regions."""
        regions = self.make_regions()
        structure = self.get_structure(regions)
        structure['asdf'] = [None, None]
        structure[12345] = [None, None]
        self.assertErrorResponse(
            data={'data': json.dumps(structure)},
            message="Data must map region id to parent id for every region "
                    "in this org.")

    def test_post_invalid_parent(self):
        """Submitted data should only reference parents within the same org."""
        regions = self.make_regions()
        structure = self.get_structure(regions)
        structure[regions.first().pk] = [12345, None]
        structure[regions.last().pk] = ["asdf", None]
        self.assertErrorResponse(
            data={'data': json.dumps(structure)},
            message="Region parent must be a region from the same org, or "
                    "null.")

    def test_post_inactive_parent(self):
        """Submitted data should not reference inactive parents."""
        regions = self.make_regions()
        structure = self.get_structure(regions)
        structure[regions.first().pk] = [self.region_inactive.pk, None]
        self.assertErrorResponse(
            data={'data': json.dumps(structure)},
            message="Region parent must be a region from the same org, or "
                    "null.")

    def test_post_other_org_parent(self):
        """Submitted data should not reference parents from another org."""
        other_region = factories.Region()  # another org
        regions = self.make_regions()
        structure = self.get_structure(regions)
        structure[regions.first().pk] = [other_region.pk, None]
        self.assertErrorResponse(
            data={'data': json.dumps(structure)},
            message="Region parent must be a region from the same org, or "
                    "null.")

    def test_post_invalid_boundaries(self):
        """Submitted data should not make invalid boundary references."""
        regions = self.make_regions()
        structure = self.get_structure(regions)
        structure[regions.first().pk] = [None, 12345]
        structure[regions.last().pk] = [None, "asdf"]
        self.assertErrorResponse(
            data={'data': json.dumps(structure)},
            message="Region boundary must be a boundary from the same org, "
                    "or null.")

    def test_post_other_org_boundary(self):
        """Submitted data should not reference boundaries from another org."""
        other_boundary = factories.Boundary()  # another org
        regions = self.make_regions()
        structure = self.get_structure(regions)
        structure[regions.first().pk] = [None, other_boundary.pk]
        self.assertErrorResponse(
            data={'data': json.dumps(structure)},
            message="Region boundary must be a boundary from the same org, "
                    "or null.")

    def test_post_same(self):
        """Test when hierarchy and boundaries do not change."""
        regions = self.make_regions()
        structure = self.get_structure(regions)
        data = {'data': json.dumps(structure)}
        self.assertSuccessResponse(data, structure)

    def test_post_change(self):
        """Test hierarchy and boundary changes."""
        regions = self.make_regions()
        structure = self.get_structure(regions)
        structure[self.region_kampala.pk] = [self.region_kenya.pk, None]
        structure[self.region_nairobi.pk] = [self.region_uganda.pk,
                                             self.region_uganda.boundary.pk]
        structure[self.region_entebbe.pk] = [None, self.region_kenya.boundary.pk]
        data = {'data': json.dumps(structure)}
        self.assertSuccessResponse(data, structure)


class TestGroupList(TracProDataTest):
    url_name = "groups.group_list"

    def test_non_admin(self):
        self.login(self.user1)  # not an admin
        url = reverse(self.url_name)
        response = self.url_get('unicef', url)
        self.assertLoginRedirect(response, "unicef", url)

    def test_admin(self):
        self.login(self.admin)
        response = self.url_get('unicef', reverse(self.url_name))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 4)


class TestGroupMostActive(TracProDataTest):
    url_name = "groups.group_most_active"

    def test_most_active(self):
        five_weeks_ago = timezone.now() - relativedelta(weeks=5)
        five_days_ago = timezone.now() - relativedelta(days=5)
        pollrun = factories.RegionalPollRun(
            poll=self.poll1,
            conducted_on=five_weeks_ago,
        )

        # empty response in last month for contact in group #1
        factories.Response(
            pollrun=pollrun, contact=self.contact1,
            created_on=five_days_ago, updated_on=five_days_ago,
            status=polls.Response.STATUS_EMPTY)

        # partial response not in last month for contact in group #2
        factories.Response(
            pollrun=pollrun, contact=self.contact3,
            created_on=five_weeks_ago, updated_on=five_weeks_ago,
            status=polls.Response.STATUS_PARTIAL)

        # partial response in last month for contact in group #2
        factories.Response(
            pollrun=pollrun, contact=self.contact3,
            created_on=five_days_ago, updated_on=five_days_ago,
            status=polls.Response.STATUS_PARTIAL)

        # 2 complete responses in last month for contact in group #3
        factories.Response(
            pollrun=pollrun, contact=self.contact5,
            created_on=five_days_ago, updated_on=five_days_ago,
            status=polls.Response.STATUS_COMPLETE)

        factories.Response(
            pollrun=pollrun, contact=self.contact5,
            created_on=five_days_ago, updated_on=five_days_ago,
            status=polls.Response.STATUS_COMPLETE)

        # log in as a non-administrator
        self.login(self.user1)

        response = self.url_get('unicef', reverse(self.url_name))
        results = json.loads(response.content)['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], self.group3.pk)
        self.assertEqual(results[0]['name'], self.group3.name)
        self.assertEqual(results[0]['response_count'], 2)
        self.assertEqual(results[1]['id'], self.group2.pk)
        self.assertEqual(results[1]['name'], self.group2.name)
        self.assertEqual(results[1]['response_count'], 1)
