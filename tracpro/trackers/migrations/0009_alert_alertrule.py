# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0032_uuid_is_unique_to_pollrun'),
        ('orgs', '0014_auto_20150722_1419'),
        ('groups', '0008_uuid_is_unique_to_org'),
        ('trackers', '0008_contactaction'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='The name of this alert', max_length=128, verbose_name='Name')),
                ('org', models.ForeignKey(related_name='alerts', verbose_name='Org', to='orgs.Org')),
            ],
        ),
        migrations.CreateModel(
            name='AlertRule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action', models.CharField(max_length=6, choices=[('add', 'Add'), ('remove', 'Remove')])),
                ('alert', models.ForeignKey(related_name='alert_rules', to='trackers.Alert')),
                ('flow', models.ForeignKey(related_name='alert_rules', to='polls.Poll')),
                ('group', models.ForeignKey(related_name='alert_rules', to='groups.Group')),
                ('region', models.ForeignKey(related_name='alert_rules', verbose_name='Region', to='groups.Region')),
            ],
        ),
    ]
