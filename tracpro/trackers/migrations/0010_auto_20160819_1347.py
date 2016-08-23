# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trackers', '0009_alert_alertrule'),
    ]

    operations = [
        migrations.RenameModel("ContactAction", "TrackerOccurrence")
    ]
