# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trackers', '0005_snapshot'),
    ]

    operations = [
        migrations.AddField(
            model_name='snapshot',
            name='contact_field_value',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
