# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def rename_condition(apps, schema_editor):
    GroupRule = apps.get_model("trackers", "GroupRule")
    GroupRule.objects.filter(condition='greater').update(condition='gt')
    GroupRule.objects.filter(condition='less').update(condition='lt')


class Migration(migrations.Migration):

    dependencies = [
        ('trackers', '0003_auto_20160729_1252'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grouprule',
            name='condition',
            field=models.CharField(max_length=7, choices=[('gt', 'Greater'), ('lt', 'Less')]),
        ),
        migrations.RunPython(rename_condition),
    ]
