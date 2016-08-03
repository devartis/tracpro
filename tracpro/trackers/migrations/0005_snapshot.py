# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0011_uuid_is_unique_to_org'),
        ('trackers', '0004_auto_20160801_1544'),
    ]

    operations = [
        migrations.CreateModel(
            name='Snapshot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('contact_field', models.ForeignKey(related_name='snapshots', verbose_name='ContactField', to='contacts.ContactField')),
            ],
        ),
    ]
