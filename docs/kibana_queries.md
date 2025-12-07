# Kibana クエリ集

## 基本的なクエリ

### 1. 全件取得（match_all）
```json
GET /sample-index/_search
{
  "query": {
    "match_all": {}
  }
}
```

### 2. 件数制限付き（最初の10件）
```json
GET /sample-index/_search
{
  "size": 10,
  "query": {
    "match_all": {}
  }
}
```

### 3. 特定のフィールドのみ取得
```json
GET /sample-index/_search
{
  "_source": ["title", "tag"],
  "query": {
    "match_all": {}
  }
}
```

## 検索クエリ

### 4. titleで検索（"Test1"を含む）
```json
GET /sample-index/_search
{
  "query": {
    "match": {
      "title": "Test1"
    }
  }
}
```

### 5. bodyで全文検索（"Kibana"を含む）
```json
GET /sample-index/_search
{
  "query": {
    "match": {
      "body": "Kibana"
    }
  }
}
```

### 6. tagで検索（"demo"タグのドキュメント）
```json
GET /sample-index/_search
{
  "query": {
    "term": {
      "tag": "demo"
    }
  }
}
```

### 7. 複数条件（AND検索）
```json
GET /sample-index/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "tag": "demo" } },
        { "match": { "body": "データ" } }
      ]
    }
  }
}
```

### 8. いずれかの条件（OR検索）
```json
GET /sample-index/_search
{
  "query": {
    "bool": {
      "should": [
        { "term": { "tag": "demo" } },
        { "term": { "tag": "tutorial" } }
      ],
      "minimum_should_match": 1
    }
  }
}
```

## 集計・分析クエリ

### 9. tagごとの件数を集計
```json
GET /sample-index/_search
{
  "size": 0,
  "aggs": {
    "tags": {
      "terms": {
        "field": "tag"
      }
    }
  }
}
```

### 10. ソート（titleで昇順）
```json
GET /sample-index/_search
{
  "query": {
    "match_all": {}
  },
  "sort": [
    {
      "title.keyword": {
        "order": "asc"
      }
    }
  ]
}
```

## インデックス情報

### 11. インデックスのマッピング確認
```json
GET /sample-index/_mapping
```

### 12. インデックスの統計情報
```json
GET /sample-index/_stats
```

### 13. ドキュメント件数
```json
GET /sample-index/_count
```

## 特定IDの取得

### 14. ID=1のドキュメントを取得
```json
GET /sample-index/_doc/1
```

### 15. 複数IDを一度に取得
```json
GET /sample-index/_mget
{
  "ids": ["1", "2", "3"]
}
```

## 削除クエリ

### 16. 特定IDのドキュメントを削除（ID=1を削除）
```json
DELETE /sample-index/_doc/1
```

### 17. クエリ条件に一致するドキュメントを削除（tag="demo"のドキュメントを削除）
```json
POST /sample-index/_delete_by_query
{
  "query": {
    "term": {
      "tag": "demo"
    }
  }
}
```

### 18. titleで検索して削除（"Test1"を含むドキュメントを削除）
```json
POST /sample-index/_delete_by_query
{
  "query": {
    "match": {
      "title": "Test1"
    }
  }
}
```

### 19. 全件削除（⚠️ 注意: インデックス内の全ドキュメントを削除）
```json
POST /sample-index/_delete_by_query
{
  "query": {
    "match_all": {}
  }
}
```

### 20. 複数IDを一度に削除
```json
POST /sample-index/_bulk
{
  "delete": { "_id": "1" }
}
{
  "delete": { "_id": "2" }
}
{
  "delete": { "_id": "3" }
}
```

### 21. インデックス全体を削除（⚠️ 注意: インデックスごと削除）
```json
DELETE /sample-index
```

