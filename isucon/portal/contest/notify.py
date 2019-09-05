import requests
import json

from django.conf import settings

from isucon.portal.authentication.models import *


def notify_abort(job):
    """SlackにAbortを出力する"""

    if job.status != job.ABORTED:
        return

    attachments =  [

        {
            "color": "danger",
            'fields': [
                {
                    "title": "JobID",
                    "value": str(job.id),
                    "short": True,
                },
                {
                    "title": "Status",
                    "value": job.get_status_display(),
                    "short": True,
                },
                {
                    "title": "チーム",
                    "value": job.team.name,
                    "short": True,
                },
                {
                    "title": "チームID",
                    "value": str(job.team.id),
                    "short": True,
                },
                {
                    "title": "ベンチマーカ",
                    "value": str(job.benchmarker),
                    "short": True,
                },
                {
                    "title": "ターゲットサーバ",
                    "value": str(job.target_ip),
                    "short": True,
                },
                {
                    "title": "Reason",
                    "value": job.reason,
                    "short": False,
                },
                {
                    "title": "stdout",
                    "value": job.stdout,
                    "short": False,
                },
                {
                    "title": "stderr",
                    "value": job.stderr,
                    "short": False,
                },
            ],
        },

    ]

    text = "JobがAbortしました"
    data = {
      'payload': json.dumps({'text': text,'attachments': attachments}),
    }

    # setup channel webhook
    webhook_url = settings.SLACK_ENDPOINT_URL

    # send it
    requests.post(webhook_url, data=data)
