import argparse
import os
from collections.abc import Iterable

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
DEFAULT_INDEX_PREFIX = "sample-index"
DEFAULT_INDEX_COUNT = 5
DEFAULT_DOCS_PER_INDEX = 100

TAGS = ["demo", "tutorial", "guide", "kibana", "elasticsearch"]
CATEGORIES = ["app", "infra", "analytics"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create multiple Elasticsearch indices and seed sample documents."
    )
    parser.add_argument(
        "--index-prefix",
        default=DEFAULT_INDEX_PREFIX,
        help=f"Prefix for index names (default: {DEFAULT_INDEX_PREFIX})",
    )
    parser.add_argument(
        "--index-count",
        type=int,
        default=DEFAULT_INDEX_COUNT,
        help=f"Number of indices to create (default: {DEFAULT_INDEX_COUNT})",
    )
    parser.add_argument(
        "--docs-per-index",
        type=int,
        default=DEFAULT_DOCS_PER_INDEX,
        help=f"Number of documents per index (default: {DEFAULT_DOCS_PER_INDEX})",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing target indices before inserting documents.",
    )
    return parser.parse_args()


def build_actions(index_name: str, docs_per_index: int) -> Iterable[dict]:
    for doc_id in range(1, docs_per_index + 1):
        tag = TAGS[(doc_id - 1) % len(TAGS)]
        category = CATEGORIES[(doc_id - 1) % len(CATEGORIES)]
        yield {
            "_index": index_name,
            "_id": str(doc_id),
            "_source": {
                "title": f"{index_name}-doc-{doc_id}",
                "body": (
                    f"Sample body for {index_name}. "
                    f"This document number is {doc_id}."
                ),
                "tag": tag,
                "category": category,
                "doc_number": doc_id,
            },
        }


def validate_args(index_count: int, docs_per_index: int) -> None:
    if index_count <= 0:
        raise ValueError("--index-count must be greater than 0.")
    if docs_per_index <= 0:
        raise ValueError("--docs-per-index must be greater than 0.")


def main() -> None:
    args = parse_args()
    validate_args(args.index_count, args.docs_per_index)

    es = Elasticsearch(ES_HOST)
    if not es.ping():
        raise RuntimeError(f"Elasticsearch is not reachable: {ES_HOST}")

    total_docs = 0
    for i in range(1, args.index_count + 1):
        index_name = f"{args.index_prefix}-{i}"

        if args.reset and es.indices.exists(index=index_name):
            es.indices.delete(index=index_name)

        if not es.indices.exists(index=index_name):
            es.indices.create(index=index_name)

        actions = build_actions(index_name, args.docs_per_index)
        bulk(es, actions, refresh="wait_for")
        count = es.count(index=index_name)["count"]
        total_docs += count
        print(f"Seeded {index_name}: {count} docs")

    print(
        f"Completed: {args.index_count} indices, total {total_docs} docs "
        f"(ES host: {ES_HOST})"
    )


if __name__ == "__main__":
    main()
