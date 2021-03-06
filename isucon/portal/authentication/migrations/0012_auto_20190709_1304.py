# Generated by Django 2.2.1 on 2019-07-09 04:04

from django.db import migrations, models
import stdimage.models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0011_auto_20190625_1458'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='display_name',
            field=models.CharField(default='', max_length=100, verbose_name='表示名'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='user',
            name='icon',
            field=stdimage.models.StdImageField(blank=True, null=True, upload_to='media//icons/'),
        ),
    ]
