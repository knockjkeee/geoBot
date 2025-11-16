
from kafka import KafkaConsumer, KafkaProducer
from abc import ABC, abstractmethod
import json
import logging
import os
from datetime import datetime
from prometheus_client import start_http_server, Counter, Histogram
import time

MESSAGES_PROCESSED = Counter('user_processor_messages_processed_total',
                             'Total messages processed', ['action_type'])
PROCESSING_TIME = Histogram('user_processor_processing_seconds',
                            'Time spent processing messages')


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'user-processor',
            'level': record.levelname,
            'message': record.getMessage()
        })


logger = logging.getLogger('user_processor')
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(JsonFormatter())
logger.addHandler(console_handler)

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_SASL_USERNAME = os.getenv('KAFKA_SASL_USERNAME', 'admin')
KAFKA_SASL_PASSWORD = os.getenv('KAFKA_SASL_PASSWORD', 'admin-secret')
CONSUMER_GROUP = os.getenv('CONSUMER_GROUP', 'user-processor-group')

SERVICE_NAME = 'ARM'


class MessageHandler(ABC):
    @abstractmethod
    def process(self, message: dict, producer: KafkaProducer) -> bool:
        pass

    def send_to_info(self, producer: KafkaProducer, message: dict) -> bool:
        try:
            future = producer.send('info_in', value=message)
            future.get(timeout=10)
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки в info_in: {str(e)}")
            return False


class CreateUserHandler(MessageHandler):
    def process(self, message: dict, producer: KafkaProducer) -> bool:
        enriched_message = {
            'service': SERVICE_NAME,
            'action': message.get('action'),
            'payload': {
                'message': 'User created',
                'timestamp': datetime.utcnow().isoformat(),
                'data': message.get('data')
            }
        }

        return self.send_to_info(producer, enriched_message)


class UpdateUserHandler(MessageHandler):
    def process(self, message: dict, producer: KafkaProducer) -> bool:
        enriched_message = {
            'service': SERVICE_NAME,
            'action': message.get('action'),
            'payload': {
                'message': 'User update',
                'timestamp': datetime.utcnow().isoformat(),
                'data': message.get('data')
            }
        }

        return self.send_to_info(producer, enriched_message)


class HandlerFactory:
    _handlers = {
        'create_user': CreateUserHandler,
        'update_user': UpdateUserHandler
    }

    @classmethod
    def get_handler(cls, action: str) -> MessageHandler:
        handler_class = cls._handlers.get(action)
        if not handler_class:
            raise ValueError(f"Unknown action: {action}")
        return handler_class()


def create_kafka_consumer(topics):

    try:
        if '9093' in KAFKA_BOOTSTRAP_SERVERS:
            consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                security_protocol='PLAINTEXT',
                group_id=CONSUMER_GROUP,
                enable_auto_commit=False,  # если нужен автокоммит, переводим в True
                auto_offset_reset='earliest'
            )

        else:
            consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                security_protocol='SASL_PLAINTEXT',
                sasl_mechanism='SCRAM-SHA-256',
                sasl_plain_username=KAFKA_SASL_USERNAME,
                sasl_plain_password=KAFKA_SASL_PASSWORD,
                group_id=CONSUMER_GROUP,
                enable_auto_commit=False,  # если нужен автокоммит, переводим в True
                auto_offset_reset='earliest'
            )

    except Exception as e:
        logger.error(f"Ошибка при создании Kafka Producer: {str(e)}")
        raise

    logger.info("Kafka Consumer успешно инициализирован")
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


def process_messages():
    topics = ['create_user_in', 'update_user_in']
    consumer = create_kafka_consumer(topics)
    producer = create_kafka_producer()

    logger.info("Arm Processor started")

    try:
        for message in consumer:
            start_time = time.time()
            try:
                payload = message.value
                action = payload.get('action')
                handler = HandlerFactory.get_handler(action)

                if handler.process(payload, producer):
                    MESSAGES_PROCESSED.labels(action_type=action).inc()
                    consumer.commit()
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
            finally:
                PROCESSING_TIME.observe(time.time() - start_time)

    finally:
        consumer.close()
        producer.close()


if __name__ == '__main__':
    metrics_port = int(os.getenv('METRICS_PORT', 8000))
    start_http_server(metrics_port)
    process_messages()
