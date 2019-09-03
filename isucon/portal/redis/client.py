import datetime
import pickle

from django.conf import settings
import redis

from isucon.portal.authentication.models import Team
from isucon.portal.contest.models import Job


class RedisClient:
    # `RedisClientによる操作` の排他制御用ロック
    LOCK = "lock"
    # チーム情報(スコア履歴、ラベル一覧含む)
    TEAM_DICT = "team-dict"
    # ランキング
    RANKING_ZRANK = "participate_at:{participate_at}:ranking"


    def __init__(self):
        self.conn = redis.StrictRedis(host=settings.REDIS_HOST)

    @staticmethod
    def _normalize_participate_at(participate_at):
        return participate_at.strftime('%Y%m%d')

    @staticmethod
    def _normalize_finished_at(finished_at):
        return finished_at.strftime('%Y-%m-%d %H:%M:%S')

    def load_cache_from_db(self, use_lock=False):
        """起動時、DBに保存された完了済みジョブをキャッシュにロードします"""
        try:
            if use_lock:
                lock = self.conn.lock(self.LOCK)
                lock.acquire(blocking=True)

            with self.conn.pipeline() as pipeline:
                team_dict = dict()
                for job in Job.objects.filter(status=Job.DONE).order_by('finished_at').select_related('team'):
                    if job.team.id not in team_dict:
                        team_dict[job.team.id] = dict(labels=[], scores=[])

                    finished_at = self._normalize_finished_at(job.finished_at)
                    team_dict[job.team.id]['name'] = job.team.name
                    team_dict[job.team.id]['participate_at'] = job.team.participate_at
                    team_dict[job.team.id]['labels'].append(finished_at)
                    team_dict[job.team.id]['scores'].append(job.score)

                    participate_at = self._normalize_participate_at(job.team.participate_at)
                    pipeline.zadd(self.RANKING_ZRANK.format(participate_at=participate_at), {job.team.id: job.score})

                pipeline.set(self.TEAM_DICT, pickle.dumps(team_dict))
                pipeline.execute()
        finally:
            if use_lock:
                lock.release()

    def update_team_cache(self, job):
        """ジョブ追加に伴い、キャッシュデータを更新します"""
        team = job.team

        # ジョブに紐づくチームの情報を用意
        target_team_dict = dict(
            name=team.name,
            participate_at=team.participate_at,
            labels=[],
            scores=[]
        )
        participate_at = self._normalize_participate_at(team.participate_at)
        with self.conn.pipeline() as pipeline:
            for job in Job.objects.filter(status=Job.DONE, team=team).order_by('finished_at'):
                finished_at = self._normalize_finished_at(job.finished_at)
                target_team_dict['labels'].append(finished_at)
                target_team_dict['scores'].append(job.score)

                # ランキングの更新
                pipeline.zadd(self.RANKING_ZRANK.format(participate_at=participate_at), {team.id: job.score})
            pipeline.execute()

        try:
            lock = self.conn.lock(self.LOCK)
            lock.acquire(blocking=True)

            # チーム情報を取得
            team_dict = self.conn.get(self.TEAM_DICT)
            if team_dict is None:
                # NOTE: manufacture でシードデータを投入する場合、ここを通る
                #       デプロイ先だと、team_dict は必ずentrypoint.shで作成されるのでここを通らない
                self.load_cache_from_db()
                team_dict = self.conn.get(self.TEAM_DICT)
            team_dict = pickle.loads(team_dict)

            # チームの情報を丸ごと更新
            team_dict[team.id] = target_team_dict
            self.conn.set(self.TEAM_DICT, pickle.dumps(team_dict))
        finally:
            lock.release()

    def get_graph_data(self, target_team, topn=30):
        """Chart.js によるグラフデータをキャッシュから取得します"""
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
