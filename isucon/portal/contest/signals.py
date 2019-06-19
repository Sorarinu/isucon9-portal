from django.db.models.signals import post_save
from django.dispatch import receiver

from isucon.portal.authentication.models import Team
from isucon.portal.contest.models import AggregatedScore


@receiver(post_save, sender=Team)
def create_default_aggregated_score(sender, instance, created, **kwargs):
    """チームに対し、デフォルトの `AggregatedScore` を作成する"""
    if created:
        # 集計スコア作成
        aggregated_score = AggregatedScore.objects.create()
        aggregated_score.save()

        # 集計スコアとチームを紐付け
        instance.aggregated_score = aggregated_score
        instance.save()