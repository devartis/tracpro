from __future__ import unicode_literals

from django.apps import apps

from tracpro.orgs_ext.tasks import OrgTask


class SyncOrgBoundaries(OrgTask):

    def org_task(self, org, **kwargs):
        apps.get_model('groups', 'Boundary').objects.sync(org)
