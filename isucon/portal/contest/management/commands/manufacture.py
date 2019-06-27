import random
from django.core.management.base import BaseCommand

from isucon.portal.authentication.factories import TeamFactory, UserFactory
from isucon.portal.contest.factories import ServerFactory, ScoreHistoryFactory, InformationFactory

class Command(BaseCommand):

    def generate_informations(self, info_num):
        InformationFactory.create_batch(info_num)

    def generate_teams(self, team_num):
        for _ in range(team_num):
            # ユーザ作成 -> チーム登録
            owner = UserFactory.create()
            team = TeamFactory.create(owner=owner)

            # チームがownerに設定される
            owner.team = team
            owner.save()
            yield team

    def generate_team_users(self, team):
        user_num = random.randint(0, 2) # 追加メンバは 0 ~ 2
        UserFactory.create_batch(user_num, team=team)

    def generate_servers(self, team, server_num):
        for _ in range(server_num):
            ServerFactory.create(team=team)

    def generate_score_histories(self, team):
        history_num = random.randint(0, 10) # 履歴は0 ~ 10
        for _ in range(history_num):
            ScoreHistoryFactory.create(team=team)

    def add_arguments(self, parser):
        parser.add_argument('-t', '--teams', default=10, type=int, help='Number of servers')
        parser.add_argument('-s', '--servers', default=3, type=int, help='Number of servers per team')
        parser.add_argument('-i', '--informations', default=10, type=int, help='Number of informations')

    def handle(self, *args, **options):
        team_num = options['teams']
        server_num = options['servers']
        info_num = options['informations']

        self.generate_informations(info_num)
        for team in self.generate_teams(team_num):
            self.generate_team_users(team)
            self.generate_servers(team, server_num)
            self.generate_score_histories(team)
