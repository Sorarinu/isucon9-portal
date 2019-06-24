from django.contrib.auth.hashers import make_password

import factory
import factory.fuzzy

from isucon.portal.authentication import models
from isucon.portal.contest import factories as contest_factories


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.User

    username = factory.Sequence(lambda idx: "user{}".format(idx))
    is_student = factory.fuzzy.FuzzyChoice([True, False])

class TeamFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Team

    # NOTE: owner以外は、別スクリプトで設定
    owner = factory.SubFactory(UserFactory)
    benchmarker = factory.SubFactory(contest_factories.BenchmarkerFactory)

    name = factory.Sequence(lambda idx: "team{}".format(idx))
    password = factory.Sequence(lambda idx: make_password("password{}".format(idx)))

    is_active = True
