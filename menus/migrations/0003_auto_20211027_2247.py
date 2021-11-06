# Generated by Django 3.1.13 on 2021-10-28 03:47

from django.db import migrations
import menus.models


class Migration(migrations.Migration):

    dependencies = [
        ('menus', '0002_auto_20211015_1830'),
    ]

    operations = [
        migrations.AlterField(
            model_name='module',
            name='name',
            field=menus.models.TrimCharField(error_messages={'unique': 'The module already exists'}, max_length=15),
        ),
    ]