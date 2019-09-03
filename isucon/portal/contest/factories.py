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
    is_enabled = True


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

    created_at = factory.Sequence(lambda idx: timezone.now()-timezone.timedelta(seconds=random.randint(5, 180)))
    updated_at = factory.Sequence(lambda idx: timezone.now()-timezone.timedelta(seconds=random.randint(5, 180)))

    is_passed = factory.fuzzy.FuzzyChoice([True, False])
    status = factory.fuzzy.FuzzyChoice([models.Job.DONE])

    @factory.lazy_attribute
    def reason(self):
        if self.status == models.Job.ABORTED:
            return "Benchmark timeout"
        return ""

    @factory.lazy_attribute
    def finished_at(self):
        if self.status == models.Job.DONE:
            return self.updated_at
        return None

    @factory.lazy_attribute
    def score(self):
        if self.is_passed:
            return random.randint(10, 90000)

        return 0
