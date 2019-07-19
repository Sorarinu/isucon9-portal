import requests
import json

from django.conf import settings

from isucon.portal.authentication.models import *


def notify_registration():
    """Slackに登録状況を出力する"""

    users = User.objects.filter(team__isnull=False)

    users_count = users.count()
    team_count = Team.objects.count()

    students_count = users.filter(is_student=True).count()

    attachments =  [

        {
            'fields': [
                {
                    "title": "参加者数",
                    "value": "{}人".format(users.count()),
                    "short": True,
                },
                {
                    "title": "学生数",
                    "value": "{}人".format(students_count),
                    "short": True,
                },
            ],
        },

        {
            'fields': [
                {
                    "title": "チーム数",
                    "value": "{}チーム".format(team_count),
                    "short": True,
                },
            ],
        },

    ]

    text = "最新の登録状況です"
    data = {
      'payload': json.dumps({'text': text,'attachments': attachments}),
    }

    # setup channel webhook
    webhook_url = settings.SLACK_ENDPOINT_URL

    # send it
    requests.post(webhook_url, data=data)
