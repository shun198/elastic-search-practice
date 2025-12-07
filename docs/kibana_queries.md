# Kibana クエリ集

# 参考文献
https://www.elastic.co/docs/reference/query-languages/query-dsl/full-text-filter-tutorial

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

## 追加・更新クエリ

### 16. 新規ドキュメントを追加（IDを自動生成）
```json
POST /sample-index/_doc
{
  "title": "New Document",
  "body": "新規追加されたドキュメントです",
  "tag": "new"
}
```

### 17. 指定IDでドキュメントを追加/更新（ID=4を追加、既存なら更新）
```json
PUT /sample-index/_doc/4
{
  "title": "Updated Document",
  "body": "更新されたドキュメントです",
  "tag": "updated"
}
```

### 18. 部分更新（ID=1のtitleのみ更新）
```json
POST /sample-index/_update/1
{
  "doc": {
    "title": "Updated Title"
  }
}
```

### 19. スクリプトを使った更新（ID=1のtagを"updated"に変更）
```json
POST /sample-index/_update/1
{
  "script": {
    "source": "ctx._source.tag = 'updated'"
  }
}
```

### 20. 条件付き更新（tagが"demo"の場合のみtitleを更新）
```json
POST /sample-index/_update/1
{
  "script": {
    "source": "if (ctx._source.tag == 'demo') { ctx._source.title = 'Conditional Update' }"
  }
}
```

### 21. 複数ドキュメントを一括追加（bulk）
```json
POST /sample-index/_bulk
{ "index": { "_id": "10" } }
{ "title": "Bulk Doc 1", "body": "一括追加1", "tag": "bulk" }
{ "index": { "_id": "11" } }
{ "title": "Bulk Doc 2", "body": "一括追加2", "tag": "bulk" }
{ "index": { "_id": "12" } }
{ "title": "Bulk Doc 3", "body": "一括追加3", "tag": "bulk" }
```

### 22. 複数ドキュメントを一括更新（bulk）
```json
POST /sample-index/_bulk
{ "update": { "_id": "1" } }
{ "doc": { "title": "Updated Title 1", "tag": "bulk-updated" } }
{ "update": { "_id": "2" } }
{ "doc": { "title": "Updated Title 2", "tag": "bulk-updated" } }
```

### 23. upsert（存在しない場合は追加、存在する場合は更新）
```json
POST /sample-index/_update/5
{
  "doc": {
    "title": "Upsert Document",
    "body": "存在すれば更新、なければ追加",
    "tag": "upsert"
  },
  "doc_as_upsert": true
}
```

## 削除クエリ

### 24. 特定IDのドキュメントを削除（ID=1を削除）
```json
DELETE /sample-index/_doc/1
```

### 25. クエリ条件に一致するドキュメントを削除（tag="demo"のドキュメントを削除）
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

### 26. titleで検索して削除（"Test1"を含むドキュメントを削除）
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

### 27. 全件削除（⚠️ 注意: インデックス内の全ドキュメントを削除）
```json
POST /sample-index/_delete_by_query
{
  "query": {
    "match_all": {}
  }
}
```

### 28. 複数IDを一度に削除
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

### 29. インデックス全体を削除（⚠️ 注意: インデックスごと削除）
```json
DELETE /sample-index
```

