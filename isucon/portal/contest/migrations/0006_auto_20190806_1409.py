# Generated by Django 2.2.1 on 2019-08-06 05:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contest', '0005_merge_20190625_1457'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='job',
            name='log_text',
        ),
        migrations.RemoveField(
            model_name='job',
            name='result_json',
        ),
        migrations.AddField(
            model_name='job',
            name='reason',
            field=models.CharField(blank=True, max_length=255, verbose_name='失敗原因'),
        ),
        migrations.AddField(
            model_name='job',
            name='stderr',
            field=models.TextField(blank=True, verbose_name='ログ標準エラー出力'),
        ),
        migrations.AddField(
            model_name='job',
            name='stdout',
            field=models.TextField(blank=True, verbose_name='ログ標準出力'),
        ),
    ]
