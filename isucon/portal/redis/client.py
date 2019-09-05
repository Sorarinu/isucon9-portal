from contextlib import contextmanager
import datetime
import pickle
from pytz import timezone

from django.conf import settings
import redis

from isucon.portal import utils as portal_utils
from isucon.portal.authentication.models import Team
from isucon.portal.contest.models import Job, Score


jst = timezone('Asia/Tokyo')


class TeamDict:
    """チーム情報を格納するデータ構造"""

    def __init__(self, team, labels=None, scores=None):
        self.id = team.id
        self.name = team.name
        self.participate_at = team.participate_at
        self.labels = [] if labels is None else labels
        self.scores = [] if scores is None else scores

        self._team = team

    @property
    def label(self):
        return '{} ({})'.format(self.name, self.id)

    @property
    def data(self):
        return zip(self.labels, self.scores)

    @property
    def unique_labels(self):
        return set(self.labels)

    @property
    def last_label(self):
        if len(self.labels) == 0:
            return None
        return self.labels[-1]

    @staticmethod
    def _normalize_finished_at(finished_at):
        return finished_at.strftime('%Y-%m-%d %H:%M:%S')

    def append_job(self, job):
        finished_at = self._normalize_finished_at(job.finished_at.astimezone(jst))

        self.labels.append(finished_at)
        self.scores.append(job.score)

    def __add__(self, other):
        # 非破壊的に、足し合わせたTeamDictを返す
        labels = self.labels[:]
        labels.extend(other.labels)
        scores = self.scores[:]
        scores.extend(other.scores)

        return TeamDict(team=self._team, labels=labels, scores=scores)


class TeamDictLoadCacheSet:
    """TeamDictに全データをロードし直す際用いるクラス"""

    def __init__(self):
        self.teams_dict = dict()
        self.lastspurt_teams_dict = dict()

        self.labels = set()

    def append_job(self, job):
        """ラストスパート判定をしつつ、TeamDictにappend_jobする"""
        is_last_spurt = portal_utils.is_last_spurt(job.finished_at)

        if not is_last_spurt:
            # teams_dict, labelsに格納
            if job.team.id not in self.teams_dict:
                self.teams_dict[job.team.id] = TeamDict(job.team)
            self.teams_dict[job.team.id].append_job(job)
            self.labels.add(self.teams_dict[job.team.id].last_label)
        else:
            # lastspurt_teams_dict, labelsに格納
            if job.team.id not in self.lastspurt_teams_dict:
                self.lastspurt_teams_dict[job.team.id] = TeamDict(job.team)
            self.lastspurt_teams_dict[job.team.id].append_job(job)
            self.labels.add(self.lastspurt_teams_dict[job.team.id].last_label)


class TeamDictUpdateSet:
    """逐次更新でTeamDictを更新する際に用いるクラス"""

    def __init__(self, job):
        self.team_dict = TeamDict(job.team)
        self.lastspurt_team_dict = TeamDict(job.team)

    @property
    def labels(self):
        labels = set()
        labels.update(self.team_dict.unique_labels)
        labels.update(self.lastspurt_team_dict.unique_labels)
        return labels

    def append_job(self, job):
        is_last_spurt = portal_utils.is_last_spurt(job.finished_at)

        if not is_last_spurt:
            self.team_dict.append_job(job)
        else:
            self.lastspurt_team_dict.append_job(job)

@contextmanager
def lock_with_redis(conn, lock_name, use_lock=True):
    if use_lock:
        try:
            lock = conn.lock(lock_name)
            lock.acquire(blocking=True)
            yield lock
        finally:
            lock.release()
    else:
        yield None


