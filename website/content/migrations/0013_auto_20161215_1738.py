# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-12-15 04:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0012_auto_20161215_0020'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blogentryhistory',
            name='modified',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='pagehistory',
            name='modified',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]