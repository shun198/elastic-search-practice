import os
from elasticsearch import Elasticsearch

ES_HOST = os.getenv("ES_HOST", "https://localhost:9200")
ES_USER = os.getenv("ES_USER", "elastic")
ES_PASS = os.getenv("ELASTIC_PASSWORD", "changeme")  # .envと合わせる

es = Elasticsearch(
    ES_HOST,
    basic_auth=(ES_USER, ES_PASS),
    verify_certs=False  # 開発環境用: 証明書検証を無効化（本番環境では非推奨）
)

# サンプルデータ
docs = [
    {"title": "Test1", "body": "Elasticsearchデータ投入", "tag": "demo"},
    {"title": "Test2", "body": "Kibanaで可視化できる", "tag": "tutorial"},
    {"title": "Test3", "body": "Pythonからも楽々投入", "tag": "demo"},
]

index = "sample-index"
if not es.indices.exists(index=index):
    es.indices.create(index=index)

for i, doc in enumerate(docs):
    es.index(index=index, id=i+1, document=doc)

print("サンプルデータ投入完了! Kibana『Discover』で sample-index を選択して確認してください。")