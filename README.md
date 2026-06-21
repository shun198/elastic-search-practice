# elastic-search-practice

## ローカル環境の構築
```bash
mise run up
```

## スクリプトの実行
```bash
mise run script
```

## 5インデックス・500件の事前データ作成
```bash
mise run seed
```

このコマンドで次を自動実行します:
- `practice-logs-1` 〜 `practice-logs-5` を作成
- 各インデックスに100件（合計500件）投入
- Kibana Data view `Practice Logs` を `practice-logs-*` で自動作成

必要に応じて件数やパターンを変更したい場合:
```bash
uv run scripts/seed_bulk_data.py \
  --index-prefix practice-logs \
  --index-count 5 \
  --docs-per-index 100 \
  --data-view-name "Practice Logs" \
  --reset
```

## テストの実行
```bash
mise run test
```