import time

from django.test import TestCase

from isucon.portal.authentication.models import User, Team
from isucon.portal.contest.models import Server, Benchmarker, ScoreHistory, BenchQueue
from isucon.portal.contest import exceptions

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

    def test_get_top_teams(self):
        """トップnチーム取得のテスト"""
        # 10チーム程度生成
        # 適当にスコア獲得
        # top３チーム取得して、結果のassertion
        pass


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
        # NOTE: チームから、サーバやベンチマーカーが特定できるので、走行に必要な情報は一通り揃う
        job_id = BenchQueue.objects.enqueue(self.team)
        # ジョブはまだ待ち状態のはず
        job = BenchQueue.objects.get(pk=job_id)
        self.assertEqual(BenchQueue.WAITING, job.status)

        # ベンチマーカーがジョブの走行を開始
        job2 = BenchQueue.objects.dequeue(job.target_hostname)
        # ジョブは走行中に遷移する
        self.assertEqual(BenchQueue.RUNNING, job2.status)

        # ベンチマーカーがジョブの完了を通知
        job3 = BenchQueue.objects.get(pk=job_id)
        job3.done('{"score": 100, "pass": true}', "blah\nblah\nblah")
        job3.refresh_from_db()
        self.assertEqual(BenchQueue.DONE, job3.status)
        self.assertEqual(100, job3.score)
        self.assertTrue(job3.is_passed)

    def test_abort(self):
        # 利用者がジョブ登録
        job_id = BenchQueue.objects.enqueue(self.team)
        job = BenchQueue.objects.get(pk=job_id)

        # ベンチマーカーがジョブの走行を開始
        BenchQueue.objects.dequeue(job.target_hostname)

        # ベンチマーカーが中断を通知
        # FIXME: resultのJSONになんか含めたほうがいい？
        job2 = BenchQueue.objects.get(pk=job_id)
        job2.abort('{}', "blah\nblah\nblah")
        job2.refresh_from_db()
        self.assertEqual(BenchQueue.ABORTED, job2.status)

    def test_duplicate_enqueue(self):
        job_id = BenchQueue.objects.enqueue(self.team)
        job = BenchQueue.objects.get(pk=job_id)

        # 同じチームのジョブを連続で登録すると例外発生
        self.assertRaises(exceptions.DuplicateJobError, lambda: BenchQueue.objects.enqueue(self.team))
        self.assertRaises(exceptions.DuplicateJobError, lambda: BenchQueue.objects.enqueue(self.team))
        self.assertRaises(exceptions.DuplicateJobError, lambda: BenchQueue.objects.enqueue(self.team))

        # 走行状態になっても、ジョブの連続登録は許されない
        BenchQueue.objects.dequeue(job.target_hostname)

        # 同じチームのジョブを連続で登録すると例外発生
        self.assertRaises(exceptions.DuplicateJobError, lambda: BenchQueue.objects.enqueue(self.team))
        self.assertRaises(exceptions.DuplicateJobError, lambda: BenchQueue.objects.enqueue(self.team))
        self.assertRaises(exceptions.DuplicateJobError, lambda: BenchQueue.objects.enqueue(self.team))

        # 成功すれば、再度ジョブ登録が可能
        job.done('{"score": 100, "pass": true}', "")
        job_id2 = BenchQueue.objects.enqueue(self.team)

        # enqueueしてから同じチームのジョブを連続で登録すると例外発生
        self.assertRaises(exceptions.DuplicateJobError, lambda: BenchQueue.objects.enqueue(self.team))
        self.assertRaises(exceptions.DuplicateJobError, lambda: BenchQueue.objects.enqueue(self.team))
        self.assertRaises(exceptions.DuplicateJobError, lambda: BenchQueue.objects.enqueue(self.team))

        # 失敗しても、再度のジョブ登録が可能になる
        job2 = BenchQueue.objects.get(pk=job_id2)
        job2.abort('{"score": 100, "pass": true}', "")
        BenchQueue.objects.enqueue(self.team)

    def test_abort_timeout(self):
        target_job_id = BenchQueue.objects.enqueue(self.team)
        target_job = BenchQueue.objects.get(pk=target_job_id)

        BenchQueue.objects.dequeue(target_job.target_hostname)

        # ジョブを直近２秒間更新されてない状態にする
        time.sleep(2)

        BenchQueue.objects.abort_timeout(timeout_sec=1)

        aborted_job = BenchQueue.objects.get(pk=target_job_id)
        self.assertEqual(BenchQueue.ABORTED, aborted_job.status)

    def test_concurrency(self):
        """並列度チェック"""
        user2 = User.objects.create(username="user2")
        team2 = Team.objects.create(
            owner=user2,
            benchmarker=self.benchmarker,
            name="team2",
            password="hogehoge",
        )
        Server.objects.create(team=team2, hostname="fuga", private_ip="xxx.xxx.xxx.xx2", global_ip="yyy.yyy.yyy.yy2", private_network="zzz.zzz.zzz.zz2")

        # ２つジョブをenqueue
        job_id = BenchQueue.objects.enqueue(self.team)
        job = BenchQueue.objects.get(pk=job_id)
        job_id2 = BenchQueue.objects.enqueue(team2)
        job2 = BenchQueue.objects.get(pk=job_id2)

        # １並列はおk
        BenchQueue.objects.dequeue(job.target_hostname, max_concurrency=1)

        # ２並列はダメ
        self.assertRaises(
            exceptions.JobCountReachesMaxConcurrencyError,
            lambda: BenchQueue.objects.dequeue(job2.target_hostname, max_concurrency=1),
        )

