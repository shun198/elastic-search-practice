import os
from elasticsearch import Elasticsearch

ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")

es = Elasticsearch(ES_HOST)

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