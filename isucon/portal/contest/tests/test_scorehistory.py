from django.test import TestCase

from isucon.portal.authentication import factories as auth_factories
from isucon.portal.contest import factories as contest_factories
from isucon.portal.authentication.models import User, Team
from isucon.portal.contest.models import Server, Benchmarker, ScoreHistory, Job, Score
from isucon.portal.contest import exceptions


class ScoreHistoryTest(TestCase):

    def setUp(self):
        self.owner = auth_factories.UserFactory.create()
        self.team = auth_factories.TeamFactory.create(owner=self.owner)
        self.owner.team = self.team

        self.benchmarker = self.team.benchmarker
        self.server = contest_factories.ServerFactory(team=self.team)

    def test_get_latest_score(self):
        """指定チームの最新スコアを取得するテスト"""
        # 同一チームのスコア履歴を複数作成
        # FIXME: seedデータに置き換え
        for i in range(10):
            want_entry = ScoreHistory.objects.create(team=self.team, score=i, is_passed=True)

        # スコア履歴のもので最新のものを取得できているか
        got_entry = ScoreHistory.objects.get_latest_score(self.team.id)
        self.assertEqual(got_entry.created_at, want_entry.created_at)

    def test_get_top_teams(self):
        """トップnチーム取得のテスト"""
        # 10チーム生成
        # FIXME: seedデータに置き換え
        teams = []
        for idx in range(10):
            owner = auth_factories.UserFactory.create()
            team = auth_factories.TeamFactory.create(owner=owner)
            owner.team = team
            teams.append(team)

            # 適当にスコア獲得
            ScoreHistory.objects.create(team=team, score=idx, is_passed=True)

        # top３チーム取得して、結果のassertion
        want_score = len(teams)-1
        top_teams = Score.objects.passed()[:3]
        for score in top_teams:
            self.assertEqual(score.best_score, want_score)
            want_score -= 1
