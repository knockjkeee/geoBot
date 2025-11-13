from flask import Flask, render_template, request, jsonify
from kafka import KafkaProducer
from prometheus_flask_exporter import PrometheusMetrics
import json
import logging
import os
from datetime import datetime


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'flask-producer',
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_data)


logger = logging.getLogger('producer')
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(JsonFormatter())
logger.addHandler(console_handler)

app = Flask(__name__)
metrics = PrometheusMetrics(app)
metrics.info('producer_info', 'Flask Producer Service', version='1.0.0')

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_SASL_USERNAME = os.getenv('KAFKA_SASL_USERNAME', 'admin')
KAFKA_SASL_PASSWORD = os.getenv('KAFKA_SASL_PASSWORD', 'admin-secret')

SERVICE_NAME = 'LK'


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


producer = create_kafka_producer()
print(producer)


def send_to_kafka(topic, message):
    try:
        future = producer.send(topic, value=message)
        # record_metadata = future.get(timeout=10)
        logger.info(f"Сообщение отправлено в топик {topic}")
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки в Kafka: {str(e)}")
        return False


@app.route('/')
def landing():
    return render_template('index.html')


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'flask-producer'}), 200


@app.route('/create_user', methods=['GET'])
def create_user():
    message = {
        'service': SERVICE_NAME,
        'action': 'create_user',

    }
    if send_to_kafka('create_user_in', message):
        return jsonify({'status': 'success'}), 200
    return jsonify({'status': 'error'}), 500


@app.route('/update_user', methods=['POST'])
def update_user():
    message = {
        'service': SERVICE_NAME,
        'action': 'update_user',
        'payload': {
            'message': 'It is update_user',
            'timestamp': datetime.utcnow().isoformat(),
            'data': request.get_json() if request.is_json else {}
        }
    }
    if send_to_kafka('update_user_in', message):
        return jsonify({'status': 'success'}), 200
    return jsonify({'status': 'error'}), 500


@app.route('/info', methods=['GET'])
def info():
    message = {
        'service': SERVICE_NAME,
        'action': 'info',
        'payload': {
            'message': 'It is info',
            'timestamp': datetime.utcnow().isoformat(),
            'data': request.get_json() if request.is_json else {}
        }

    }
    if send_to_kafka('info_in', message):
        return jsonify({'status': 'success'}), 200
    return jsonify({'status': 'error'}), 500


@app.route('/start_task', methods=['GET'])
def start_task():
    message = {
        'service': SERVICE_NAME,
        'action': 'start_task',
        'payload': {
            'message': 'It is start_task',
            'timestamp': datetime.utcnow().isoformat(),
            'data': request.get_json() if request.is_json else {}
        }
    }
    if send_to_kafka('task_in', message):
        return jsonify({'status': 'success'}), 200
    return jsonify({'status': 'error'}), 500


if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    port = int(os.getenv('PORT', 5500))
    app.run(host='0.0.0.0', port=port, debug=False)