class RedisClient:
    # `RedisClientによる操作` の排他制御用ロック
    LOCK = "lock"
    # チーム情報(スコア履歴、ラベル一覧含む)
    TEAM_DICT = "team:{team_id}:team-dict"
    # チームごとの情報であるteam-dictを、チームIDとの対応表で保持する辞書
    TEAMS_DICT = "teams-dict"
    LASTSPURT_TEAMS_DICT = "lastspurt-teams-dict"
    # グラフ描画の際に用いるラベル (finished_at を正規化した文字列)
    LABELS = "labels"


    def __init__(self):
        self.conn = redis.StrictRedis(host=settings.REDIS_HOST)

    def get_labels(self, retry=False):
        """Redisから LABELS pickleを取得するヘルパ"""
        labels_bytes = self.conn.get(self.LABELS)
        if labels_bytes is None:
            # NOTE: manufacture でシードデータを投入する場合、ここを通る
            #       デプロイ先だと、team_dict は必ずentrypoint.shで作成されるのでここを通らない
            self.load_cache_from_db()
            labels_bytes = self.conn.get(self.LABELS)

        if labels_bytes is not None:
            return pickle.loads(labels_bytes)

        return None

    def get_teams_dict(self, is_last_spurt=False):
        """Redisから TEAMS_DICT pickleを取得するヘルパ"""
        if not is_last_spurt:
            key_name = self.TEAMS_DICT
        else:
            key_name = self.LASTSPURT_TEAMS_DICT

        team_bytes = self.conn.get(key_name)
        if team_bytes is None:
            return None

        return pickle.loads(team_bytes)

    def load_cache_from_db(self, use_lock=False):
        """起動時、DBに保存された完了済みジョブをキャッシュにロードします"""
        with lock_with_redis(self.conn, self.LOCK, use_lock=use_lock):
            # 全てのpassedなジョブデータを元にteam_dictを再構成する
            load_cache_set = TeamDictLoadCacheSet()
            for job in Job.objects.filter(status=Job.DONE).order_by('finished_at').select_related('team'):
                load_cache_set.append_job(job)

            with self.conn.pipeline() as pipeline:
                pipeline.set(self.LABELS, pickle.dumps(load_cache_set.labels))

                for team_id, team_dict in load_cache_set.teams_dict.items():
                    pipeline.set(self.TEAM_DICT.format(team_id=team_id), pickle.dumps(team_dict))

                pipeline.set(self.TEAMS_DICT, pickle.dumps(load_cache_set.teams_dict))
                pipeline.set(self.LASTSPURT_TEAMS_DICT, pickle.dumps(load_cache_set.lastspurt_teams_dict))

                pipeline.execute()

    def update_team_cache(self, job):
        """ジョブ追加に伴い、キャッシュデータを更新します"""
        # ジョブに紐づくチームの全ジョブについて、キャッシュを読み込み直す
        update_set = TeamDictUpdateSet(job)
        for job in Job.objects.filter(status=Job.DONE, team=job.team).order_by('finished_at'):
            update_set.append_job(job)

        with lock_with_redis(self.conn, self.LOCK):
            # ラベルを取得
            labels = self.get_labels(retry=True)
            if labels is None:
                return

            # チーム情報を取得
            teams_dict = self.get_teams_dict(is_last_spurt=False)
            if teams_dict is None:
                return

            lastspurt_teams_dict = self.get_teams_dict(is_last_spurt=True)
            if lastspurt_teams_dict is None:
                return

            # チームの情報を丸ごと更新
            labels.update(update_set.labels)
            teams_dict[job.team.id] = update_set.team_dict
            lastspurt_teams_dict[job.team.id] = update_set.lastspurt_team_dict

            # 対象チームごとのteam_dictを更新
            with self.conn.pipeline() as pipeline:
                pipeline.set(self.TEAM_DICT.format(team_id=job.team.id), pickle.dumps(update_set.team_dict))

                pipeline.set(self.LABELS, pickle.dumps(labels))
                pipeline.set(self.TEAMS_DICT, pickle.dumps(teams_dict))

                pipeline.set(self.LASTSPURT_TEAMS_DICT, pickle.dumps(lastspurt_teams_dict))

                pipeline.execute()

    def _prepare_for_lastspurt(self, target_team):
        """lastspurt向けの teams_dict, team_dict, labels を用意します"""
        # team_dictを用意
        team_dict = self.conn.get(self.TEAM_DICT.format(team_id=target_team.id))
        if team_dict is None:
            team_dict = None
        else:
            team_dict = pickle.loads(team_dict)

        lastspurt_teams_dict = self.get_teams_dict(is_last_spurt=True)
        if lastspurt_teams_dict is None:
            return dict(), None, []

        team_dict = team_dict + lastspurt_teams_dict[team_dict.id]

        # teams_dictを用意
        teams_dict = self.get_teams_dict(is_last_spurt=False)
        if teams_dict is None:
            return dict(), None, []
        teams_dict[team_dict.id] = team_dict

        # labelsを用意
        labels = self.get_labels()
        if labels is None:
            labels = []
        labels = list(sorted(labels))

        return teams_dict, team_dict, labels

    def _prepare_for_not_lastspurt(self, target_team):
        """lastspurtでない場合向けの teams_dict, team_dict, labels を用意します"""
        # teams_dict を用意
        teams_dict = self.get_teams_dict(is_last_spurt=False)
        if teams_dict is None:
            teams_dict = dict()

        # team_dict を用意
        if target_team.id in teams_dict:
            team_dict = teams_dict[target_team.id]
        else:
            team_dict = None

        # labels を用意
        labels = self.get_labels()
        if labels is None:
            labels = []
        labels = list(sorted(labels))

        return teams_dict, team_dict, labels

    def _prepare_for_staff(self):
        """staff向けの teams_dict, team_dict, labels を用意します"""
        # teams_dict を用意
        teams_dict = self.get_teams_dict(is_last_spurt=False)
        if teams_dict is None:
            teams_dict = dict()

        lastspurt_teams_dict = self.get_teams_dict(is_last_spurt=True)
        if lastspurt_teams_dict is None:
            lastspurt_teams_dict = dict()

        new_teams_dict = dict()
        for team_id, team_dict in teams_dict.items():
            if team_id in lastspurt_teams_dict:
                new_teams_dict[team_id] = team_dict + lastspurt_teams_dict[team_id]
            else:
                new_teams_dict[team_id] = team_dict

        # labels を用意
        labels = self.get_labels()
        if labels is None:
            labels = []
        labels = list(sorted(labels))

        return new_teams_dict, None, labels

    def get_graph_data(self, target_team, ranking, is_last_spurt=False):
        """Chart.js によるグラフデータをキャッシュから取得します"""
        # teams_dictとteam_dict、labelsを用意
        if is_last_spurt:
            # ラストスパートでは、自分以外のチームのグラフ更新が止まったように見える
            teams_dict, target_team_dict, labels = self._prepare_for_lastspurt(target_team)
        else:
            # どのユーザにおいても、topn rankingに含まれるチームのみグラフで見れる
            teams_dict, target_team_dict, labels = self._prepare_for_not_lastspurt(target_team)

        # teams_dict, team_dict, labels に基づき、ラベルとデータセットを作成して返す
        datasets = []
        for team_id, team_dict in teams_dict.items():
            if team_id not in ranking:
                #  グラフにはtopNに含まれる参加者情報しか出さない
                continue
            if team_dict.participate_at != target_team.participate_at:
                # グラフには同じ日にちの参加者情報しか出さない(スタッフである場合は除く)
                continue

            datasets.append(dict(label=team_dict.label, data=team_dict.data))

        # 自分がランキングに含まれない場合、自分のdataも追加(スタッフである場合は除く)
        if target_team.id not in ranking and target_team_dict is not None:
            datasets.append(dict(label=target_team_dict.label, data=target_team_dict.data))

        return labels, datasets

    def get_graph_data_for_staff(self, participate_at, ranking):
        """Chart.js によるグラフデータをキャッシュから取得します"""
        # NOTE: prepare_for_staff の返値の２つ目(team_dict)はNoneが返ってくる
        #       (=スタッフについて、チームを考慮したグラフデータの特別な加工が必要ないので)
        teams_dict, _, labels = self._prepare_for_staff()

        # teams_dict, labels に基づき、ラベルとデータセットを作成して返す
        datasets = []
        for team_id, team_dict in teams_dict.items():
            if team_id not in ranking:
                #  グラフにはtopNに含まれる参加者情報しか出さない
                continue
            if team_dict.participate_at != participate_at:
                # スタッフは、指定の日の参加者しか出さない
                continue

            datasets.append(dict(label=team_dict.label, data=team_dict.data))

        return labels, datasets

