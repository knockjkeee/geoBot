## 🚀 Quick Reference - bash команды

## 📦 Запуск и остановка

```bash
# Запуск всей системы
docker-compose up -d --build

# Быстрая перезборка контейнера
docker compose up --build --force-recreate -d

# Остановка
docker-compose down

# Остановка с удалением данных
docker-compose down -v

# Перезапуск конкретного сервиса
docker-compose restart kafka

# Пересборка и перезапуск
docker-compose up -d --build kafka
```

## 📊 Мониторинг

```bash
# Статус всех контейнеров
docker-compose ps

# Логи всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f kafka
docker-compose logs -f nginx

# Последние 100 строк
docker-compose logs --tail=100 kafka

# Использование ресурсов
docker stats
```

## 🔒 Kafka Security

```bash
# === ПОЛЬЗОВАТЕЛИ ===

# Создать пользователя
docker exec -it kafka kafka-configs \
  --bootstrap-server kafka:9093 \
  --alter \
  --add-config 'SCRAM-SHA-256=[password=PASSWORD]' \
  --entity-type users \
  --entity-name USERNAME

# Список пользователей
docker exec -it kafka kafka-configs \
  --bootstrap-server kafka:9093 \
  --describe \
  --entity-type users

# Удалить пользователя
docker exec -it kafka kafka-configs \
  --bootstrap-server kafka:9093 \
  --alter \
  --delete-config 'SCRAM-SHA-256' \
  --entity-type users \
  --entity-name USERNAME

# === ACL ===

# Добавить WRITE права
docker exec -it kafka kafka-acls \
  --bootstrap-server kafka:9093 \
  --add \
  --allow-principal User:USERNAME \
  --operation WRITE \
  --topic TOPIC_NAME

# Добавить READ права
docker exec -it kafka kafka-acls \
  --bootstrap-server kafka:9093 \
  --add \
  --allow-principal User:USERNAME \
  --operation READ \
  --topic TOPIC_NAME

# Права на consumer group
docker exec -it kafka kafka-acls \
  --bootstrap-server kafka:9093 \
  --add \
  --allow-principal User:USERNAME \
  --operation READ \
  --group GROUP_NAME

# Список всех ACL
docker exec -it kafka kafka-acls \
  --bootstrap-server kafka:9093 \
  --list

# ACL для топика
docker exec -it kafka kafka-acls \
  --bootstrap-server kafka:9093 \
  --list \
  --topic TOPIC_NAME

# Удалить ACL
docker exec -it kafka kafka-acls \
  --bootstrap-server kafka:9093 \
  --remove \
  --allow-principal User:USERNAME \
  --operation WRITE \
  --topic TOPIC_NAME
```

## 📨 Kafka Topics

```bash
# Список топиков
docker exec -it kafka kafka-topics \
  --list \
  --bootstrap-server localhost:9093

# Описание топика
docker exec -it kafka kafka-topics \
  --describe \
  --topic TOPIC_NAME \
  --bootstrap-server localhost:9093

# Создать топик
docker exec -it kafka kafka-topics \
  --create \
  --topic NEW_TOPIC \
  --partitions 3 \
  --replication-factor 1 \
  --bootstrap-server localhost:9093

# Удалить топик
docker exec -it kafka kafka-topics \
  --delete \
  --topic TOPIC_NAME \
  --bootstrap-server localhost:9093

# Читать сообщения (без auth)
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9093 \
  --topic info.in \
  --from-beginning \
  --max-messages 10

# Отправить сообщение (без auth)
docker exec -it kafka kafka-console-producer \
  --bootstrap-server localhost:9093 \
  --topic test.in
```

## 🌐 NGINX

```bash
# Проверка конфигурации
docker exec -it nginx nginx -t

# Перезагрузка конфигурации (без downtime)
docker exec -it nginx nginx -s reload

# Просмотр логов
docker exec -it nginx tail -f /var/log/nginx/access.log
docker exec -it nginx tail -f /var/log/nginx/error.log

# Статистика (через volume)
docker exec -it nginx cat /var/log/nginx/access.log | \
  awk '{print $1}' | sort | uniq -c | sort -rn | head -10
```

## 🔍 Elasticsearch

```bash
# Статус кластера
curl http://localhost:9200/_cluster/health?pretty

# Список индексов
curl http://localhost:9200/_cat/indices?v

# Поиск в индексе
curl http://localhost:9200/kafka-messages-*/_search?pretty&size=5

# Количество документов
curl http://localhost:9200/_cat/count/kafka-messages-*?v

# Удалить индекс
curl -X DELETE http://localhost:9200/INDEX_NAME

# Удалить все индексы (ОСТОРОЖНО!)
curl -X DELETE http://localhost:9200/*

# Статистика нод
curl http://localhost:9200/_cat/nodes?v

# Задачи в процессе
curl http://localhost:9200/_cat/tasks?v
```

## 📈 Prometheus

