# elastic-search-practice

## ローカル環境の構築
```
mise run up
```

## スクリプトの実行
```
mise run script
```

## テストの実行

### 依存関係のインストール
```bash
uv sync --extra dev
```

### モックを使ったユニットテスト（高速、Elasticsearch不要）
```bash
pytest tests/test_insert_sample_data.py::TestInsertSampleDataWithMock -v
```

### 実際のElasticsearchを使った統合テスト（docker-composeが必要）
```bash
# Elasticsearchが起動していることを確認
docker-compose ps

# 統合テストを実行
pytest tests/test_insert_sample_data.py::TestInsertSampleDataWithRealElasticsearch -v
```

### すべてのテストを実行
```bash
pytest tests/ -v
```