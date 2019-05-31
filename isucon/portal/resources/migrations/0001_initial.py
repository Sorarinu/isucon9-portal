# Generated by Django 2.2.1 on 2019-05-31 06:13

from django.db import migrations, models
import django.db.models.deletion
import isucon.portal.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Benchmarker',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.CharField(max_length=100, verbose_name='IPアドレス')),
                ('network', models.CharField(max_length=100, verbose_name='ネットワークアドレス')),
                ('node', models.CharField(max_length=100, verbose_name='ノード')),
            ],
            options={
                'verbose_name': 'ベンチマーカー',
                'verbose_name_plural': 'ベンチマーカー',
            },
            bases=(isucon.portal.models.LogicalDeleteMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Server',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hostname', models.CharField(max_length=100, unique=True, verbose_name='ホスト名')),
                ('global_ip', models.CharField(max_length=100, unique=True, verbose_name='グローバルIPアドレス')),
                ('private_ip', models.CharField(max_length=100, verbose_name='プライベートIPアドレス')),
                ('private_network', models.CharField(max_length=100, verbose_name='プライベートネットワークアドレス')),
                ('benchmarker', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='resources.Benchmarker', verbose_name='ベンチマーカー')),
            ],
            options={
                'verbose_name': 'サーバ',
                'verbose_name_plural': 'サーバ',
            },
            bases=(isucon.portal.models.LogicalDeleteMixin, models.Model),
        ),
    ]
