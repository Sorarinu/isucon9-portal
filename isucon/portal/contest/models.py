import datetime
import json

from django.db import models
from django.db.models import Max, Sum
from django.forms.models import model_to_dict
from django.utils import timezone

from isucon.portal import settings
from isucon.portal.models import LogicalDeleteMixin
from isucon.portal.contest import exceptions

# FIXME: ベンチマーク対象のサーバを変更する機能
# https://github.com/isucon/isucon8-final/blob/d1480128c917f3fe4d87cb84c83fa2a34ca58d39/portal/lib/ISUCON8/Portal/Web/Controller/API.pm#L32


class Information(LogicalDeleteMixin, models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "お知らせ"

    # TODO: タイトルあった方がいい？
    # title = models.CharField('タイトル', max_length=100)
    description = models.TextField('本文')


class Benchmarker(LogicalDeleteMixin, models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "ベンチマーカー"

    # TODO: ベンチマーカーを管理する上で必要な情報を追加
    ip = models.CharField("ベンチマーカーのIPアドレス", max_length=100)

    def __str__(self):
        return self.ip


class ServerManager(models.Manager):

    def of_team(self, team):
        """チームが持つサーバ一覧を取得"""
        return self.get_queryset().filter(team=team)

    def get_bench_target(self, team):
        """チームのベンチマーク対象を取得"""
        return self.get_queryset().get(team=team, is_bench_target=True)

    # FIXME: WAITING状態でenqueueされていても、変更ができる.
    # このことのテストを追加


class Server(LogicalDeleteMixin, models.Model):
    """参加者の問題サーバー"""
    class Meta:
        verbose_name = verbose_name_plural = "サーバ"

    # NOTE: パスワード、鍵認証とかにすればいい気がしたのでまだ追加してない
    # FIXME: デフォルトのベンチマーク対象を設定

    team = models.ForeignKey('authentication.Team', verbose_name="チーム", on_delete=models.PROTECT)
    hostname = models.CharField("ホスト名", max_length=100, unique=True)

    global_ip = models.CharField("グローバルIPアドレス", max_length=100, unique=True)
    private_ip = models.CharField("プライベートIPアドレス", max_length=100)

    is_bench_target = models.BooleanField("ベンチマークターゲットであるかのフラグ", default=False)

    objects = ServerManager()

    def set_bench_target(self):
        # 現在のベンチ対象を、ベンチ対象から外す
        current_bench_target = ServerManager.objects.get_bench_target(self.team)
        current_bench_target.is_bench_target = False
        current_bench_target.save()

        # 自分をベンチ対象にする
        self.is_bench_target = True
        self.save(using=self._db)

    def __str__(self):
        return self.hostname


class ScoreHistoryManager(models.Manager):

    def of_team(self, team):
        return self.get_queryset()\
                   .filter(team=team, team__is_active=True, is_passed=True)

    def get_best_score(self, team):
        """指定チームのベストスコアを取得"""
        return self.of_team(team)\
                   .annotate(best_score=Max('score'))[0]

    def get_latest_score(self, team):
        """指定チームの最新スコアを取得"""
        # NOTE: orderingにより最新順に並んでいるので、LIMITで取れば良い
        return self.of_team(team).order_by('-created_at').first()

    def get_top_teams(self, limit=30):
        """トップ30チームの取得"""
        histories = self.get_queryset().filter(team__is_active=True)\
                        .annotate(best_score=Max('score'))\
                        .order_by('-best_score', '-created_at')[:limit]\
                        .select_related('team', 'team__aggregated_score')

        return [history.team for history in histories]

class ScoreHistory(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "スコア履歴"
        ordering = ('-created_at',)

    team = models.ForeignKey('authentication.Team', verbose_name="チーム", on_delete=models.PROTECT, null=True)
    job = models.ForeignKey('contest.Job', verbose_name="ベンチキュー", on_delete=models.PROTECT, null=True)
    score = models.IntegerField("得点")
    is_passed = models.BooleanField("正答フラグ", default=False)

    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("最終更新日時", auto_now=True)

    objects = ScoreHistoryManager()


class JobManager(models.Manager):

    def of_team(self, team):
        return self.get_queryset().filter(team=team)

    def enqueue(self, team):
        # 重複チェック
        if self.check_duplicated(team):
            raise exceptions.DuplicateJobError

        # 追加
        job = self.model(team=team)
        job.save(using=self._db)

        return job.id

    def dequeue(self, benchmarker=None):
        if benchmarker is not None:
            # ベンチマーカーが自身にひもづくチームのサーバにベンチマークを行う場合
            # 報告したベンチマーカの紐づいているチーム、かつWAITING状態のジョブを取得
            queryset = self.get_queryset().filter(status=Job.WAITING, team__benchmarker=benchmarker)
        else:
            # ベンチマーカーがチーム気にせずベンチマークを行う場合
            queryset = self.get_queryset().filter(status=Job.WAITING)

        job = queryset.first()
        if job is None:
            raise exceptions.JobDoesNotExistError

        # 状態を処理中にする
        job.status = Job.RUNNING
        job.save(using=self._db)

        return job

    def discard_timeout_jobs(self, timeout_sec=settings.BENCHMARK_ABORT_TIMEOUT_SEC):
        # FIXME: Celeryタスクで定期的に実行させる

        # タイムアウトの締め切り
        deadline = timezone.now() - datetime.timedelta(seconds=timeout_sec)

        # タイムアウトした(=締め切りより更新時刻が古い) ジョブを aborted にしていく
        jobs = Job.objects.filter(status=Job.RUNNING, updated_at__lt=deadline)
        for job in jobs:
            job.abort(result=dict(reason="Benchmark timeout"), log_text='')

        return list(map(model_to_dict, jobs))

    def check_duplicated(self, team):
        """重複enqueue防止"""
        return self.get_queryset().filter(team=team, status__in=[
            Job.WAITING,
            Job.RUNNING,
        ]).exists()


class Job(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "ジョブ"
        ordering=('-created_at',)

    # 進捗の選択肢
    WAITING = 'waiting'
    RUNNING = 'running'
    DONE = 'done'
    ABORTED = 'aborted'
    CANCELED = 'canceled'
    STATUS_CHOICES = (
        (WAITING, WAITING), # 処理待ち
        (RUNNING, RUNNING), # 処理中
        (DONE, DONE), # 処理完了
        (ABORTED, ABORTED), # 異常終了
        (CANCELED, CANCELED), # 意図的なキャンセル
    )

    # FIXME: SET_NULLされたレコードを、ジョブ取得時に考慮
    team = models.ForeignKey('authentication.Team', verbose_name="チーム", null=True, on_delete=models.SET_NULL)

    # Choice系
    status = models.CharField("進捗", max_length=100, choices=STATUS_CHOICES, default=WAITING)
    is_passed = models.BooleanField("正答フラグ", default=False)

    score = models.IntegerField("獲得スコア", default=0, null=False)

    # ベタテキスト
    result_json = models.TextField("結果JSON", blank=True)
    log_text = models.TextField("ログ文字列", blank=True)

    # 日時
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("最終更新日時", auto_now=True)

    objects = JobManager()

    @property
    def is_finished(self):
        return self.result in [
            self.DONE,
            self.ABORTED,
            self.CANCELED,
        ]

    @property
    def result(self):
        if self.result_json:
            return json.loads(self.result_json)
        return {}

    @result.setter
    def result(self, result):
        self.result_json = json.dumps(result)

    def append_log(self, log):
        self.log_text += log
        self.save(update_fields=["log_raw"])

    def done(self, result, log_text):
        self.status = Job.DONE
        self.result = result
        # FIXME: append? そうなると逐次報告だが、どうログを投げるか話し合う
        self.log_text = log_text

        # 結果のJSONからスコアや結果を参照し、ジョブに設定
        self.score = self.result['score']
        if self.result['pass']:
            self.is_passed = True
        self.save()

        ScoreHistory.objects.create(
            team=self.team,
            job=self,
            score=self.score,
            is_passed=self.is_passed,
        )

    def abort(self, result, log_text):
        self.status = Job.ABORTED
        self.result = result
        self.log_text = log_text
        self.save()

        ScoreHistory.objects.create(
            team=self.team,
            job=self,
            score=0,
            is_passed=self.is_passed,
        )

# NOTE: AggregatedScoreは、Django signals を用いることで、チーム登録時に作成され、得点履歴が追加されるごとに更新されます
class AggregatedScore(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "集計スコア"

    best_score = models.IntegerField('ベストスコア', default=0)
    latest_score = models.IntegerField('最新獲得スコア', default=0)
    # latest_is_passed = is_passed (True | False)
    # NOTE: 旧 latest_status
    latest_is_passed = models.BooleanField('最新のベンチマーク成否フラグ', default=False, blank=True)