# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trackers', '0012_auto_20160823_1539'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trackeroccurrence',
            name='contact',
            field=models.ForeignKey(related_name='occurrences', verbose_name='Contact', to='contacts.Contact'),
        ),
        migrations.AlterField(
            model_name='trackeroccurrence',
            name='tracker',
            field=models.ForeignKey(related_name='occurrences', verbose_name='Tracker', to='trackers.Tracker'),
        ),
    ]
