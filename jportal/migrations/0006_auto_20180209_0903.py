# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-09 09:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jportal', '0005_auto_20180208_1223'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='education',
            options={'verbose_name_plural': 'PhD'},
        ),
        migrations.AddField(
            model_name='education',
            name='category',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]