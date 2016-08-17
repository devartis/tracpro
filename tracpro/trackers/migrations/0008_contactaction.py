# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0012_contact_groups'),
        ('groups', '0008_uuid_is_unique_to_org'),
        ('trackers', '0007_auto_20160804_1601'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactAction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action', models.CharField(max_length=6, choices=[('add', 'Add'), ('remove', 'Remove')])),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('contact', models.ForeignKey(related_name='contact_actions', verbose_name='Contact', to='contacts.Contact')),
                ('group', models.ForeignKey(related_name='contact_actions', verbose_name='Group', to='groups.Group')),
                ('tracker', models.ForeignKey(related_name='contact_actions', verbose_name='Tracker', to='trackers.Tracker')),
            ],
        ),
    ]
