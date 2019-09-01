import datetime

from django.conf import settings
import redis

from isucon.portal.authentication.models import Team

HOGE = 1

class RedisClient:
    # Chart.js で用いるラベルのリスト (yy-mm-dd H:M:S な具合の日付文字列リスト)
    LABEL_LISTS = "labels"
    # LABEL_LIST と対応づけられる、チームごとのスコアリスト
    SCORE_LISTS = "team:{team_id}:{team_name}:scores"
    # ラベルとSCORE_LISTのインデックスの対応表
    DATETIME_TO_INDEX_HASHES = "datetime-table"

    def __init__(self):
        self.conn = redis.StrictRedis(host=settings.REDIS_HOST)

    def normalize_dt_str(self, created_at):
        return created_at.strftime('%Y-%m-%d %H:%M:%S')

    def add_job(self, job):
        target_team_id, target_team_name = job.team.id, job.team.name
        label = self.normalize_dt_str(job.created_at)
        is_label_exists = self.conn.hexists(self.DATETIME_TO_INDEX_HASHES, label)

        if not is_label_exists:
            with self.conn.pipeline() as pipeline:
                # ラベルが存在しない場合
                # ラベル追加
                pipeline.rpush(self.LABEL_LISTS, label)

                # 当該チームのスコアを追加
                pipeline.rpush(self.SCORE_LISTS.format(team_id=target_team_id, team_name=target_team_name), job.score)

                # 他チームのスコアに0初期値を追加 (この値は更新されうる)
                for team in Team.objects.all().values("id", "name"):
                    if team['id'] != target_team_id:
                        pipeline.rpush(self.SCORE_LISTS.format(team_id=team['id'], team_name=team['name']), 0)

                pipeline.execute()

            # ラベルとスコアの紐付け対応表更新
            label_idx = self.conn.llen(self.LABEL_LISTS)-1
            self.conn.hset(self.DATETIME_TO_INDEX_HASHES, label, label_idx)
        else:
            # 時刻が存在する場合. 値の更新だけ(対象チームの更新だけでいい)
            label_idx = int(self.conn.hget(self.DATETIME_TO_INDEX_HASHES, label))-1
            self.conn.lset(self.SCORE_LISTS.format(team_id=target_team_id, team_name=target_team_name), label_idx, job.score)

    def get_graph_data(self):
        labels = list(map(lambda label: label.decode(), self.conn.lrange(self.LABEL_LISTS, 0, -1)))

        datasets = []
        for scores_key in self.conn.scan_iter(self.SCORE_LISTS.format(team_id="*", team_name="*")):
            _, team_id, team_name, _ = scores_key.decode().split(':')

            data = map(int, self.conn.lrange(self.SCORE_LISTS.format(team_id=team_id, team_name=team_name), 0, -1))
            datasets.append(dict(
                team_id=team_id,
                label='{} ({})'.format(team_name, team_id),
                data=list(data)
            ))

        return labels, datasets
