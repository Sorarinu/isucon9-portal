from django_slack import slack_message

slack_message('test.slack', {'text': 'hoge'})


def notify_registration():
    """Slackに登録状況を出力する"""
