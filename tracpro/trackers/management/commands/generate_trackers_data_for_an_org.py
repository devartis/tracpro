from __future__ import absolute_import, unicode_literals

from dash.orgs.models import Org
from django.core.management.base import BaseCommand, CommandError

from tracpro.trackers.data_generator import DataGenerator


class Command(BaseCommand):
    args = "org_id"
    help = 'Generates data for trackers app'

    def handle(self, *args, **options):
        org_id = int(args[0]) if args else None
        if not org_id:
            raise CommandError("Most provide valid org id")

        try:
            org = Org.objects.get(pk=org_id)
        except Org.DoesNotExist:
            raise CommandError("No such org with id %d" % org_id)

        generator = DataGenerator(org=org)
        generator.generate_data()

        self.stdout.write("Contacts, trackers and alerts have been created")
