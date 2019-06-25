from django.contrib.auth.hashers import make_password

import factory
import factory.fuzzy

from isucon.portal.authentication import models
from isucon.portal.contest import factories as contest_factories


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.User

    username = factory.Sequence(lambda idx: "user{}".format(idx))
    # NOTE: 最大３人のチームで、３チームに１人くらい学生がいる
    # なお、シード生成の時にチームの人数がランダムになるので、そこで調整が入り、学生の増減がでる
    is_student = factory.Sequence(lambda idx: idx % 9 == 0)

class TeamFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Team

    # NOTE: owner以外は、別スクリプトで設定
    owner = factory.SubFactory(UserFactory)
    benchmarker = factory.SubFactory(contest_factories.BenchmarkerFactory)

    name = factory.Sequence(lambda idx: "team{}".format(idx))
    password = factory.Sequence(lambda idx: make_password("password{}".format(idx)))

    is_active = True
