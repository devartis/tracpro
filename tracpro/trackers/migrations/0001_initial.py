# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0011_uuid_is_unique_to_org'),
        ('orgs', '0014_auto_20150722_1419'),
        ('groups', '0008_uuid_is_unique_to_org'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupRule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action', models.CharField(max_length=6, choices=[('add', 'Add'), ('remove', 'Remove')])),
                ('condition', models.CharField(max_length=7, choices=[('greater', 'Greater'), ('less', 'Less')])),
                ('threshold', models.CharField(max_length=4, choices=[('GMax', 'Group Maximum'), ('GMin', 'Group Minimum'), ('CMax', 'Contact Maximum'), ('CMin', 'Contact Minimum')])),
                ('region', models.ForeignKey(related_name='group_rules', verbose_name='Region', to='groups.Region')),
            ],
        ),
        migrations.CreateModel(
            name='Tracker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('reporting_period', models.DurationField(max_length=2, choices=[(datetime.timedelta(1), 'Daily'), (datetime.timedelta(7), 'Weekly'), (datetime.timedelta(14), 'Fortnightly'), (datetime.timedelta(30), 'Monthly'), (datetime.timedelta(90), 'Quarterly')])),
                ('minimum_group_threshold', models.IntegerField()),
                ('target_group_threshold', models.IntegerField()),
                ('maximum_group_threshold', models.IntegerField()),
                ('minimum_contact_threshold', models.IntegerField()),
                ('target_contact_threshold', models.IntegerField()),
                ('maximum_contact_threshold', models.IntegerField()),
                ('emails', models.TextField()),
                ('contact_field', models.ForeignKey(to='contacts.ContactField')),
                ('org', models.ForeignKey(related_name='trackers', verbose_name='Org', to='orgs.Org')),
                ('region', models.ForeignKey(related_name='trackers', verbose_name='Region', to='groups.Region')),
            ],
        ),
        migrations.AddField(
            model_name='grouprule',
            name='tracker',
            field=models.ForeignKey(related_name='group_rules', verbose_name='Tracker', to='trackers.Tracker'),
        ),
    ]
