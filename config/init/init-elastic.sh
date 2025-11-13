#!/bin/sh

echo "⏳ Waiting for Elasticsearch to be ready..."

until curl -s -f -u "$ELASTIC_USER:$ELASTIC_PASSWORD" http://elasticsearch:9200/_cluster/health > /dev/null; do
  echo "Elasticsearch not ready yet... sleeping"
  sleep 5
done

echo "Creating users and roles in Elasticsearch..."

curl -X PUT "http://elasticsearch:9200/_cluster/settings" \
-u "$ELASTIC_USER:$ELASTIC_PASSWORD" \
-H 'Content-Type: application/json' \
-d '{
  "persistent": {
    "cluster.routing.allocation.disk.watermark.low": "95%",
    "cluster.routing.allocation.disk.watermark.high": "99%",
    "cluster.routing.allocation.disk.watermark.flood_stage": "99%",
    "cluster.info.update.interval": "1m"
  }
}'

curl -X POST "http://elasticsearch:9200/_security/user/logstash_writer" \
  -u "$ELASTIC_USER:$ELASTIC_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "'"$ELASTICSEARCH_PASSWORD_LOGSTASH"'",
    "roles": ["superuser"],
    "full_name": "Logstash Writer",
    "email": "logstash@example.com"
}'

curl -X POST "http://elasticsearch:9200/_security/user/kibana_system/_password" \
-u "$ELASTIC_USER:$ELASTIC_PASSWORD" \
-H "Content-Type: application/json" \
-d '{
  "password": "'"$ELASTICSEARCH_PASSWORD_KIBANA"'"
}'

curl -X POST "http://elasticsearch:9200/_security/user/reader_user" \
-u "$ELASTIC_USER:$ELASTIC_PASSWORD" \
-H "Content-Type: application/json" \
-d '{
  "password": "'"$ELASTICSEARCH_PASSWORD_READER"'",
  "roles": ["kibana_user", "monitoring_user"],
  "full_name": "Read Only User"
}'

curl -X POST "http://elasticsearch:9200/_security/user/developer" \
-u "$ELASTIC_USER:$ELASTIC_PASSWORD" \
-H "Content-Type: application/json" \
-d '{
  "password": "'"$ELASTICSEARCH_PASSWORD_DEV"'",
  "roles": ["superuser"],
  "full_name": "Developer User"
}'

curl -X POST "http://elasticsearch:9200/_security/role/logstash_writer_role" \
-u "$ELASTIC_USER:$ELASTIC_PASSWORD" \
-H "Content-Type: application/json" \
-d '{
  "cluster": ["monitor", "manage_index_templates"],
  "indices": [
    {
      "names": ["*-*"],
      "privileges": ["create_index", "write", "delete", "create"]
    }
  ]
}'
echo ""
echo "✅ Initialization elastic complete."