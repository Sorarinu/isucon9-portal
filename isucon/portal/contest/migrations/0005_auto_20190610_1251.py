# Generated by Django 2.2.1 on 2019-06-10 03:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contest', '0004_auto_20190607_1051'),
    ]

    operations = [
        migrations.RenameField(
            model_name='scorehistory',
            old_name='bench_queue',
            new_name='job',
        ),
    ]
