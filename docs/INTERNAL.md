# 内部API仕様

ベンチマーカーとポータル間のやりとりなど、競技者には見えない内部APIの仕様です

## POST /internal/job/dequeue/

ジョブをdequeueして取得します

ジョブは、以下のような構造を取ります

```
type Server struct {
	ID            int    `json:"id"`
	Hostname      string `json:"hostname"`
	GlobalIP      string `json:"global_ip"`
	PrivateIP     string `json:"private_ip"`
	IsBenchTarget bool   `json:"is_bench_target"`
}

type Team struct {
	ID      int       `json:"id"`
	Owner   int       `json:"owner"`
	Name    string    `json:"name"`
	Servers []*Server `json:"servers"`
}

type Job struct {
	ID     int    `json:"id"`
	Team   *Team  `json:"team"`
	Status string `json:"status"`
	Score  int    `json:"score"`
	Reason string `json:"reason"`
	Stdout string `json:"stdout"`
	Stderr string `json:"stderr"`
}
```

JSONですと、以下のようになります

```
{
  "id": 36,
  "team": {
    "id": 1,
    "owner": 2,
    "name": "team0",
    "servers": [
      {
        "id": 1,
        "hostname": "server0",
        "global_ip": "192.55.229.0",
        "private_ip": "121.84.88.0",
        "is_bench_target": true
      },
      {
        "id": 2,
        "hostname": "server1",
        "global_ip": "192.169.90.1",
        "private_ip": "169.139.31.1",
        "is_bench_target": false
      },
      {
        "id": 3,
        "hostname": "server2",
        "global_ip": "192.0.8.2",
        "private_ip": "169.212.209.2",
        "is_bench_target": false
      }
    ]
  },
  "status": "running",
  "score": 0,
  "reason": "これは失敗の原因です",
  "stdout": "これは標準出力です",
  "stderr": "これは標準エラー出力です"
}
```

チームとベンチマーカーが紐づく場合、リクエストしてきたベンチマーカのIPアドレスを元に、ジョブを払い出します

一方、チームとベンチマーカーが紐づかない（共用ベンチマーカーが存在する）場合、チームに関わらずジョブを払い出します

## POST /internal/job/:id/report/

指定された ジョブIDのベンチマーク結果をポータルに報告します

ベンチマーク結果は以下のような構造をとります

```
type Result struct {
	// ID はジョブのIDです
	ID       int    `json:"id"`
	Status   string `json:"status"`
	Score    int    `json:"score"`
	IsPassed bool   `json:"is_passed"`
	Reason   string `json:"reason"`
	Stdout   string `json:"stdout"`
	Stderr   string `json:"stderr"`
}
```

JSONですと、以下のようになります

```
{
  "id": 37,
  "status": "done",
  "score": 120,
  "is_passed": true,
  "reason": "",
  "stdout": "stdout\nstdout\nstdout",
  "stderr": "stderr\nstderr\nstderr"
}
```

JSONでPOSTするため、 `Content-Type: application/json` ヘッダの指定が必要です
