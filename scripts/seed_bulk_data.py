import argparse
import json
import os
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
KIBANA_HOST = os.getenv("KIBANA_HOST", "http://localhost:5601")

COMMERCE_INDEX_PREFIX = "shoplane-prod-commerce-events"
USER_PROFILE_INDEX_PREFIX = "shoplane-prod-user-profile"
APP_LOG_INDEX_PREFIX = "shoplane-prod-app-logs"

COMMERCE_DATA_VIEW_NAME = "Shoplane Commerce Events"
USER_PROFILE_DATA_VIEW_NAME = "Shoplane User Profiles"
APP_LOG_DATA_VIEW_NAME = "Shoplane App Logs"
TRIGGER_DATA_VIEW_NAMES = {
    "cart_in": "Shoplane Cart In Events",
    "purchase": "Shoplane Purchase Events",
    "search": "Shoplane Search Events",
}

DEFAULT_INDEX_COUNT = 5
DEFAULT_DOCS_PER_INDEX = 100
DEFAULT_USER_PROFILE_COUNT = 120
DEFAULT_APP_LOG_COUNT = 180

COMMERCE_SERVICES = ["web-store", "orders-api", "payments-api", "warehouse-api"]
EVENT_TYPES = ["cart_in", "purchase", "search"]
TAGS = ["cart", "checkout", "payment", "shipment", "promotion"]
CATEGORIES = ["order", "payment", "customer", "fulfillment"]
LOCATIONS = ["jp-east", "jp-west", "jp-central"]
LEVELS = ["INFO", "INFO", "INFO", "INFO", "WARN", "ERROR"]
ENVIRONMENTS = ["prod", "prod", "prod", "stg"]

COMMERCE_INDEX_MAPPINGS = {
    "properties": {
        "title": {
            "type": "text",
            "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
        },
        "body": {"type": "text"},
        "message": {"type": "text"},
        "tag": {"type": "keyword"},
        "category": {"type": "keyword"},
        "level": {"type": "keyword"},
        "service": {"type": "keyword"},
        "env": {"type": "keyword"},
        "location": {"type": "keyword"},
        "event_type": {"type": "keyword"},
        "host": {"type": "keyword"},
        "trace_id": {"type": "keyword"},
        "endpoint": {"type": "keyword"},
        "http_method": {"type": "keyword"},
        "status_code": {"type": "integer"},
        "response_time_ms": {"type": "integer"},
        "user_id": {"type": "keyword"},
        "order_id": {"type": "keyword"},
        "payment_method": {"type": "keyword"},
        "customer_tier": {"type": "keyword"},
        "item_count": {"type": "integer"},
        "cart_value_jpy": {"type": "integer"},
        "doc_number": {"type": "integer"},
        "@timestamp": {"type": "date"},
    }
}

USER_PROFILE_MAPPINGS = {
    "properties": {
        "user_id": {"type": "keyword"},
        "email": {"type": "keyword"},
        "age": {"type": "integer"},
        "region": {"type": "keyword"},
        "customer_tier": {"type": "keyword"},
        "favorite_category": {"type": "keyword"},
        "last_login_at": {"type": "date"},
        "signup_at": {"type": "date"},
        "lifetime_value_jpy": {"type": "integer"},
        "is_active": {"type": "boolean"},
        "@timestamp": {"type": "date"},
    }
}

APP_LOG_MAPPINGS = {
    "properties": {
        "service": {"type": "keyword"},
        "level": {"type": "keyword"},
        "message": {"type": "text"},
        "error_code": {"type": "keyword"},
        "trace_id": {"type": "keyword"},
        "endpoint": {"type": "keyword"},
        "status_code": {"type": "integer"},
        "latency_ms": {"type": "integer"},
        "host": {"type": "keyword"},
        "env": {"type": "keyword"},
        "@timestamp": {"type": "date"},
    }
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed ecommerce event, user profile, and app log datasets."
    )
    parser.add_argument("--index-prefix", default=COMMERCE_INDEX_PREFIX)
    parser.add_argument("--data-view-name", default=COMMERCE_DATA_VIEW_NAME)
    parser.add_argument("--index-count", type=int, default=DEFAULT_INDEX_COUNT)
    parser.add_argument("--docs-per-index", type=int, default=DEFAULT_DOCS_PER_INDEX)
    parser.add_argument("--user-profile-count", type=int, default=DEFAULT_USER_PROFILE_COUNT)
    parser.add_argument("--app-log-count", type=int, default=DEFAULT_APP_LOG_COUNT)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--skip-data-view", action="store_true")
    return parser.parse_args()


