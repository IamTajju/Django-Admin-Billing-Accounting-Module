# Generated by Django 4.1.3 on 2023-08-18 12:53

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cashoutflow',
            name='date_cleared',
            field=models.DateField(blank=True, default=datetime.date(2023, 8, 18), null=True),
        ),
    ]
