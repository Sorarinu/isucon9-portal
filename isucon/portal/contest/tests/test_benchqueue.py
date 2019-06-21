import time

from django.test import TestCase

from isucon.portal.authentication.models import User, Team
from isucon.portal.contest.models import Server, Benchmarker, ScoreHistory, Job
from isucon.portal.contest import exceptions


class JobTest(TestCase):

    def setUp(self):
        self.user = User.objects.create()
        self.benchmarker = Benchmarker.objects.create(ip="xxx.xxx.xxx.xxx")
        self.team = Team.objects.create(
            owner=self.user,
            benchmarker=self.benchmarker,
            name="test",
            password="test",
        )
        self.server = Server.objects.create(team=self.team, hostname="hoge", global_ip="xxx.xxx.xxx.xxx", private_ip="yyy.yyy.yyy.yyy")

    def test_done(self):
        # 利用者がジョブ登録
        # NOTE: チームから、サーバやベンチマーカーが特定できるので、走行に必要な情報は一通り揃う
        job_id = Job.objects.enqueue(self.team)
        # ジョブはまだ待ち状態のはず
        job = Job.objects.get(pk=job_id)
        self.assertEqual(Job.WAITING, job.status)

        # ベンチマーカーがジョブの走行を開始
        job2 = Job.objects.dequeue()
        # ジョブは走行中に遷移する
        self.assertEqual(Job.RUNNING, job2.status)

        # ベンチマーカーがジョブの完了を通知
        job3 = Job.objects.get(pk=job_id)
        job3.done('{"score": 100, "pass": true}', "blah\nblah\nblah")
        job3.refresh_from_db()
        self.assertEqual(Job.DONE, job3.status)
        self.assertEqual(100, job3.score)
        self.assertTrue(job3.is_passed)

    def test_abort(self):
        # 利用者がジョブ登録
        job_id = Job.objects.enqueue(self.team)

        # ベンチマーカーがジョブの走行を開始
        Job.objects.dequeue()

        # ベンチマーカーが中断を通知
        # NOTE: resultのJSONになんか含めたほうがいい？
        job2 = Job.objects.get(pk=job_id)
        job2.abort('{}', "blah\nblah\nblah")
        job2.refresh_from_db()
        self.assertEqual(Job.ABORTED, job2.status)

    def test_duplicate_enqueue(self):
        job_id = Job.objects.enqueue(self.team)
        job = Job.objects.get(pk=job_id)

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
        job.done('{"score": 100, "pass": true}', "")
        job_id2 = Job.objects.enqueue(self.team)

        # enqueueしてから同じチームのジョブを連続で登録すると例外発生
        self.assertRaises(exceptions.DuplicateJobError, lambda: Job.objects.enqueue(self.team))
        self.assertRaises(exceptions.DuplicateJobError, lambda: Job.objects.enqueue(self.team))
        self.assertRaises(exceptions.DuplicateJobError, lambda: Job.objects.enqueue(self.team))

        # 失敗しても、再度のジョブ登録が可能になる
        job2 = Job.objects.get(pk=job_id2)
        job2.abort('{"score": 100, "pass": true}', "")
        Job.objects.enqueue(self.team)

    def test_abort_timeout(self):
        job_id = Job.objects.enqueue(self.team)

        Job.objects.dequeue()

        # ジョブを直近２秒間更新されてない状態にする
        time.sleep(2)

        Job.objects.abort_timeout(timeout_sec=1)

        aborted_job = Job.objects.get(pk=job_id)
        self.assertEqual(Job.ABORTED, aborted_job.status)

    def test_get_recent_jobs(self):
        """特定チームの最近のジョブ取得テスト"""
        # ジョブを11件走行
        # NOTE: 走行中ジョブは１チームにつき１つだけなので、完了済みジョブを複数作る
        job_ids = []
        for idx in range(11):
            job_id = Job.objects.enqueue(self.team)
            job = Job.objects.get(pk=job_id)
            job.done('{{"score": {}, "pass": true}}'.format(idx), "logloglog")

            job_ids.append(job_id)

        # 最初に走行させた10件のみ取得され、一番最初に追加した１件が含まれないことをassertion
        recent_jobs = Job.objects.get_recent_jobs(self.team)
        for job in recent_jobs:
            self.assertNotEqual(job.id, job_ids[0])

    def test_get_jobs(self):
        """特定チームのジョブ取得テスト"""
        # ジョブをいくつか走行させる
        for idx in range(11):
            job_id = Job.objects.enqueue(self.team)
            job = Job.objects.get(pk=job_id)
            job.done('{{"score": {}, "pass": true}}'.format(idx), "logloglog")

        # それらのジョブが取得できるか
        jobs = Job.objects.get_jobs(self.team)
        self.assertEqual(len(jobs), 11)

    def test_job_detail_view(self):
        # views.job_detail に対するテスト
        # ジョブをいくつか走行させる
        # 特定のジョブの詳細を取得
        # ジョブのステータスを変更
        # 再度取得して更新されている
        pass