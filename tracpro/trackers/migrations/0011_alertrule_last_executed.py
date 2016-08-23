# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trackers', '0010_auto_20160819_1347'),
    ]

    operations = [
        migrations.AddField(
            model_name='alertrule',
            name='last_executed',
            field=models.DateTimeField(null=True),
        ),
    ]
