# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0008_uuid_is_unique_to_org'),
        ('contacts', '0011_uuid_is_unique_to_org'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='groups',
            field=models.ManyToManyField(help_text='All groups to which this contact belongs.', related_name='all_contacts', null=True, verbose_name='Groups', to='groups.Group'),
        ),
    ]
