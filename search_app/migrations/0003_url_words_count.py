# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-06 07:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search_app', '0002_auto_20160605_1335'),
    ]

    operations = [
        migrations.AddField(
            model_name='url',
            name='words_count',
            field=models.IntegerField(default=0),
        ),
    ]
