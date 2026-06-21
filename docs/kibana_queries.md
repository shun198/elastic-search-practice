# Kibana クエリ集（EC実践版）

## 前提
- `mise run seed` 実行後を前提にしています
- 作成される主な Data view:
  - `Shoplane Commerce Events` (`shoplane-prod-commerce-events-*`)
  - `Shoplane User Profiles` (`shoplane-prod-user-profile-*`)
  - `Shoplane App Logs` (`shoplane-prod-app-logs-*`)
  - `Shoplane Cart In Events` (`shoplane-commerce-cart-in`)
  - `Shoplane Purchase Events` (`shoplane-commerce-purchase`)
  - `Shoplane Search Events` (`shoplane-commerce-search`)

## 参考
- https://www.elastic.co/docs/reference/query-languages/query-dsl/full-text-filter-tutorial

## Commerce Events 基本

### 1) 全件取得
```json
GET /shoplane-prod-commerce-events-01/_search
{
  "query": { "match_all": {} }
}
```

### 2) 先頭10件
```json
GET /shoplane-prod-commerce-events-01/_search
{
  "size": 10,
  "query": { "match_all": {} }
}
```

### 3) 必要フィールドだけ取得
```json
GET /shoplane-prod-commerce-events-01/_search
{
  "_source": ["@timestamp", "event_type", "service", "user_id", "cart_value_jpy"],
  "query": { "match_all": {} },
  "size": 10
}
```

### 4) event_type で絞り込み（purchase）
```json
GET /shoplane-prod-commerce-events-01/_search
{
  "query": {
    "term": { "event_type": "purchase" }
  }
}
```

### 5) service + status_code の複合条件
```json
GET /shoplane-prod-commerce-events-01/_search
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "service": "payments-api" } },
        { "term": { "status_code": 200 } }
      ]
    }
  }
}
```

### 6) 直近30分
```json
GET /shoplane-prod-commerce-events-*/_search
{
  "query": {
    "range": {
      "@timestamp": {
        "gte": "now-30m",
        "lt": "now"
      }
    }
  },
  "sort": [{ "@timestamp": { "order": "desc" } }],
  "size": 20
}
```

### 7) 遅延イベント抽出（response_time_ms >= 300）
```json
GET /shoplane-prod-commerce-events-*/_search
{
  "query": {
    "range": {
      "response_time_ms": { "gte": 300 }
    }
  },
  "sort": [{ "response_time_ms": { "order": "desc" } }]
}
```

## Commerce Events 集計

### 8) event_type ごとの件数
```json
GET /shoplane-prod-commerce-events-*/_search
{
  "size": 0,
  "aggs": {
    "by_event_type": {
      "terms": { "field": "event_type" }
    }
  }
}
```

### 9) service ごとの平均応答時間
```json
GET /shoplane-prod-commerce-events-*/_search
{
  "size": 0,
  "aggs": {
    "by_service": {
      "terms": { "field": "service" },
      "aggs": {
        "avg_latency": { "avg": { "field": "response_time_ms" } }
      }
    }
  }
}
```

### 10) customer_tier ごとの購入金額合計
```json
GET /shoplane-prod-commerce-events-*/_search
{
  "size": 0,
  "query": {
    "term": { "event_type": "purchase" }
  },
  "aggs": {
    "by_tier": {
      "terms": { "field": "customer_tier" },
      "aggs": {
        "total_value": { "sum": { "field": "cart_value_jpy" } }
      }
    }
  }
}
```

## Trigger 別（Alias）

### 11) Cart In イベント
```json
GET /shoplane-commerce-cart-in/_search
{
  "size": 20,
  "sort": [{ "@timestamp": { "order": "desc" } }]
}
```

### 12) Purchase イベント
```json
GET /shoplane-commerce-purchase/_search
{
  "size": 20,
  "sort": [{ "@timestamp": { "order": "desc" } }]
}
```

### 13) Search イベント
```json
GET /shoplane-commerce-search/_search
{
  "size": 20,
  "sort": [{ "@timestamp": { "order": "desc" } }]
}
```

## User Profile

### 14) プロファイル一覧（10件）
```json
GET /shoplane-prod-user-profile-*/_search
{
  "size": 10,
  "query": { "match_all": {} }
}
```

### 15) customer_tier ごとの人数
```json
GET /shoplane-prod-user-profile-*/_search
{
  "size": 0,
  "aggs": {
    "by_tier": {
      "terms": { "field": "customer_tier" }
    }
  }
}
```