```bash
# Статус targets
curl http://localhost:9090/api/v1/targets | jq .

# Проверка конфигурации
docker exec -it prometheus \
  promtool check config /etc/prometheus/prometheus.yml

# Перезагрузка конфигурации
curl -X POST http://localhost:9090/-/reload

# Выполнить запрос
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=up' | jq .

# Range query
curl -G http://localhost:9090/api/v1/query_range \
  --data-urlencode 'query=rate(flask_http_request_total[5m])' \
  --data-urlencode 'start=2024-01-01T00:00:00Z' \
  --data-urlencode 'end=2024-01-01T01:00:00Z' \
  --data-urlencode 'step=15s' | jq .
```

## 🧪 Тестирование API

```bash
# === FLASK ENDPOINTS (через NGINX) ===

# Create User
curl http://localhost/flask_create_user

# Update User
curl -X POST http://localhost/flask_update_user

# Info
curl http://localhost/flask_info

# Start Task
curl http://localhost/flask_start_task

# Health Check
curl http://localhost/health

# Метрики Prometheus
curl http://localhost/metrics

# === НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ ===

# 100 последовательных запросов
for i in {1..100}; do
  curl -s http://localhost/flask_create_user
done

# 50 параллельных запросов
for i in {1..50}; do
  curl -s http://localhost/flask_info &
done
wait

# С использованием Apache Bench
ab -n 1000 -c 10 http://localhost/flask_create_user

# С использованием wrk
wrk -t4 -c100 -d30s http://localhost/flask_create_user
```

## 🗄️ Docker Volumes

```bash
# Список volumes
docker volume ls

# Информация о volume
docker volume inspect kafka-elk-project_kafka-data

# Размер volume
docker system df -v

# Очистка неиспользуемых volumes
docker volume prune

# Backup volume
docker run --rm \
  -v kafka-elk-project_kafka-data:/data \
  -v $(pwd):/backup \
  busybox tar czf /backup/kafka-data-backup.tar.gz /data

# Restore volume
docker run --rm \
  -v kafka-elk-project_kafka-data:/data \
  -v $(pwd):/backup \
  busybox tar xzf /backup/kafka-data-backup.tar.gz -C /
```

## 🔧 Debugging

```bash
# Войти в контейнер
docker exec -it kafka /bin/bash
docker exec -it flask-producer-1 /bin/sh

# Сетевая диагностика
docker exec -it flask-producer-1 ping kafka
docker exec -it flask-producer-1 nc -zv kafka 9092

# Просмотр переменных окружения
docker exec -it flask-producer-1 env

# Проверка процессов
docker exec -it kafka ps aux

# Использование диска
docker exec -it elasticsearch df -h

# Проверка портов
docker exec -it nginx netstat -tlnp

# Inspect контейнера
docker inspect flask-producer-1 | jq .
```

## 📊 Полезные PromQL запросы

```promql
# HTTP RPS
rate(flask_http_request_total[5m])

# Ошибки %
rate(flask_http_request_exceptions_total[5m]) / rate(flask_http_request_total[5m]) * 100

# 95th percentile latency
histogram_quantile(0.95, rate(flask_http_request_duration_seconds_bucket[5m]))

# Kafka messages/sec
rate(kafka_server_brokertopicmetrics_messagesin_total[5m])

# NGINX connections
nginx_connections_active

# Container memory
container_memory_usage_bytes{name="flask-producer-1"}

# CPU usage
rate(container_cpu_usage_seconds_total{name="kafka"}[5m]) * 100

# Disk usage
(node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100
```

## 🚨 Alerting (примеры правил)

```yaml
# prometheus/alerts/rules.yml
groups:
  - name: kafka
    rules:
      - alert: KafkaDown
        expr: up{job="kafka"} == 0
        for: 1m
        annotations:
          summary: "Kafka is down"

      - alert: HighConsumerLag
        expr: kafka_consumer_lag > 1000
        for: 5m
        annotations:
          summary: "High consumer lag"

  - name: flask
    rules:
      - alert: HighErrorRate
        expr: rate(flask_http_request_exceptions_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate in Flask"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(flask_http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        annotations:
          summary: "High latency in Flask"
```

## 🔄 Полезные однострочники

```bash
# Количество сообщений в топике
docker exec -it kafka kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list localhost:9093 \
  --topic info.in | awk -F ":" '{sum += $3} END {print sum}'

# Top 10 IP по запросам в NGINX
docker exec -it nginx cat /var/log/nginx/access.log | \
  awk '{print $1}' | sort | uniq -c | sort -rn | head -10

# Средний размер сообщений в Kafka
docker exec -it kafka kafka-log-dirs \
  --bootstrap-server localhost:9093 \
  --describe | grep size

# Распределение HTTP статус кодов
docker exec -it nginx cat /var/log/nginx/access.log | \
  awk '{print $9}' | sort | uniq -c | sort -rn
```