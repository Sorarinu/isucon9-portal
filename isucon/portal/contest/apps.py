from django.apps import AppConfig


class ContestConfig(AppConfig):
    name = 'isucon.portal.contest'

    def ready(self):
        from isucon.portal.contest.signals import create_default_aggregated_score