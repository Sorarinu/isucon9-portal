# Generated by Django 2.2.1 on 2019-08-16 04:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0014_remove_team_aggregated_score'),
        ('contest', '0008_auto_20190814_1132'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AggregatedScore',
        ),
    ]
