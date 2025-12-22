#!/usr/bin/env bash
set -euo pipefail

# scripts/test_logstash_pipeline.sh
# - 起動: elasticsearch + logstash
# - サンプルメッセージを TCP 5055 に送信
# - Logstash のログにメッセージが出力されることを確認

echo "Starting elasticsearch & logstash via docker-compose..."
docker-compose up -d elasticsearch logstash

echo "Waiting for Elasticsearch to be ready (http://localhost:9200)..."
until curl -s http://localhost:9200/ >/dev/null 2>&1; do
  sleep 2
done

echo "Sending sample log to logstash TCP input (localhost:5055)"
echo "2025-12-23T12:34:56.789Z INFO Sample test message from test script" | nc localhost 5055

sleep 3

echo "Checking Logstash logs for the message..."
if docker-compose logs logstash --no-color | grep -q "Sample test message from test script"; then
  echo "OK: message found in Logstash logs"
  exit 0
else
  echo "ERROR: message not found in Logstash logs"
  docker-compose logs logstash --no-color | tail -n 200
  exit 2
fi
