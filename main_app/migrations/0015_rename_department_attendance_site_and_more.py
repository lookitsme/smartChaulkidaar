# Generated by Django 5.0.6 on 2024-06-09 03:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0014_client_guard_office'),
    ]

    operations = [
        migrations.RenameField(
            model_name='attendance',
            old_name='department',
            new_name='site',
        ),
        migrations.RenameField(
            model_name='client',
            old_name='department',
            new_name='site',
        ),
        migrations.RenameField(
            model_name='guard',
            old_name='department',
            new_name='site',
        ),
        migrations.RenameField(
            model_name='guardsalary',
            old_name='department',
            new_name='site',
        ),
    ]
