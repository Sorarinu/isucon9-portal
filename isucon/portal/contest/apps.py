from django.apps import AppConfig


class ContestConfig(AppConfig):
    name = 'isucon.portal.contest'

    def ready(self):
        from isucon.portal.contest.signals import create_aggregated_score, update_aggregated_score