# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-10-24 23:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0006_auto_20160915_2344'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='template',
            field=models.FilePathField(match='\\.html$', path='templates'),
        ),
    ]