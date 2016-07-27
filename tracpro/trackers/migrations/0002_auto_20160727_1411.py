# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trackers', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tracker',
            name='contact_field',
            field=models.ForeignKey(to='contacts.DataField'),
        ),
    ]
