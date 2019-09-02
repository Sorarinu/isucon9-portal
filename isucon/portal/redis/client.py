import datetime
import pickle

from django.conf import settings
import redis

from isucon.portal.authentication.models import Team


class RedisClient:
    # Chart.js で用いるラベルのリスト (yy-mm-dd H:M:S な具合の日付文字列リスト)
    LABEL_LISTS = "labels"
    # LABEL_LIST と対応づけられる、チーム情報
    TEAM_DICT = "team-dict"
    # ラベルとスコアのインデックスの対応表
    DATETIME_TO_INDEX_HASHES = "datetime-table"
    # ランキング
    RANKING_ZRANK = "ranking"

    def __init__(self):
        self.conn = redis.StrictRedis(host=settings.REDIS_HOST)

    @staticmethod
    def normalize_dt_str(created_at):
        return created_at.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def get_initial_team_dict():
        team_dict = dict()
        for team in Team.objects.all():
            team_dict[team.id] = dict(
                name=team.name,
                participate_at=team.participate_at,
                scores=[]
            )
        return team_dict

    def add_job(self, job):
        target_team_id, target_team_name = job.team.id, job.team.name
        label = self.normalize_dt_str(job.created_at)
        is_label_exists = self.conn.hexists(self.DATETIME_TO_INDEX_HASHES, label)

        # JSONに固めたチームオブジェクトを取得
        team_bytes = self.conn.get(self.TEAM_DICT)
        if team_bytes is None:
            # team_jsonの初回生成
            team_dict = self.get_initial_team_dict()
        else:
            team_dict = pickle.loads(team_bytes)

        if not is_label_exists:
            with self.conn.pipeline() as pipeline:
                # ラベル追加
                pipeline.rpush(self.LABEL_LISTS, label)

                # ランキング更新
                pipeline.zadd(self.RANKING_ZRANK, {target_team_id: job.score})

                # 他チームのスコアに0初期値を追加 (この値は更新されうる)
                for team_id in team_dict.keys():
                    if team_id == target_team_id:
                        team_dict[target_team_id]['scores'].append(job.score)
                    else:
                        team_dict[team_id]['scores'].append(0)

                pipeline.set(self.TEAM_DICT, pickle.dumps(team_dict))
                pipeline.execute()

            # ラベルとスコアの紐付け対応表更新
            label_idx = self.conn.llen(self.LABEL_LISTS)-1
            self.conn.hset(self.DATETIME_TO_INDEX_HASHES, label, label_idx)
        else:
            # 時刻が存在する場合. 値の更新だけ(対象チームの更新だけでいい)
            label_idx = int(self.conn.hget(self.DATETIME_TO_INDEX_HASHES, label))
            with self.conn.pipeline() as pipeline:
                team_dict[target_team_id]['scores'][label_idx] = job.score
                pipeline.set(self.TEAM_DICT, pickle.dumps(team_dict))
                pipeline.zadd(self.RANKING_ZRANK, {target_team_id: job.score})
                pipeline.execute()

    def get_graph_data(self, target_team, topn=30):
        labels = list(map(lambda label: label.decode(), self.conn.lrange(self.LABEL_LISTS, 0, -1)))
        target_team_id, target_team_name, target_team_paritcipate_at = target_team.id, target_team.name, target_team.participate_at

        # topNランキング取得 (team_id の一覧を取得)
        ranking = list(map(int, self.conn.zrange(self.RANKING_ZRANK, 0, topn, desc=True)))

        team_bytes = self.conn.get(self.TEAM_DICT)
        if team_bytes is None:
            return [], []

        team_dict = pickle.loads(team_bytes)
        datasets = []
        for team_id, team in team_dict.items():
            if team_id not in ranking:
                # グラフにはtopNに含まれる参加者情報しか出さない
                continue
            if team['participate_at'] != target_team_paritcipate_at:
                # グラフには同じ日にちの参加者情報しか出さない
                continue

            datasets.append(dict(
                label='{} ({})'.format(team['name'], team_id),
                data=team['scores']
            ))

        # 自分がランキングに含まれない場合、自分のdataも追加
        if target_team_id not in ranking:
            datasets.append(dict(
                team_id=target_team_id,
                label='{} ({})'.format(target_team_name, target_team_id),
                data=team_dict[target_team_id]['scores']
            ))

        return labels, datasets