### 16) 非アクティブユーザー抽出
```json
GET /shoplane-prod-user-profile-*/_search
{
  "query": {
    "term": { "is_active": false }
  }
}
```

## App Logs

### 17) ERROR ログのみ
```json
GET /shoplane-prod-app-logs-*/_search
{
  "query": {
    "term": { "level": "ERROR" }
  },
  "sort": [{ "@timestamp": { "order": "desc" } }],
  "size": 50
}
```

### 18) service ごとのログ件数
```json
GET /shoplane-prod-app-logs-*/_search
{
  "size": 0,
  "aggs": {
    "by_service": {
      "terms": { "field": "service" }
    }
  }
}
```

## 調査テンプレート（深掘り）

### 19) 障害調査: ERROR/WARN の時系列推移（5分バケット）
```json
GET /shoplane-prod-app-logs-*/_search
{
  "size": 0,
  "query": {
    "terms": {
      "level": ["ERROR", "WARN"]
    }
  },
  "aggs": {
    "over_time": {
      "date_histogram": {
        "field": "@timestamp",
        "fixed_interval": "5m"
      },
      "aggs": {
        "by_level": {
          "terms": {
            "field": "level"
          }
        }
      }
    }
  }
}
```

### 20) 性能調査: endpoint ごとの P95 応答時間
```json
GET /shoplane-prod-commerce-events-*/_search
{
  "size": 0,
  "aggs": {
    "by_endpoint": {
      "terms": { "field": "endpoint" },
      "aggs": {
        "p95_latency": {
          "percentiles": {
            "field": "response_time_ms",
            "percents": [95]
          }
        }
      }
    }
  }
}
```

### 21) 品質調査: status_code 5xx のイベント抽出
```json
GET /shoplane-prod-commerce-events-*/_search
{
  "query": {
    "range": {
      "status_code": { "gte": 500, "lt": 600 }
    }
  },
  "sort": [{ "@timestamp": { "order": "desc" } }],
  "size": 50
}
```

### 22) ボトルネック調査: service 別の高遅延割合
```json
GET /shoplane-prod-commerce-events-*/_search
{
  "size": 0,
  "aggs": {
    "by_service": {
      "terms": { "field": "service" },
      "aggs": {
        "slow_events": {
          "filter": {
            "range": { "response_time_ms": { "gte": 300 } }
          }
        },
        "all_events": {
          "value_count": { "field": "doc_number" }
        }
      }
    }
  }
}
```

### 23) ユーザー行動調査: 特定 user_id の時系列イベント
```json
GET /shoplane-prod-commerce-events-*/_search
{
  "query": {
    "term": { "user_id": "user-0001" }
  },
  "_source": ["@timestamp", "event_type", "service", "status_code", "cart_value_jpy"],
  "sort": [{ "@timestamp": { "order": "asc" } }],
  "size": 100
}
```

### 24) 収益調査: 直近24時間の購入件数と売上合計
```json
GET /shoplane-commerce-purchase/_search
{
  "size": 0,
  "query": {
    "range": {
      "@timestamp": { "gte": "now-24h", "lt": "now" }
    }
  },
  "aggs": {
    "purchase_count": { "value_count": { "field": "order_id" } },
    "total_revenue": { "sum": { "field": "cart_value_jpy" } }
  }
}
```

### 25) 顧客分析: tier × event_type のクロス集計
```json
GET /shoplane-prod-commerce-events-*/_search
{
  "size": 0,
  "aggs": {
    "by_tier": {
      "terms": { "field": "customer_tier" },
      "aggs": {
        "by_event_type": {
          "terms": { "field": "event_type" }
        }
      }
    }
  }
}
```

### 26) トレース調査: trace_id で commerce と app logs を突合
```json
GET /shoplane-prod-commerce-events-*,shoplane-prod-app-logs-*/_search
{
  "query": {
    "term": { "trace_id": "trace-01-00001" }
  },
  "_source": ["@timestamp", "service", "event_type", "level", "message", "status_code"],
  "sort": [{ "@timestamp": { "order": "asc" } }]
}
```

## 更新・削除系（練習用）

### 27) ドキュメント部分更新
```json
POST /shoplane-prod-commerce-events-01/_update/1
{
  "doc": {
    "tag": "promotion"
  }
}
```

### 28) 条件に一致するイベント削除（注意）
```json
POST /shoplane-prod-commerce-events-01/_delete_by_query
{
  "query": {
    "term": { "event_type": "search" }
  }
}
```

### 29) インデックス削除（注意）
```json
DELETE /shoplane-prod-commerce-events-01
```
