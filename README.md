# isucon9-portal
ISUCON9 Portal


## Getting Started

```bash
git clone git@github.com:chibiegg/isucon9-portal.git
cd isucon9-portal
pip install -r requirements.txt
python manage.py migrate
docker run -d -p 6379:6379 redis
python manage.py runserver
```


## docker-compose

```bash
docker-compose build
docker-compose up
```


## テストデータ生成

```bash
python manage.py manufacture -t 300
```

## リポジトリを公開にする前にするべきこと

* Slackトークンの失効
* Alibabaクラウドアカウントトークンの失効
