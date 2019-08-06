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

## POST /internal/job/:id/report/

指定された ジョブIDのベンチマーク結果をポータルに報告します

ベンチマーク結果は以下のような構造をとります

```
type Result struct {
	// ID はジョブのIDです
	ID       int    `json:"id"`
	Score    int    `json:"score"`
	IsPassed bool   `json:"is_passed"`
	Reason   string `json:"reason"`
	Stdout   string `json:"stdout"`
	Stderr   string `json:"stderr"`
}
```

JSONでPOSTするため、 `Content-Type: application/json` ヘッダの指定が必要です

