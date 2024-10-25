# Generated by Django 5.0.6 on 2024-06-25 06:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0022_guard_individual_leave_days_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='GuardLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('timestamp', models.DateTimeField(auto_now=True)),
                ('guard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_app.guard')),
            ],
        ),
    ]