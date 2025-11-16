from kafka import KafkaConsumer
import json
import logging
import os
from datetime import datetime
from prometheus_client import start_http_server, Counter, Histogram
import requests
from requests.auth import HTTPBasicAuth
import random

INFO_MESSAGES_PROCESSED = Counter('info_processor_messages_processed_total', 'Messages processed')
ELK_SEND_TIME = Histogram('info_processor_elk_send_seconds', 'ELK send time')


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'info-processor',
            'level': record.levelname,
            'message': record.getMessage()
        })


logger = logging.getLogger('info_processor')
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(JsonFormatter())
logger.addHandler(console_handler)

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_SASL_USERNAME = os.getenv('KAFKA_SASL_USERNAME', 'admin')
KAFKA_SASL_PASSWORD = os.getenv('KAFKA_SASL_PASSWORD', 'admin-secret')
LOGSTASH_HOST = os.getenv('LOGSTASH_HOST', 'localhost')
LOGSTASH_PORT = int(os.getenv('LOGSTASH_PORT', 5005))
LOGSTASH_URL = f"http://{LOGSTASH_HOST}:{LOGSTASH_PORT}"

LOGSTASH_USER = "logstash_http"
LOGSTASH_PASSWORD = "HttpPassword123!"

SERVICE_NAME = 'LOGGING'


def create_kafka_consumer():
    topic = 'info_in'

    try:
        if '9093' in KAFKA_BOOTSTRAP_SERVERS:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                security_protocol='PLAINTEXT',
                group_id='info-processor-group',
                enable_auto_commit=False,  # если нужен автокоммит, переводим в True
                auto_offset_reset='earliest'
            )

        else:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                security_protocol='SASL_PLAINTEXT',
                sasl_mechanism='SCRAM-SHA-256',
                sasl_plain_username=KAFKA_SASL_USERNAME,
                sasl_plain_password=KAFKA_SASL_PASSWORD,
                group_id='info-processor-group',
                enable_auto_commit=False,  # если нужен автокоммит, переводим в True
                auto_offset_reset='earliest'
            )

    except Exception as e:
        logger.error(f"Ошибка при создании Kafka Producer: {str(e)}")
        raise

    logger.info("Kafka Consumer успешно инициализирован")

    return consumer


def send_to_elk(data):
    with ELK_SEND_TIME.time():
        try:
            elk_document = {
                '@timestamp': data.get('payload', '').get('timestamp', ''),
                'service': "logger-service",
                'executer': data.get('service'),
                'message': data.get('payload', '').get('message', ''),
                'level': random.choice(['info', 'error', 'debug']),
                'action': data.get('action', ''),
                'data': data.get('payload', '').get('data', {})
            }

            response = requests.post(LOGSTASH_URL, json=elk_document, timeout=10, headers={'Content-Type': 'application/json'},
                                     auth=HTTPBasicAuth(LOGSTASH_USER, LOGSTASH_PASSWORD))
            if response.status_code in [200, 201]:
                INFO_MESSAGES_PROCESSED.inc()
                return True
            # return True
        except Exception as e:
            logger.error(f"LOG error: {str(e)}")
    return False


def process_messages():
    consumer = create_kafka_consumer()
    logger.info("Log Processor started")

    try:
        for message in consumer:
            send_to_elk(message.value)
            consumer.commit()
    finally:
        consumer.close()


if __name__ == '__main__':
    start_http_server(int(os.getenv('METRICS_PORT', 8002)))
    process_messages()
