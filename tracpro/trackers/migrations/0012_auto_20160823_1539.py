# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trackers', '0011_alertrule_last_executed'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='trackeroccurrence',
            name='action',
        ),
        migrations.RemoveField(
            model_name='trackeroccurrence',
            name='group',
        ),
        migrations.AddField(
            model_name='trackeroccurrence',
            name='alert_rules',
            field=models.ManyToManyField(related_name='occurrences', verbose_name='Alert Rule', to='trackers.AlertRule'),
        ),
    ]
