from kafka import KafkaConsumer, KafkaProducer, TopicPartition
import json
import logging
import os
from datetime import datetime
from prometheus_client import start_http_server, Counter, Histogram, Gauge
import time

TASKS_PROCESSED = Counter('task_processor_tasks_processed_total', 'Total tasks processed')
PROCESSING_TIME = Histogram('task_processor_processing_seconds', 'Processing time')
ACTIVE_TASKS = Gauge('task_processor_active_tasks', 'Active tasks')


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'task-processor',
            'level': record.levelname,
            'message': record.getMessage()
        })


logger = logging.getLogger('task_processor')
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(JsonFormatter())
logger.addHandler(console_handler)

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_SASL_USERNAME = os.getenv('KAFKA_SASL_USERNAME', 'admin')
KAFKA_SASL_PASSWORD = os.getenv('KAFKA_SASL_PASSWORD', 'admin-secret')
CONSUMER_GROUP = os.getenv('CONSUMER_GROUP', 'task-processor-group')

PARTITION_ID = os.getenv('PARTITION_ID', 0)
SERVICE_NAME = 'WORKER' + f'_{PARTITION_ID}'

CURRENT_PORT = os.getenv('CURRENT_PORT', 8001)

print('==> KAFKA_BOOTSTRAP_SERVERS', KAFKA_BOOTSTRAP_SERVERS)


def create_kafka_consumer():
    topic = 'task_in'
    try:
        if '9093' in KAFKA_BOOTSTRAP_SERVERS:
            consumer = KafkaConsumer(
                # topic, # если 1 топик
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                security_protocol='PLAINTEXT',
                group_id=CONSUMER_GROUP,
                enable_auto_commit=False, #если нужен автокоммит, переводим в True
                auto_offset_reset='earliest'
            )

        else:
            consumer = KafkaConsumer(
                # topic, # если 1 топик
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                security_protocol='SASL_PLAINTEXT',
                sasl_mechanism='SCRAM-SHA-256',
                sasl_plain_username=KAFKA_SASL_USERNAME,
                sasl_plain_password=KAFKA_SASL_PASSWORD,
                group_id=CONSUMER_GROUP,
                enable_auto_commit=False, #если нужен автокоммит, переводим в True
                auto_offset_reset='earliest'
            )

    except Exception as e:
        logger.error(f"Ошибка при создании Kafka Producer: {str(e)}")
        raise

    logger.info("Kafka Consumer успешно инициализирован")

    tp = TopicPartition(topic, int(PARTITION_ID))  # todo удалить если 1 partition
    consumer.assign([tp])  # todo удалить если 1 partition
    return consumer


def create_kafka_producer():

    try:
        if '9093' in KAFKA_BOOTSTRAP_SERVERS:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                security_protocol='PLAINTEXT',
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1,
                request_timeout_ms=30000,
                batch_size=16384,
                linger_ms=10
            )

        else:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                security_protocol='SASL_PLAINTEXT',
                sasl_mechanism='SCRAM-SHA-256',
                sasl_plain_username=KAFKA_SASL_USERNAME,
                sasl_plain_password=KAFKA_SASL_PASSWORD,
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1,
                request_timeout_ms=30000,
                batch_size=16384,
                linger_ms=10
            )

    except Exception as e:
        logger.error(f"Ошибка при создании Kafka Producer: {str(e)}")
        raise

    logger.info("Kafka Producer успешно инициализирован")
    return producer



def process_task(message, producer):
    try:
        ACTIVE_TASKS.inc()
        result = {
            'service': SERVICE_NAME,
            'action': message.get('action'),
            'payload': {
                'message': 'Task completed',
                'timestamp': datetime.utcnow().isoformat(),
                'data': {}
            }
        }

        producer.send('info_in', value=result).get(timeout=10)
        TASKS_PROCESSED.inc()
        return True
    except Exception as e:
        logger.error(f"Task processing error: {str(e)}")
        return False
    finally:
        ACTIVE_TASKS.dec()


def process_messages():
    consumer = create_kafka_consumer()
    producer = create_kafka_producer()
    logger.info("Worker Processor started")

    try:
        for message in consumer:
            start_time = time.time()
            process_task(message.value, producer)
            PROCESSING_TIME.observe(time.time() - start_time)
            consumer.commit()
    finally:
        consumer.close()
        producer.close()


if __name__ == '__main__':
    start_http_server(int(os.getenv('METRICS_PORT', CURRENT_PORT)))
    process_messages()
