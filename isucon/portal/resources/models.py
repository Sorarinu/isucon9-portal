from django.db import models

from isucon.portal.models import LogicalDeleteMixin


class Benchmarker(LogicalDeleteMixin, models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "ベンチマーカー"

    # FIXME: ネットワーク構成により今後変更
    ip = models.CharField("IPアドレス", max_length=100)
    network = models.CharField("ネットワークアドレス", max_length=100)

    # FIXME: これってなんのフィールドなのかまだわかってない
    node = models.CharField("ノード", max_length=100)

    def __str__(self):
        return self.ip


class Server(LogicalDeleteMixin, models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "サーバ"

    # FIXME: group_id を持つモデルが複数あるが、これはGroupモデルとして定義した方が管理の都合上楽そう？
    # 検討必要そうなのでまだ定義してない
    # FIXME: パスワード、鍵認証とかにすればいい気がしたのでまだ追加してない

    hostname = models.CharField("ホスト名", max_length=100, unique=True)

    global_ip = models.CharField("グローバルIPアドレス", max_length=100, unique=True)
    private_ip = models.CharField("プライベートIPアドレス", max_length=100)
    private_network = models.CharField("プライベートネットワークアドレス", max_length=100)

    def __str__(self):
        return self.hostname

