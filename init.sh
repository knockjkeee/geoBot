#!/usr/bin/env bash


## Загружаем переменные из .env
#if [ -f .env ]; then
#  set -a
#  . .env
#  set +a
#else
#  echo "⚠️  Файл .env не найден. Используются переменные из окружения."
#fi


docker compose up --build --force-recreate -d \
--scale lk-producer=0 \
--scale arm-processor=0 \
--scale log-processor=0 \
--scale worker-processor-0=0 \
--scale worker-processor-1=0
echo "✅ Все сервисы из 'docker compose' запущены."


wait_and_remove_service() {
    local SERVICE_NAME=$1

    while true; do

        STATUS=$(docker compose ps | grep $SERVICE_NAME | awk '{print $4}')

        if [ "$STATUS" == "Up" ]; then
            echo "Сервис $SERVICE_NAME запущен, ждем его остановки..."
        elif [ "$STATUS" == "Exited" ] || [ -z "$STATUS" ]; then
            echo "Сервис $SERVICE_NAME остановлен. Удаляю контейнер..."
            docker compose rm -fsv $SERVICE_NAME
            break
        else
            echo "Сервис $SERVICE_NAME находится в состоянии: $STATUS"
        fi
        sleep 5
    done
}


wait_and_remove_service kafka-init
wait_and_remove_service elastic-init

docker compose up -d lk-producer arm-processor log-processor worker-processor-0 worker-processor-1


#docker exec kafka kafka-topics --bootstrap-server localhost:9093 --create --topic create_user.in --partitions 1 --replication-factor 1 --if-not-exists;
#docker exec kafka kafka-topics --bootstrap-server localhost:9093 --create --topic update_user.in --partitions 1 --replication-factor 1 --if-not-exists;
#docker exec kafka kafka-topics --bootstrap-server localhost:9093 --create --topic task.in --partitions 1 --replication-factor 1 --if-not-exists;
#docker exec kafka kafka-topics --bootstrap-server localhost:9093 --create --topic info.in --partitions 1 --replication-factor 1 --if-not-exists;
#
#docker exec kafka kafka-configs --bootstrap-server localhost:9093  --alter --add-config 'SCRAM-SHA-256=[password=admin-secret]' --entity-type users --entity-name admin
#
#docker compose up -d elasticsearch
#
#curl -X PUT "http://localhost:9200/_cluster/settings" \
#-u $ELASTIC_USER:$ELASTIC_PASSWORD \
#-H 'Content-Type: application/json' \
#-d '{
#  "persistent": {
#    "cluster.routing.allocation.disk.watermark.low": "95%",
#    "cluster.routing.allocation.disk.watermark.high": "99%",
#    "cluster.routing.allocation.disk.watermark.flood_stage": "99%",
#    "cluster.info.update.interval": "1m"
#  }
#}'
#
#
#curl -X POST "http://localhost:9200/_security/user/logstash_writer" \
#  -u $ELASTIC_USER:$ELASTIC_PASSWORD \
#  -H "Content-Type: application/json" \
#  -d '{
#    "password": "'$ELASTICSEARCH_PASSWORD_LOGSTASH'",
#    "roles": ["superuser"],
#    "full_name": "Logstash Writer",
#    "email": "logstash@example.com"
#  }'
#
#  curl -X POST "http://localhost:9200/_security/user/kibana_system/_password" \
#  -u $ELASTIC_USER:$ELASTIC_PASSWORD \
#  -H "Content-Type: application/json" \
#  -d '{
#    "password": "'$ELASTICSEARCH_PASSWORD_KIBANA'"
#  }'
#
#
#  curl -X POST "http://localhost:9200/_security/user/reader_user" \
#  -u $ELASTIC_USER:$ELASTIC_PASSWORD \
#  -H "Content-Type: application/json" \
#  -d '{
#    "password": "'$ELASTICSEARCH_PASSWORD_READER'",
#    "roles": ["kibana_user", "monitoring_user"],
#    "full_name": "Read Only User"
#  }'
#
#  curl -X POST "http://localhost:9200/_security/user/developer" \
#  -u $ELASTIC_USER:$ELASTIC_PASSWORD \
#  -H "Content-Type: application/json" \
#  -d '{
#    "password": "'$ELASTICSEARCH_PASSWORD_DEV'",
#    "roles": ["superuser"],
#    "full_name": "Developer User"
#  }'
#
#  curl -X POST "http://localhost:9200/_security/role/logstash_writer_role" \
#  -u $ELASTIC_USER:$ELASTIC_PASSWORD \
#  -H "Content-Type: application/json" \
#  -d '{
#    "cluster": ["monitor", "manage_index_templates"],
#    "indices": [
#      {
#        "names": ["*-*"],
#        "privileges": ["create_index", "write", "delete", "create"]
#      }
#    ]
#  }'