# Generated by Django 4.0.5 on 2022-06-25 01:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menus', '0008_alter_menu_parent'),
    ]

    operations = [
        migrations.AddField(
            model_name='module',
            name='position',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
