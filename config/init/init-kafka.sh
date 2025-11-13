#!/bin/sh

echo "⏳ Waiting for Kafka to be ready..."

# Активное ожидание готовности Kafka
until kafka-broker-api-versions --bootstrap-server kafka:9093 >/dev/null 2>&1; do
  echo "Kafka not ready yet... sleeping 5s"
  sleep 5
done

echo "✅ Kafka is ready."


echo "🔑 Creating admin SCRAM user..."
kafka-configs --bootstrap-server kafka:9093 \
  --alter --add-config "SCRAM-SHA-256=[password=${KAFKA_ADMIN_PASSWORD}]" \
  --entity-type users --entity-name admin
echo "✅ Kafka SCRAM user 'admin' created successfully."

echo "👁 Creating topic ..."
kafka-topics --bootstrap-server kafka:9093 --create --topic create_user_in --partitions 1 --replication-factor 1 --if-not-exists;
kafka-topics --bootstrap-server kafka:9093 --create --topic update_user_in --partitions 1 --replication-factor 1 --if-not-exists;
#kafka kafka-topics --bootstrap-server kafka:9093 --create --topic task_in --partitions 1 --replication-factor 1 --if-not-exists; # если 1 worker
kafka-topics --bootstrap-server kafka:9093 --create --topic task_in --partitions 2 --replication-factor 1 --if-not-exists; # если 2 worker
kafka-topics --bootstrap-server kafka:9093 --create --topic info_in --partitions 1 --replication-factor 1 --if-not-exists;
echo "✅ Kafka topics created successfully."
