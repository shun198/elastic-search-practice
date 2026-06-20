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

必要に応じて件数を変更したい場合:
```bash
uv run scripts/seed_bulk_data.py --index-count 5 --docs-per-index 100 --reset
```

## テストの実行
```bash
mise run test
```