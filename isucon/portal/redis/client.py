import datetime
import pickle

from django.conf import settings
import redis

from isucon.portal.authentication.models import Team


class RedisClient:
    # LABEL_LIST と対応づけられる、チーム情報
    TEAM_DICT = "team-dict"
    # ランキング
    RANKING_ZRANK = "participate_at:{participate_at}:ranking"

    def __init__(self):
        self.conn = redis.StrictRedis(host=settings.REDIS_HOST)

    @staticmethod
    def _normalize_participate_at(participate_at):
        return participate_at.strftime('%Y%m%d')

    @staticmethod
    def _normalize_created_at(created_at):
        return created_at.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def _get_initial_team_dict():
        team_dict = dict()
        for team in Team.objects.all():
            team_dict[team.id] = dict(
                name=team.name,
                participate_at=team.participate_at,
                labels=[],
                scores=[]
            )
        return team_dict

    def add_job(self, job):
        target_team_id = job.team.id
        target_team_participate_at = self._normalize_participate_at(job.team.participate_at)

        # JSONに固めたチームオブジェクトを取得
        team_bytes = self.conn.get(self.TEAM_DICT)
        if team_bytes is None:
            # team_jsonの初回生成
            team_dict = self._get_initial_team_dict()
        else:
            team_dict = pickle.loads(team_bytes)

        label = self._normalize_created_at(job.created_at)
        with self.conn.pipeline() as pipeline:
            # ラベル追加
            team_dict[target_team_id]['labels'].append(label)

            # スコア記録
            team_dict[target_team_id]['scores'].append(job.score)

            pipeline.zadd(self.RANKING_ZRANK.format(participate_at=target_team_participate_at), {target_team_id: job.score})
            pipeline.set(self.TEAM_DICT, pickle.dumps(team_dict))
            pipeline.execute()

    def get_graph_data(self, target_team, topn=30):
        target_team_id, target_team_name = target_team.id, target_team.name
        target_team_participate_at = self._normalize_participate_at(target_team.participate_at)

        # topNランキング取得 (team_id の一覧を取得)
        ranking = list(map(int, self.conn.zrange(self.RANKING_ZRANK.format(participate_at=target_team_participate_at), 0, topn-1, desc=True)))

        team_bytes = self.conn.get(self.TEAM_DICT)
        if team_bytes is None:
            return [], []

        team_dict = pickle.loads(team_bytes)

        datasets = []
        for team_id, team in team_dict.items():
            if team_id not in ranking:
                #  グラフにはtopNに含まれる参加者情報しか出さない
                continue
            if team['participate_at'] != target_team.participate_at:
                # グラフには同じ日にちの参加者情報しか出さない
                continue

            datasets.append(dict(
                label='{} ({})'.format(team['name'], team_id),
                data=zip(team['labels'], team['scores'])
            ))

        # 自分がランキングに含まれない場合、自分のdataも追加
        if target_team_id not in ranking:
            datasets.append(dict(
                label='{} ({})'.format(target_team_name, target_team_id),
                data=zip(team_dict[target_team_id]['labels'], team_dict[target_team_id]['scores'])
            ))

        return datasets
