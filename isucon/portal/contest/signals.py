from django.db.models.signals import post_save
from django.dispatch import receiver

from isucon.portal.authentication.models import Team
from isucon.portal.contest.models import Server, ScoreHistory, AggregatedScore


@receiver(post_save, sender=Team)
def create_aggregated_score(sender, instance, created, **kwargs):
    """チームが作成されたら、デフォルトの `AggregatedScore` を作成する"""
    if created:
        # 集計スコア作成
        aggregated_score = AggregatedScore.objects.create()

        # 集計スコアとチームを紐付け
        instance.aggregated_score = aggregated_score
        instance.save()

@receiver(post_save, sender=ScoreHistory)
def update_aggregated_score(sender, instance, created, **kwargs):
    """スコア履歴が追加されたら、集計スコアを更新する"""
    if created:
        aggregated_score = instance.team.aggregated_score

        if instance.is_passed:
            # ベンチマークが通ったら、スコアとステータスを更新
            aggregated_score.best_score = max(aggregated_score.best_score, instance.score)
            aggregated_score.latest_score = instance.score
            aggregated_score.latest_is_passed = instance.is_passed
        else:
            # ベンチマークが通らなかったら、ステータスのみ更新
            aggregated_score.latest_is_passed = instance.is_passed

        aggregated_score.save()

@receiver(post_save, sender=Server)
def set_default_benchmark_target_server(sender, instance, created, **kwargs):
    """サーバ追加時、ベンチマークのターゲットとするかどうか設定する"""
    if created:
        queryset = Server.objects.filter(team=instance.team)\
                                        .exclude(pk=instance.pk)
        if queryset.exists():
            # すでに他のサーバが存在するならば、ベンチマーク対象は既に存在する
            return

        instance.is_bench_target = True
        instance.save()