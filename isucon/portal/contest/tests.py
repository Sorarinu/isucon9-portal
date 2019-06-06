from django.test import TestCase

from isucon.portal.authentication.models import User, Team
from isucon.portal.contest.models import Server, Benchmarker, ScoreHistory, BenchQueue


class ScoreHistoryTest(TestCase):

    def setUp(self):
        self.user = User.objects.create()
        self.benchmarker = Benchmarker.objects.create(ip="xxx.xxx.xxx.xxx", network="xxx.xxx.xxx.xxx", node="node")
        self.team = Team.objects.create(
            owner=self.user,
            benchmarker=self.benchmarker,
            name="test",
            password="test",
        )

    def test_get_best_score(self):
        """指定チームのベストスコアを取得"""
        max_score = -1
        for i in range(10):
            entry = ScoreHistory.objects.create(team=self.team, score=i, is_passed=True)
            max_score = max(max_score, entry.score)

        got_entry = ScoreHistory.objects.get_best_score(self.team.id)
        self.assertEqual(got_entry.score, max_score)

    def test_get_latest_score(self):
        """指定チームの最新スコアを取得するテスト"""
        # 同一チームのスコア履歴を複数作成
        for i in range(10):
            want_entry = ScoreHistory.objects.create(team=self.team, score=i, is_passed=True)

        # スコア履歴のもので最新のものを取得できているか
        got_entry = ScoreHistory.objects.get_latest_score(self.team.id)
        self.assertEqual(got_entry.created_at, want_entry.created_at)


class BenchQueueTest(TestCase):

    def setUp(self):
        self.user = User.objects.create()
        self.benchmarker = Benchmarker.objects.create(ip="xxx.xxx.xxx.xxx", network="xxx.xxx.xxx.xxx", node="node")
        self.team = Team.objects.create(
            owner=self.user,
            benchmarker=self.benchmarker,
            name="test",
            password="test",
        )
        self.server = Server.objects.create(team=self.team, hostname="hoge", global_ip="xxx.xxx.xxx.xxx", private_ip="yyy.yyy.yyy.yyy", private_network="zzz.zzz.zzz.zzz")

    def test_done(self):
        # 利用者がジョブ登録
        job_id = BenchQueue.objects.enqueue(self.team)
        # ジョブはまだ待ち状態のはず
        job = BenchQueue.objects.get(pk=job_id)
        self.assertEqual(BenchQueue.WAITING, job.progress)

        # ベンチマーカーがジョブの走行を開始
        job2 = BenchQueue.objects.dequeue(job.target_hostname)
        # ジョブは走行中に遷移する
        self.assertEqual(BenchQueue.RUNNING, job2.progress)

        # ベンチマーカーがジョブの完了を通知
        BenchQueue.objects.done(job_id, '{"score": 100, "pass": true}', "blah\nblah\nblah")
        job3 = BenchQueue.objects.get(pk=job_id)
        self.assertEqual(BenchQueue.DONE, job3.progress)

    def test_abort(self):
        pass