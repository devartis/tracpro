# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trackers', '0006_snapshot_contact_field_value'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tracker',
            name='maximum_contact_threshold',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='tracker',
            name='maximum_group_threshold',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='tracker',
            name='minimum_contact_threshold',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='tracker',
            name='minimum_group_threshold',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
