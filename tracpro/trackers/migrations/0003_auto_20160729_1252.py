# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trackers', '0002_auto_20160727_1411'),
    ]

    operations = [
        migrations.AddField(
            model_name='tracker',
            name='contact_threshold_emails',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='tracker',
            name='group_threshold_emails',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
