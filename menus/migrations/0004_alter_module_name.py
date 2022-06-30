# Generated by Django 4.0.5 on 2022-06-02 02:13

from django.db import migrations
import menus.models


class Migration(migrations.Migration):

    dependencies = [
        ('menus', '0003_remove_module_unique_module'),
    ]

    operations = [
        migrations.AlterField(
            model_name='module',
            name='name',
            field=menus.models.CharFieldTrim(error_messages={'unique': 'The module already exists'}, max_length=15, unique=True),
        ),
    ]