# isucon9-portal

ISUCON9 Portal

## 予選と本戦の違い

予選時のバージョン [tag/isucon9-qualify](https://github.com/isucon/isucon9-portal/releases/tag/isucon9-qualify) と 本戦時のバージョン [tag/isucon9-final](https://github.com/isucon/isucon9-portal/releases/tag/isucon9-final) の違い。

* 予選バージョンでは各チームのAlibaba Cloud Accountの入力機能があった
* ベンチマーカーとチームを1対1で対応付けした時の動作を修正


## Requirements

* Docker
* Pyhton3
* pip

## Getting Started

ローカル環境では、SQLite3を利用して開発をすることができます。

Redisが必要なため、以下の起動例ではDockerで起動させています。

```bash
git clone git@github.com:chibiegg/isucon9-portal.git
cd isucon9-portal
pip install -r requirements.txt
python manage.py migrate
docker run -d -p 6379:6379 redis
python manage.py runserver
```

### テストデータ生成

```bash
python manage.py manufacture -t 300
```

## Deployment

docker-composeとkubernetesに対応しています。

### kubernetes (minikube)

```bash
make
make apply
```

### docker-compose

```bash
docker-compose build
docker-compose up
```
