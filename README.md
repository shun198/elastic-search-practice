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
- `shoplane-prod-commerce-events-01` 〜 `shoplane-prod-commerce-events-05` を作成
- 各インデックスに100件（合計500件）投入
- `shoplane-prod-user-profile-01` を作成（120件）
- `shoplane-prod-app-logs-01` を作成（180件）
- Kibana Data view `Shoplane Commerce Events` を `shoplane-prod-commerce-events-*` で自動作成
- 追加で `Shoplane User Profiles` / `Shoplane App Logs` も自動作成
- トリガー別 Data view (`Cart In` / `Purchase` / `Search`) も自動作成
- `message` / `event_type` / `level` / `order_id` などEC業務向け項目を投入

必要に応じて件数やパターンを変更したい場合:
```bash
uv run scripts/seed_bulk_data.py \
  --index-count 5 \
  --docs-per-index 100 \
  --user-profile-count 120 \
  --app-log-count 180 \
  --reset
```

別カテゴリ名で試したい場合は `--index-prefix` と `--data-view-name` を上書きできます。

```bash
uv run scripts/seed_bulk_data.py \
  --index-prefix myteam-prod-support-events \
  --data-view-name "MyTeam Support Events" \
  --index-count 5 \
  --docs-per-index 100 \
  --reset
```

既存インデックスで `Fielddata is disabled on [tag]` が出た場合は、
`--reset` を付けて再作成してください（`tag`/`category` を keyword で作り直します）。

## テストの実行
```bash
mise run test
```