def build_commerce_actions(
    index_name: str, docs_per_index: int, index_no: int
) -> Iterable[dict]:
    now = datetime.now(UTC)
    service = COMMERCE_SERVICES[(index_no - 1) % len(COMMERCE_SERVICES)]
    location = LOCATIONS[(index_no - 1) % len(LOCATIONS)]

    for doc_id in range(1, docs_per_index + 1):
        tag = TAGS[(doc_id - 1) % len(TAGS)]
        category = CATEGORIES[(doc_id - 1) % len(CATEGORIES)]
        event_type = EVENT_TYPES[(doc_id - 1) % len(EVENT_TYPES)]
        level = LEVELS[(doc_id - 1) % len(LEVELS)]
        endpoint = ["/cart", "/purchase", "/search", "/wishlist"][(doc_id - 1) % 4]
        method = ["GET", "POST", "PUT", "DELETE"][(doc_id - 1) % 4]
        environment = ENVIRONMENTS[(index_no - 1) % len(ENVIRONMENTS)]
        status_code = 500 if level == "ERROR" else 429 if level == "WARN" else 200
        response_time_ms = 900 if level == "ERROR" else 320 if level == "WARN" else 140
        trace_id = f"trace-{index_no:02d}-{doc_id:05d}"
        user_id = f"user-{((doc_id - 1) % 120) + 1:04d}"

        yield {
            "_index": index_name,
            "_id": str(doc_id),
            "_source": {
                "title": f"ecommerce {service} event #{doc_id}",
                "body": f"Practice event for {service} in {location}.",
                "message": (
                    f"{service} handled {event_type} via {method} {endpoint} "
                    f"status={status_code} latency={response_time_ms}ms"
                ),
                "tag": tag,
                "category": category,
                "level": level,
                "service": service,
                "env": environment,
                "location": location,
                "event_type": event_type,
                "host": f"{service}-{(doc_id % 3) + 1}",
                "trace_id": trace_id,
                "endpoint": endpoint,
                "http_method": method,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
                "user_id": user_id,
                "order_id": f"ORD-{index_no:02d}-{doc_id:05d}",
                "payment_method": ["card", "konbini", "wallet", "bank-transfer"][
                    (doc_id - 1) % 4
                ],
                "customer_tier": ["bronze", "silver", "gold", "platinum"][
                    (doc_id - 1) % 4
                ],
                "item_count": ((doc_id - 1) % 7) + 1,
                "cart_value_jpy": 1200 + ((doc_id - 1) % 15) * 800,
                "doc_number": doc_id,
                "@timestamp": (now - timedelta(minutes=doc_id)).isoformat(),
            },
        }


def build_user_profile_actions(index_name: str, user_profile_count: int) -> Iterable[dict]:
    now = datetime.now(UTC)
    for i in range(1, user_profile_count + 1):
        yield {
            "_index": index_name,
            "_id": f"user-{i:04d}",
            "_source": {
                "user_id": f"user-{i:04d}",
                "email": f"user{i:04d}@example.com",
                "age": 18 + (i % 45),
                "region": ["tokyo", "osaka", "nagoya", "fukuoka"][i % 4],
                "customer_tier": ["bronze", "silver", "gold", "platinum"][i % 4],
                "favorite_category": ["electronics", "fashion", "food", "books"][i % 4],
                "last_login_at": (now - timedelta(hours=i % 72)).isoformat(),
                "signup_at": (now - timedelta(days=30 + i)).isoformat(),
                "lifetime_value_jpy": 5000 + (i % 80) * 2500,
                "is_active": i % 7 != 0,
                "@timestamp": now.isoformat(),
            },
        }


def build_app_log_actions(index_name: str, app_log_count: int) -> Iterable[dict]:
    now = datetime.now(UTC)
    services = ["frontend", "checkout-api", "search-api", "notification-worker"]
    for i in range(1, app_log_count + 1):
        level = LEVELS[(i - 1) % len(LEVELS)]
        status_code = 500 if level == "ERROR" else 429 if level == "WARN" else 200
        yield {
            "_index": index_name,
            "_id": f"log-{i:05d}",
            "_source": {
                "service": services[(i - 1) % len(services)],
                "level": level,
                "message": f"Application log sample #{i} level={level}",
                "error_code": "E_TIMEOUT" if level == "ERROR" else "NONE",
                "trace_id": f"app-trace-{i:05d}",
                "endpoint": ["/health", "/checkout", "/search", "/notify"][(i - 1) % 4],
                "status_code": status_code,
                "latency_ms": 980 if level == "ERROR" else 340 if level == "WARN" else 90,
                "host": f"app-node-{(i % 4) + 1}",
                "env": "prod",
                "@timestamp": (now - timedelta(minutes=i)).isoformat(),
            },
        }


