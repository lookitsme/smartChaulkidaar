# Generated by Django 5.0.6 on 2024-06-06 11:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0013_alter_client_company_name_alter_client_vat_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='guard_office',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main_app.guardoffice'),
        ),
    ]