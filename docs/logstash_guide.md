# Logstash 入門ガイド 🔧

このドキュメントでは、**Logstash の基本的な仕組みと実践的な使い方**について解説します。サンプルのパイプライン設定や Filebeat 設定、よく使うフィルターの例、トラブルシュートのヒントも含めています。既にこのリポジトリの `logstash/pipeline/logstash.conf` にシンプルな Beats -> Elasticsearch の出力が定義されています（参考にしてください）。

---

## 目次
1. 概要
2. 基本コンポーネント
3. サンプルパイプライン（File input -> Grok -> Date -> Elasticsearch）
4. Filebeat と併用する例（Beats -> Logstash）
5. 実行方法 / デバッグ
6. よく使うフィルター一覧
7. ベストプラクティス & 注意点
8. 参考リンク

---

## 1. 概要 💡
- Logstash はログの受け取り（Input）、解析・変換（Filter）、出力（Output）を行うデータパイプラインです。
- プラグインベースで拡張可能（input/filter/output/codec など）。

---

## 2. 基本コンポーネント 🔧
- input: データの取り込み元（例: beats, file, tcp, http）
- filter: データの解析と変換（例: grok, date, mutate, json）
- output: データの出力先（例: elasticsearch, stdout, file）

---

## 3. サンプルパイプライン: ファイルログをパースして Elasticsearch に送る
下記を `logstash/pipeline/myapp.conf` として配置するか、既存のパイプラインに追加してください。

```conf
input {
  file {
    path => "/var/log/myapp/*.log"
    start_position => "beginning"
    sincedb_path => "/dev/null"  # 開発用：常に先頭から読み取りたい場合
  }
}

filter {
  grok {
    match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:message}" }
    # grok デバッグには "grokdebugger" を公式ページで利用できます
  }

  date {
    match => [ "timestamp", "ISO8601" ]
    target => "@timestamp"
  }

  mutate {
    remove_field => [ "timestamp" ]
  }
}

output {
  elasticsearch {
    hosts => ["http://elasticsearch:9200"]
    index => "myapp-%{+YYYY.MM.dd}"
  }
  stdout { codec => rubydebug }
}
```

説明:
- `grok` でログ行を構造化（timestamp, level, message など）
- `date` で日時文字列を `@timestamp` に変換
- 開発時は `stdout` を付けて出力を確認すると便利

---

## 4. Filebeat（Beats）と組み合わせる例
既にリポジトリの `logstash/pipeline/logstash.conf` は Beats をリッスンして Elasticsearch に出力する設定になっています。
Filebeat 側の最小設定例:

```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/myapp/*.log

output.logstash:
  hosts: ["logstash:5044"]
```

Logstash 側は以下のように `beats` input を使用します（既存の `logstash.conf` を参照）:

```conf
input {
  beats { port => 5044 }
}
```

---

## 5. 実行方法とデバッグ 🧭
- Docker Compose（リポジトリに docker-compose がある場合）:
  - `docker-compose up -d logstash` で起動
- ローカルで直接:
  - `bin/logstash -f /path/to/pipeline.conf --config.test_and_exit`（設定検証）
  - `bin/logstash -f /path/to/pipeline.conf --log.level debug`（デバッグログ有効）
- よく使うコマンド:
  - `--config.test_and_exit` : 設定ファイルの構文チェック
  - `--log.level` : debug/info/warn などのログレベル
- トラブル: grok がマッチしない → `stdout { codec => rubydebug }` で `message` を確認してパターンを調整

---

## 6. よく使うフィルター一覧（簡易）
- grok: 正規表現ベースでフィールド抽出
- date: 文字列を @timestamp に変換
- mutate: フィールド削除/変更/型変換
- json: JSON 文字列をパースしてフィールド化
- kv: key=value 形式をパース

---

## 7. ベストプラクティス & 注意点 ✅
- 本番では `sincedb` の扱いに注意（ファイルの読み飛ばし / 既読管理）
- pipeline の数・worker 設定でスループットに差が出る（性能検証をする）
- Grok は複雑になりがち→パターンは分割して再利用
- 機密情報のマスクはフィルター段階で行う（例: mutate, gsub）

---

## 8. 参考リンク 🔗
- 公式: https://www.elastic.co/guide/en/logstash/current/index.html
- Grok デバッガ: https://grokdebug.herokuapp.com/ など

---

### 付録: 追加のサンプル（JSON のパース）
```conf
filter {
  json {
    source => "message"
    remove_field => ["message"]
  }
}
```

---

必要に応じて、**実際にリポジトリにサンプルパイプラインファイルを追加**したり、Filebeat のサンプルを `examples/` 配下に作ることもできます。今回、以下のサンプルと簡易テストを追加しました:

- `logstash/pipeline/myapp.conf` — テスト用の TCP input（ポート5055）を使ったサンプルパイプライン（grok → date → stdout）
- `docs/examples/filebeat.yml` — Filebeat のサンプル設定
- `tests/samples/myapp.log` — テスト用ログサンプル
- `scripts/test_logstash_pipeline.sh` — 簡易テストスクリプト（docker-compose 経由で Logstash を起動し、サンプルメッセージを TCP で送信してログを確認します）

実行例:
```bash
chmod +x scripts/test_logstash_pipeline.sh
./scripts/test_logstash_pipeline.sh
```

必要ならさらに Docker Compose のテストサービス追加や、Elasticsearch への自動検証（インデックス確認）を追加できます。追加してほしい改良があれば教えてください！ 🎯