def validate_args(args: argparse.Namespace) -> None:
    if args.index_count <= 0 or args.docs_per_index <= 0:
        raise ValueError("--index-count and --docs-per-index must be greater than 0.")
    if args.user_profile_count <= 0 or args.app_log_count <= 0:
        raise ValueError("--user-profile-count and --app-log-count must be greater than 0.")


def create_data_view(data_view_name: str, index_pattern: str) -> None:
    endpoint = f"{KIBANA_HOST}/api/data_views/data_view"
    payload = {
        "data_view": {
            "name": data_view_name,
            "title": index_pattern,
            "timeFieldName": "@timestamp",
        }
    }
    request = Request(
        f"{endpoint}?override=true",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "kbn-xsrf": "true"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10):
            print(f"Created/updated Data view: {data_view_name} ({index_pattern})")
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        if error.code == 400 and "Duplicate data view" in body:
            print(f"Data view already exists: {data_view_name} ({index_pattern})")
            return
        raise RuntimeError(f"Failed to create Data view: {error.code} {body}") from error
    except URLError as error:
        raise RuntimeError(f"Kibana is not reachable: {KIBANA_HOST}") from error


def recreate_alias(es: Elasticsearch, alias_name: str, index_pattern: str, event_type: str) -> None:
    matched_indices = list(es.indices.get(index=index_pattern).keys())
    try:
        es.indices.delete_alias(index="*", name=alias_name, ignore_unavailable=True)
    except Exception:
        pass

    actions = []
    for index_name in matched_indices:
        actions.append(
            {
                "add": {
                    "index": index_name,
                    "alias": alias_name,
                    "filter": {"term": {"event_type": event_type}},
                }
            }
        )
    es.indices.update_aliases(actions=actions)
    print(f"Created alias {alias_name} for event_type={event_type}")


def ensure_index(es: Elasticsearch, index_name: str, mappings: dict, reset: bool) -> None:
    if reset and es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, mappings=mappings)


def main() -> None:
    args = parse_args()
    validate_args(args)

    es = Elasticsearch(ES_HOST)
    if not es.ping():
        raise RuntimeError(f"Elasticsearch is not reachable: {ES_HOST}")

    total_docs = 0
    commerce_pattern = f"{args.index_prefix}-*"
    for i in range(1, args.index_count + 1):
        commerce_index = f"{args.index_prefix}-{i:02d}"
        ensure_index(es, commerce_index, COMMERCE_INDEX_MAPPINGS, args.reset)
        bulk(es, build_commerce_actions(commerce_index, args.docs_per_index, i), refresh="wait_for")
        count = es.count(index=commerce_index)["count"]
        total_docs += count
        print(f"Seeded {commerce_index}: {count} docs")

    user_profile_index = f"{USER_PROFILE_INDEX_PREFIX}-01"
    ensure_index(es, user_profile_index, USER_PROFILE_MAPPINGS, args.reset)
    bulk(es, build_user_profile_actions(user_profile_index, args.user_profile_count), refresh="wait_for")
    user_count = es.count(index=user_profile_index)["count"]
    total_docs += user_count
    print(f"Seeded {user_profile_index}: {user_count} docs")

    app_log_index = f"{APP_LOG_INDEX_PREFIX}-01"
    ensure_index(es, app_log_index, APP_LOG_MAPPINGS, args.reset)
    bulk(es, build_app_log_actions(app_log_index, args.app_log_count), refresh="wait_for")
    log_count = es.count(index=app_log_index)["count"]
    total_docs += log_count
    print(f"Seeded {app_log_index}: {log_count} docs")

    recreate_alias(es, "shoplane-commerce-cart-in", commerce_pattern, "cart_in")
    recreate_alias(es, "shoplane-commerce-purchase", commerce_pattern, "purchase")
    recreate_alias(es, "shoplane-commerce-search", commerce_pattern, "search")

    print(f"Completed: total {total_docs} docs (ES host: {ES_HOST})")

    if not args.skip_data_view:
        create_data_view(args.data_view_name, commerce_pattern)
        create_data_view(USER_PROFILE_DATA_VIEW_NAME, f"{USER_PROFILE_INDEX_PREFIX}-*")
        create_data_view(APP_LOG_DATA_VIEW_NAME, f"{APP_LOG_INDEX_PREFIX}-*")
        create_data_view(TRIGGER_DATA_VIEW_NAMES["cart_in"], "shoplane-commerce-cart-in")
        create_data_view(TRIGGER_DATA_VIEW_NAMES["purchase"], "shoplane-commerce-purchase")
        create_data_view(TRIGGER_DATA_VIEW_NAMES["search"], "shoplane-commerce-search")


if __name__ == "__main__":
    main()
