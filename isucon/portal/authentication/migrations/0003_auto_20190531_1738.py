# Generated by Django 2.2.1 on 2019-05-31 08:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_team_benchmarker'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='authentication.Team'),
        ),
        migrations.AlterField(
            model_name='team',
            name='owner',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='オーナー'),
        ),
    ]
