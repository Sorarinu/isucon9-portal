from django.test import TestCase

from isucon.portal.authentication.models import User, Team
from isucon.portal.resources.models import Benchmarker
from isucon.portal.history.models import ScoreHistory


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
