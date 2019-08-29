import dateutil.parser

from django.db import models
from django import forms
from django.db.models import signals
from django.dispatch import receiver

from isucon.portal.models import LogicalDeleteMixin, CommaSeparatedDateField
from isucon.portal.authentication.models import Team
from isucon.portal.contest.alibaba import SyncImageSharePermission


class Image(LogicalDeleteMixin, models.Model):

    class Meta:
        ordering = ("id",)

    id = models.CharField("イメージID", primary_key=True, max_length=256)
    name = models.CharField("名前", max_length=512)
    is_enabled = models.BooleanField("共有有効", blank=True)
    allowed_participate_at = CommaSeparatedDateField("共有対象日", max_length=512, choices=[])

    def sync_permissions(self):
        accounts = []
        if self.is_enabled:
            teams = Team.objects.filter(participate_at__in=self.allowed_participate_at).exclude(alibaba_account="")
            for t in teams:
                accounts.append(t.alibaba_account)
        SyncImageSharePermission(self.id, accounts)


@receiver(signals.post_save, sender=Team)
def update_team(sender, instance, created, raw, using, update_fields, **kwargs):
    for i in Image.objects.filter(is_enabled=True):
        i.sync_permissions()

@receiver(signals.post_delete, sender=Team)
def delete_team(sender, instance, using, **kwargs):
    for i in Image.objects.filter(is_enabled=True):
        i.sync_permissions()

@receiver(signals.post_save, sender=Image)
def update_image(sender, instance, created, raw, using, update_fields, **kwargs):
    instance.sync_permissions()

@receiver(signals.pre_delete, sender=Image)
def delete_image(sender, instance, using, **kwargs):
    instance.is_enabled = False
    instance.sync_permissions()
