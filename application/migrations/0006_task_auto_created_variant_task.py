# Generated by Django 4.1.4 on 2023-03-18 07:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0005_variant_liked_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='auto_created',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='variant',
            name='task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='used_variants', to='application.task'),
        ),
    ]
