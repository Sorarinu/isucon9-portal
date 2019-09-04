import datetime
import pickle
from pytz import timezone

from django.conf import settings
import redis

from isucon.portal.authentication.models import Team
from isucon.portal.contest.models import Job, Score


jst = timezone('Asia/Tokyo')


class RedisClient:
    # `RedisClientによる操作` の排他制御用ロック
    LOCK = "lock"
    # チーム情報(スコア履歴、ラベル一覧含む)
    TEAM_DICT = "team-dict"


    def __init__(self):
        self.conn = redis.StrictRedis(host=settings.REDIS_HOST)

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
                team_dict = dict(all_labels=set())
                for job in Job.objects.filter(status=Job.DONE).order_by('finished_at').select_related('team'):
                    if job.team.id not in team_dict:
                        team_dict[job.team.id] = dict(labels=[], scores=[])

                    finished_at = self._normalize_finished_at(job.finished_at.astimezone(jst))
                    team_dict[job.team.id]['name'] = job.team.name
                    team_dict[job.team.id]['participate_at'] = job.team.participate_at
                    team_dict[job.team.id]['labels'].append(finished_at)
                    team_dict[job.team.id]['scores'].append(job.score)

                    team_dict['all_labels'].add(finished_at)

                pipeline.set(self.TEAM_DICT, pickle.dumps(team_dict))
                pipeline.execute()
        finally:
            if use_lock:
                lock.release()

    def update_team_cache(self, job):
        """ジョブ追加に伴い、キャッシュデータを更新します"""
        team = job.team

        # ジョブに紐づくチームの情報を用意
        all_labels = set()
        target_team_dict = dict(
            name=team.name,
            participate_at=team.participate_at,
            labels=[],
            scores=[]
        )
        with self.conn.pipeline() as pipeline:
            for job in Job.objects.filter(status=Job.DONE, team=team).order_by('finished_at'):
                finished_at = self._normalize_finished_at(job.finished_at.astimezone(jst))
                target_team_dict['labels'].append(finished_at)
                target_team_dict['scores'].append(job.score)

                all_labels.add(finished_at)

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
            team_dict['all_labels'].update(all_labels)
            team_dict[team.id] = target_team_dict
            self.conn.set(self.TEAM_DICT, pickle.dumps(team_dict))
        finally:
            lock.release()

    def get_graph_data(self, target_team, ranking, is_last_spurt=False):
        """Chart.js によるグラフデータをキャッシュから取得します"""
        target_team_id, target_team_name = target_team.id, target_team.name

        # pickleで保存してあるRedisキャッシュを取得
        team_bytes = self.conn.get(self.TEAM_DICT)
        if team_bytes is None:
            return [], []
        team_dict = pickle.loads(team_bytes)

        # ラストスパートに入ったならば、自チームのみグラフに表示する
        if is_last_spurt:
            if target_team_id in team_dict:
                return list(sorted(team_dict['all_labels'])), [dict(
                    label='{} ({})'.format(target_team_name, target_team_id),
                    data=zip(team_dict[target_team_id]['labels'], team_dict[target_team_id]['scores'])
                )]
            else:
                # ラストスパート時、未得点者はグラフに何も描画されない
                return list(sorted(team_dict['all_labels'])), [dict(
                    label='{} ({})'.format(target_team_name, target_team_id),
                    data=zip([], [])
                )]

        # ラストスパート前は、topNのチームについてグラフ描画を行う
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
        if target_team_id not in ranking and target_team_id in team_dict:
            datasets.append(dict(
                label='{} ({})'.format(target_team_name, target_team_id),
                data=zip(team_dict[target_team_id]['labels'], team_dict[target_team_id]['scores'])
            ))

        return list(sorted(team_dict['all_labels'])), datasets
