# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-01-18 23:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0013_auto_20161215_1738'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='modified',
            field=models.DateTimeField(),
        ),
    ]
