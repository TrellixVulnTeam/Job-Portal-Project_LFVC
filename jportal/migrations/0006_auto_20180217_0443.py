# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-17 04:43
from __future__ import unicode_literals

from django.db import migrations
import django.db.models.deletion
import smart_selects.db_fields


class Migration(migrations.Migration):

    dependencies = [
        ('jportal', '0005_auto_20180217_0423'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobseekers',
            name='city',
            field=smart_selects.db_fields.ChainedForeignKey(auto_choose=True, chained_field='state', chained_model_field='state', on_delete=django.db.models.deletion.CASCADE, to='jportal.City'),
        ),
    ]
