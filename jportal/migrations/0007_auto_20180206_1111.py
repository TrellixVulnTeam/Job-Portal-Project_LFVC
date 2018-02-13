# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-06 11:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jportal', '0006_auto_20180206_0949'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='city',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='jportal.City'),
        ),
        migrations.AlterField(
            model_name='job',
            name='state',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='jportal.State'),
        ),
        migrations.AlterField(
            model_name='jobseekers',
            name='city',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='jportal.City'),
        ),
        migrations.AlterField(
            model_name='jobseekers',
            name='state',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='jportal.State'),
        ),
        migrations.AlterField(
            model_name='resume',
            name='city',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='jportal.City'),
        ),
        migrations.AlterField(
            model_name='resume',
            name='state',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='jportal.State'),
        ),
    ]