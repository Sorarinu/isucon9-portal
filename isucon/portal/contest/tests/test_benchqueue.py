import time

from django.test import TestCase

from isucon.portal.authentication.models import User, Team
from isucon.portal.contest.models import Server, Benchmarker, ScoreHistory, Job
from isucon.portal.authentication import factories as auth_factories
from isucon.portal.contest import factories as contest_factories
from isucon.portal.contest import exceptions


class JobTest(TestCase):

    def setUp(self):
        self.owner = auth_factories.UserFactory()
        self.team = auth_factories.TeamFactory.create(owner=self.owner)
        self.owner.team = self.team

        self.benchmarker = self.team.benchmarker
        self.server = contest_factories.ServerFactory(team=self.team)

    def test_done(self):
        # 利用者がジョブ登録
        # NOTE: チームから、サーバやベンチマーカーが特定できるので、走行に必要な情報は一通り揃う
        job = Job.objects.enqueue(self.team)
        # ジョブはまだ待ち状態のはず
        self.assertEqual(Job.WAITING, job.status)

        # ベンチマーカーがジョブの走行を開始
        job2 = Job.objects.dequeue()
        # ジョブは走行中に遷移する
        self.assertEqual(Job.RUNNING, job2.status)

        # ベンチマーカーがジョブの完了を通知
        job3 = Job.objects.get(pk=job.id)
        job3.done(score=100, is_passed=True, reason="成功", stdout="blah\nblah\nblah", stderr="blah\nblah\nblah")
        job3.refresh_from_db()
        self.assertEqual(Job.DONE, job3.status)
        self.assertEqual(100, job3.score)
        self.assertTrue(job3.is_passed)

    def test_abort(self):
        # 利用者がジョブ登録
        job = Job.objects.enqueue(self.team)

        # ベンチマーカーがジョブの走行を開始
        Job.objects.dequeue()

        # ベンチマーカーが中断を通知
        # NOTE: resultのJSONになんか含めたほうがいい？
        job2 = Job.objects.get(pk=job.id)
        job2.abort(reason="Benchmark Timeout", stdout="blah\nblah\nblah", stderr="blah\nblah\nblah")
        job2.refresh_from_db()
        self.assertEqual(Job.ABORTED, job2.status)

    def test_duplicate_enqueue(self):
        job = Job.objects.enqueue(self.team)

        # 同じチームのジョブを連続で登録すると例外発生
        self.assertRaises(exceptions.DuplicateJobError, lambda: Job.objects.enqueue(self.team))
        self.assertRaises(exceptions.DuplicateJobError, lambda: Job.objects.enqueue(self.team))
        self.assertRaises(exceptions.DuplicateJobError, lambda: Job.objects.enqueue(self.team))

        # 走行状態になっても、ジョブの連続登録は許されない
        Job.objects.dequeue()

        # 同じチームのジョブを連続で登録すると例外発生
        self.assertRaises(exceptions.DuplicateJobError, lambda: Job.objects.enqueue(self.team))
        self.assertRaises(exceptions.DuplicateJobError, lambda: Job.objects.enqueue(self.team))
        self.assertRaises(exceptions.DuplicateJobError, lambda: Job.objects.enqueue(self.team))

        # 成功すれば、再度ジョブ登録が可能
        job.done(score=100, is_passed=True, reason="成功しました", stdout="", stderr="")
        job2 = Job.objects.enqueue(self.team)

        # enqueueしてから同じチームのジョブを連続で登録すると例外発生
        self.assertRaises(exceptions.DuplicateJobError, lambda: Job.objects.enqueue(self.team))
        self.assertRaises(exceptions.DuplicateJobError, lambda: Job.objects.enqueue(self.team))
        self.assertRaises(exceptions.DuplicateJobError, lambda: Job.objects.enqueue(self.team))

        # 失敗しても、再度のジョブ登録が可能になる
        job2.abort(reason="Benchmark Timeout", stdout="", stderr="")
        Job.objects.enqueue(self.team)

    def test_abort_timeout(self):
        job = Job.objects.enqueue(self.team)

        Job.objects.dequeue()

        # ジョブを直近２秒間更新されてない状態にする
        time.sleep(2)

        Job.objects.discard_timeout_jobs(timeout_sec=1)

        aborted_job = Job.objects.get(pk=job.id)
        self.assertEqual(Job.ABORTED, aborted_job.status)

    def test_of_team(self):
        """特定チームのジョブ取得テスト"""
        # ジョブをいくつか走行させる
        for idx in range(11):
            job = Job.objects.enqueue(self.team)
            job.done(score=idx, is_passed=True, reason="成功しました", stdout="logloglog", stderr="logloglog")

        # それらのジョブが取得できるか
        jobs = Job.objects.of_team(self.team)
        self.assertEqual(len(jobs), 11)

    def test_job_detail_view(self):
        # views.job_detail に対するテスト
        # ジョブをいくつか走行させる
        # 特定のジョブの詳細を取得
        # ジョブのステータスを変更
        # 再度取得して更新されている
        pass
