import datetime
import random

from django.utils import timezone

import factory
import factory.fuzzy
from faker import Faker

from isucon.portal.contest import models


def random_ip(idx):
    ipv4 = Faker().ipv4()
    octets = ipv4.split('.')[:-1]
    octets.append(idx)
    return '.'.join(map(str, octets))


class InformationFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Information

    description = factory.fuzzy.FuzzyText(length=50)


class BenchmarkerFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Benchmarker

    ip = factory.Sequence(lambda idx: random_ip(idx))


class ServerFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Server

    # NOTE: 紐づくチームは contest.management.commands.manufacture にて設定
    hostname = factory.Sequence(lambda idx: "server{}".format(idx))

    global_ip = factory.Sequence(lambda idx: random_ip(idx))
    private_ip = factory.Sequence(lambda idx: random_ip(idx))


class JobFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Job

    stdout = factory.Faker('sentence')
    stderr = factory.Faker('sentence')

    created_at = factory.fuzzy.FuzzyDate(
        start_date=timezone.now()-datetime.timedelta(days=5),
        end_date=timezone.now()-datetime.timedelta(days=3),
    )
    updated_at = factory.fuzzy.FuzzyDate(
        start_date=timezone.now()-datetime.timedelta(days=2),
        end_date=timezone.now()-datetime.timedelta(days=1),
    )

    @factory.lazy_attribute
    def result_json(self):
        if self.status == models.Job.ABORTED:
            return '{"reason": "Benchmark timeout"}'

        if self.is_passed:
            pass_str = "true"
        else:
            pass_str = "false"

        return '{{ "score": {}, "pass": {} }}'.format(self.score, pass_str)


class ScoreHistoryFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.ScoreHistory

    # NOTE: 紐づくチームは contest.management.commands.manufacture にて設定
    job = factory.LazyAttribute(lambda o: JobFactory(
        team=o.team,
        score=o.score,
        is_passed=o.is_passed,
        status=models.Job.DONE)
    )
    is_passed = factory.fuzzy.FuzzyChoice([True, False])

    @factory.lazy_attribute
    def score(self):
        if self.is_passed:
            return random.randint(10, 90000)

        return 0
