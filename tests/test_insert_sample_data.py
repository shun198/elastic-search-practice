"""
insert_sample_data.py のテストコード
POST/PUT操作を含む
"""

import pytest
from scripts.insert_sample_data import docs, index
from starlette import status


class TestInsertSampleData:
    """実際のElasticsearchを使った統合テスト(docker-composeが必要)"""

    @pytest.fixture
    def es_client(self):
        """Elasticsearchクライアントのフィクスチャ"""
        from elasticsearch import Elasticsearch
        import os
        
        host = os.getenv("ES_HOST", "http://localhost:9200")
        client = Elasticsearch(host)
        
        # 接続確認
        if not client.ping():
            pytest.skip("Elasticsearch is not available")
        
        yield client
        
        # テスト後のクリーンアップ
        try:
            client.indices.delete(index=index, ignore=[status.HTTP_404_NOT_FOUND])
        except Exception:
            pass

    def test_index_creation(self, es_client):
        """インデックスが作成されるかテスト"""
        # 既存のインデックスを削除
        es_client.indices.delete(index=index, ignore=[status.HTTP_404_NOT_FOUND])
        
        # インデックスが存在しないことを確認
        assert not es_client.indices.exists(index=index)
        
        # インデックスを作成
        es_client.indices.create(index=index)
        
        # インデックスが作成されたことを確認
        assert es_client.indices.exists(index=index)

    def test_document_indexing(self, es_client):
        """ドキュメントが正しくインデックスされるかテスト"""
        # インデックスをクリーンアップ
        es_client.indices.delete(index=index, ignore=[status.HTTP_404_NOT_FOUND])
        es_client.indices.create(index=index)
        
        # ドキュメントをインデックス
        for i, doc in enumerate(docs, start=1):
            es_client.index(index=index, id=i, document=doc)
        
        # リフレッシュして検索可能にする
        es_client.indices.refresh(index=index)
        
        # ドキュメントが正しくインデックスされたか確認
        result = es_client.search(index=index, body={"query": {"match_all": {}}})
        assert result["hits"]["total"]["value"] == 3
        
        # 各ドキュメントの内容を確認
        hits = result["hits"]["hits"]
        assert hits[0]["_source"]["title"] == "Test1"
        assert hits[1]["_source"]["title"] == "Test2"
        assert hits[2]["_source"]["title"] == "Test3"

    def test_document_retrieval(self, es_client):
        """インデックスされたドキュメントを取得できるかテスト"""
        # インデックスをクリーンアップ
        es_client.indices.delete(index=index, ignore=[status.HTTP_404_NOT_FOUND])
        es_client.indices.create(index=index)
        
        # ドキュメントをインデックス
        for i, doc in enumerate(docs, start=1):
            es_client.index(index=index, id=i, document=doc)
        
        es_client.indices.refresh(index=index)
        
        # ID=1のドキュメントを取得
        result = es_client.get(index=index, id=1)
        assert result["_source"]["title"] == "Test1"
        assert result["_source"]["body"] == "Elasticsearchデータ投入"
        assert result["_source"]["tag"] == "demo"

    def test_post_new_document_without_id(self, es_client):
        """POST: IDを指定せずに新規ドキュメントを作成"""
        # インデックスをクリーンアップ
        es_client.indices.delete(index=index, ignore=[status.HTTP_404_NOT_FOUND])
        es_client.indices.create(index=index)
        
        # 新規ドキュメント(IDなし)
        new_doc = {
            "title": "POSTテスト",
            "body": "自動生成されたID",
            "tag": "post-test"
        }
        
        # POST操作でドキュメントを作成
        result = es_client.index(index=index, document=new_doc)
        
        # 自動生成されたIDを確認
        assert result["result"] == "created"
        assert "_id" in result
        doc_id = result["_id"]
        
        # リフレッシュ
        es_client.indices.refresh(index=index)
        
        # ドキュメントが作成されたことを確認
        retrieved = es_client.get(index=index, id=doc_id)
        assert retrieved["_source"]["title"] == "POSTテスト"
        assert retrieved["_source"]["body"] == "自動生成されたID"

    def test_post_new_document_with_id(self, es_client):
        """POST: IDを指定して新規ドキュメントを作成"""
        # インデックスをクリーンアップ
        es_client.indices.delete(index=index, ignore=[status.HTTP_404_NOT_FOUND])
        es_client.indices.create(index=index)
        
        # 新規ドキュメント(ID指定)
        new_doc = {
            "title": "POST ID指定",
            "body": "ID=100で作成",
            "tag": "post-with-id"
        }
        
        # POST操作(op_type="create"で新規作成のみ許可)
        result = es_client.index(
            index=index,
            id=100,
            document=new_doc,
            op_type="create"
        )
        
        assert result["result"] == "created"
        assert result["_id"] == "100"
        
        # リフレッシュ
        es_client.indices.refresh(index=index)
        
        # ドキュメントを確認
        retrieved = es_client.get(index=index, id=100)
        assert retrieved["_source"]["title"] == "POST ID指定"

    def test_post_duplicate_id_fails(self, es_client):
        """POST: 既存IDで作成しようとすると失敗する"""
        # インデックスをクリーンアップ
        es_client.indices.delete(index=index, ignore=[status.HTTP_404_NOT_FOUND])
        es_client.indices.create(index=index)
        
        # 最初のドキュメントを作成
        doc1 = {"title": "最初", "body": "1回目", "tag": "test"}
        es_client.index(index=index, id=200, document=doc1, op_type="create")
        
        # 同じIDで再度作成を試みる
        doc2 = {"title": "2回目", "body": "失敗するはず", "tag": "test"}
        
        from elasticsearch import ConflictError
        with pytest.raises(ConflictError):
            es_client.index(index=index, id=200, document=doc2, op_type="create")

    def test_put_update_existing_document(self, es_client):
        """PUT: 既存ドキュメントを更新"""
        # インデックスをクリーンアップ
        es_client.indices.delete(index=index, ignore=[status.HTTP_404_NOT_FOUND])
        es_client.indices.create(index=index)
        
        # 元のドキュメントを作成
        original_doc = {
            "title": "更新前",
            "body": "古いコンテンツ",
            "tag": "old"
        }
        es_client.index(index=index, id=300, document=original_doc)
        es_client.indices.refresh(index=index)
        
        # PUTで更新
        updated_doc = {
            "title": "更新後",
            "body": "新しいコンテンツ",
            "tag": "new"
        }
        result = es_client.index(index=index, id=300, document=updated_doc)
        
        assert result["result"] == "updated"
        
        # リフレッシュ
        es_client.indices.refresh(index=index)
        
        # 更新されたことを確認
        retrieved = es_client.get(index=index, id=300)
        assert retrieved["_source"]["title"] == "更新後"
        assert retrieved["_source"]["body"] == "新しいコンテンツ"
        assert retrieved["_source"]["tag"] == "new"

    def test_put_create_new_document(self, es_client):
        """PUT: 存在しないIDで新規作成(upsert)"""
        # インデックスをクリーンアップ
        es_client.indices.delete(index=index, ignore=[status.HTTP_404_NOT_FOUND])
        es_client.indices.create(index=index)
        
        # 存在しないIDに対してPUT
        new_doc = {
            "title": "PUT新規",
            "body": "upsert動作",
            "tag": "put-upsert"
        }
        result = es_client.index(index=index, id=400, document=new_doc)
        
        assert result["result"] == "created"
        
        # リフレッシュ
        es_client.indices.refresh(index=index)
        
        # ドキュメントが作成されたことを確認
        retrieved = es_client.get(index=index, id=400)
        assert retrieved["_source"]["title"] == "PUT新規"

    def test_put_partial_update(self, es_client):
        """PUT(update API): 部分更新"""
        # インデックスをクリーンアップ
        es_client.indices.delete(index=index, ignore=[status.HTTP_404_NOT_FOUND])
        es_client.indices.create(index=index)
        
        # 元のドキュメントを作成
        original_doc = {
            "title": "部分更新前",
            "body": "元の本文",
            "tag": "original"
        }
        es_client.index(index=index, id=500, document=original_doc)
        es_client.indices.refresh(index=index)
        
        # update APIで部分更新(titleのみ変更)
        es_client.update(
            index=index,
            id=500,
            body={"doc": {"title": "部分更新後"}}
        )
        
        # リフレッシュ
        es_client.indices.refresh(index=index)
        
        # 更新を確認
        retrieved = es_client.get(index=index, id=500)
        assert retrieved["_source"]["title"] == "部分更新後"
        assert retrieved["_source"]["body"] == "元の本文"  # 変更されていない
        assert retrieved["_source"]["tag"] == "original"  # 変更されていない

    def test_put_with_version_conflict(self, es_client):
        """PUT: バージョン競合のテスト"""
        # インデックスをクリーンアップ
        es_client.indices.delete(index=index, ignore=[status.HTTP_404_NOT_FOUND])
        es_client.indices.create(index=index)
        
        # ドキュメントを作成
        doc = {"title": "バージョンテスト", "body": "初期", "tag": "v1"}
        result = es_client.index(index=index, id=600, document=doc)
        seq_no = result["_seq_no"]
        primary_term = result["_primary_term"]
        
        # 正しいバージョンで更新
        updated_doc = {"title": "更新1", "body": "正常更新", "tag": "v2"}
        es_client.index(
            index=index,
            id=600,
            document=updated_doc,
            if_seq_no=seq_no,
            if_primary_term=primary_term
        )
        
        # 古いバージョン情報で更新を試みる(競合エラー)
        updated_doc2 = {"title": "更新2", "body": "失敗するはず", "tag": "v3"}
        
        from elasticsearch import ConflictError
        with pytest.raises(ConflictError):
            es_client.index(
                index=index,
                id=600,
                document=updated_doc2,
                if_seq_no=seq_no,
                if_primary_term=primary_term
            )

    def test_delete_existing_document(self, es_client):
        """DELETE: 既存ドキュメントを削除"""
        # インデックスをクリーンアップ
        es_client.indices.delete(index=index, ignore=[status.HTTP_404_NOT_FOUND])
        es_client.indices.create(index=index)
        
        # ドキュメントを作成
        doc = {"title": "削除対象", "body": "このドキュメントは削除される", "tag": "delete-test"}
        es_client.index(index=index, id=700, document=doc)
        es_client.indices.refresh(index=index)
        
        # ドキュメントが存在することを確認
        assert es_client.exists(index=index, id=700)
        
        # ドキュメントを削除
        result = es_client.delete(index=index, id=700)
        
        assert result["result"] == "deleted"
        
        # リフレッシュ
        es_client.indices.refresh(index=index)
        
        # ドキュメントが削除されたことを確認
        assert not es_client.exists(index=index, id=700)

    def test_delete_nonexistent_document(self, es_client):
        """DELETE: 存在しないドキュメントの削除を試みる"""
        # インデックスをクリーンアップ
        es_client.indices.delete(index=index, ignore=[status.HTTP_404_NOT_FOUND])
        es_client.indices.create(index=index)
        
        # 存在しないIDを削除しようとする
        from elasticsearch import NotFoundError
        with pytest.raises(NotFoundError):
            es_client.delete(index=index, id=999)

    def test_delete_by_query(self, es_client):
        """DELETE: クエリによる複数ドキュメントの削除"""
        # インデックスをクリーンアップ
        es_client.indices.delete(index=index, ignore=[status.HTTP_404_NOT_FOUND])
        es_client.indices.create(index=index)
        
        # 複数のドキュメントを作成
        test_docs = [
            {"title": "削除1", "body": "削除対象", "tag": "to-delete"},
            {"title": "削除2", "body": "削除対象", "tag": "to-delete"},
            {"title": "保持", "body": "残すべき", "tag": "keep"},
        ]
        
        for i, doc in enumerate(test_docs, start=800):
            es_client.index(index=index, id=i, document=doc)
        
        es_client.indices.refresh(index=index)
        
        # 削除前のドキュメント数を確認
        result = es_client.search(index=index, body={"query": {"match_all": {}}})
        assert result["hits"]["total"]["value"] == 3
        
        # tagが"to-delete"のドキュメントを削除
        delete_result = es_client.delete_by_query(
            index=index,
            body={"query": {"match": {"tag": "to-delete"}}}
        )
        
        assert delete_result["deleted"] == 2
        
        # リフレッシュ
        es_client.indices.refresh(index=index)
        
        # 削除後のドキュメント数を確認
        result = es_client.search(index=index, body={"query": {"match_all": {}}})
        assert result["hits"]["total"]["value"] == 1
        
        # 残ったドキュメントを確認
        remaining = result["hits"]["hits"][0]["_source"]
        assert remaining["tag"] == "keep"

    def test_delete_and_recreate_same_id(self, es_client):
        """DELETE: 削除後に同じIDで再作成"""
        # インデックスをクリーンアップ
        es_client.indices.delete(index=index, ignore=[status.HTTP_404_NOT_FOUND])
        es_client.indices.create(index=index)
        
        # ドキュメントを作成
        doc1 = {"title": "最初", "body": "初回作成", "tag": "v1"}
        result1 = es_client.index(index=index, id=900, document=doc1)
        version1 = result1["_version"]
        
        es_client.indices.refresh(index=index)
        
        # ドキュメントを削除
        es_client.delete(index=index, id=900)
        es_client.indices.refresh(index=index)
        
        # 同じIDで再作成
        doc2 = {"title": "2回目", "body": "再作成", "tag": "v2"}
        result2 = es_client.index(index=index, id=900, document=doc2)
        version2 = result2["_version"]
        
        # バージョンが増加していることを確認
        assert version2 > version1
        
        es_client.indices.refresh(index=index)
        
        # 新しいドキュメントが作成されたことを確認
        retrieved = es_client.get(index=index, id=900)
        assert retrieved["_source"]["title"] == "2回目"
        assert retrieved["_source"]["body"] == "再作成"
        assert retrieved["_source"]["tag"] == "v2"

    def test_delete_with_refresh(self, es_client):
        """DELETE: refresh指定による即座の反映"""
        # インデックスをクリーンアップ
        es_client.indices.delete(index=index, ignore=[status.HTTP_404_NOT_FOUND])
        es_client.indices.create(index=index)
        
        # ドキュメントを作成
        doc = {"title": "即座削除", "body": "refresh=trueでテスト", "tag": "refresh-test"}
        es_client.index(index=index, id=1000, document=doc, refresh=True)
        
        # 削除(refresh=trueで即座に反映)
        result = es_client.delete(index=index, id=1000, refresh=True)
        
        assert result["result"] == "deleted"
        
        # リフレッシュなしで即座に確認可能
        assert not es_client.exists(index=index, id=1000)

    def test_bulk_delete(self, es_client):
        """DELETE: バルク操作による複数削除"""
        # インデックスをクリーンアップ
        es_client.indices.delete(index=index, ignore=[status.HTTP_404_NOT_FOUND])
        es_client.indices.create(index=index)
        
        # 複数のドキュメントを作成
        for i in range(1100, 1105):
            doc = {"title": f"Doc{i}", "body": "バルク削除テスト", "tag": "bulk"}
            es_client.index(index=index, id=i, document=doc)
        
        es_client.indices.refresh(index=index)
        
        # バルク削除
        bulk_body = []
        for i in range(1100, 1103):  # 3つ削除
            bulk_body.append({"delete": {"_index": index, "_id": i}})
        
        result = es_client.bulk(body=bulk_body)
        assert not result["errors"]
        
        es_client.indices.refresh(index=index)
        
        # 削除されたことを確認
        for i in range(1100, 1103):
            assert not es_client.exists(index=index, id=i)
        
        # 残っているドキュメントを確認
        for i in range(1103, 1105):
            assert es_client.exists(index=index, id=i)