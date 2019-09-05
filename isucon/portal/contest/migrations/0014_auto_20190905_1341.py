# Generated by Django 2.2.1 on 2019-09-05 04:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contest', '0013_auto_20190830_1646'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='benchmarker',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contest.Benchmarker', verbose_name='ベンチマーカ'),
        ),
        migrations.AddField(
            model_name='job',
            name='target',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contest.Server', verbose_name='対象サーバ'),
        ),
        migrations.AlterField(
            model_name='job',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authentication.Team', verbose_name='チーム'),
        ),
    ]