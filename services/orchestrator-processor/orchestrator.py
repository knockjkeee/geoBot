# from flask import Flask, jsonify, request
# from kafka.admin import KafkaAdminClient, NewPartitions
# import docker
# import json
# import logging
# import os
# from datetime import datetime
# from prometheus_client import make_wsgi_app, Counter, Gauge
# from werkzeug.middleware.dispatcher import DispatcherMiddleware
#
#
# class JsonFormatter(logging.Formatter):
#     def format(self, record):
#         return json.dumps({
#             'timestamp': datetime.utcnow().isoformat(),
#             'service': 'orchestrator',
#             'level': record.levelname,
#             'message': record.getMessage()
#         })
#
#
# logger = logging.getLogger('orchestrator')
# logger.setLevel(logging.INFO)
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(JsonFormatter())
# logger.addHandler(console_handler)
#
# app = Flask(__name__)
#
# SCALE_OPERATIONS = Counter('orchestrator_scale_operations_total', 'Scale operations', ['service'])
# ACTIVE_CONTAINERS = Gauge('orchestrator_active_containers', 'Active containers', ['service'])
# # ACTIVE_CONTAINERS = Gauge('orchestrator_active_containers', 'Active containers')
#
# KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
# KAFKA_SASL_USERNAME = os.getenv('KAFKA_SASL_USERNAME', 'admin')
# KAFKA_SASL_PASSWORD = os.getenv('KAFKA_SASL_PASSWORD', 'admin-secret')
#
# try:
#     docker_client = docker.from_env()
# except:
#     docker_client = None
#
#
# def create_kafka_admin():
#     try:
#         return KafkaAdminClient(
#             bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
#             security_protocol='SASL_PLAINTEXT',
#             sasl_mechanism='SCRAM-SHA-256',
#             sasl_plain_username=KAFKA_SASL_USERNAME,
#             sasl_plain_password=KAFKA_SASL_PASSWORD
#         )
#     except:
#         return None
#
#
# kafka_admin = create_kafka_admin()
#
#
# @app.route('/health', methods=['GET'])
# def health():
#     return jsonify({'status': 'healthy'}), 200
#
#
# @app.route('/kafka/topics', methods=['GET'])
# def get_kafka_topics():
#     if not kafka_admin:
#         return jsonify({'error': 'Kafka Admin unavailable'}), 503
#     topics = kafka_admin.list_topics()
#     return jsonify({'topics': list(topics)}), 200
#
#
# @app.route('/kafka/partitions/<topic>', methods=['POST'])
# def scale_topic_partitions(topic):
#     if not kafka_admin:
#         return jsonify({'error': 'Kafka Admin unavailable'}), 503
#
#     data = request.get_json()
#     new_partition_count = data.get('partitions')
#
#     topic_partitions = {topic: NewPartitions(total_count=new_partition_count)}
#     kafka_admin.create_partitions(topic_partitions)
#
#     SCALE_OPERATIONS.labels(service='kafka').inc()
#     return jsonify({'status': 'success', 'topic': topic}), 200
#
#
# @app.route('/services', methods=['GET'])
# def get_services():
#     if not docker_client:
#         return jsonify({'error': 'Docker unavailable'}), 503
#
#     containers = docker_client.containers.list(all=True)
#     services_info = []
#
#     for container in containers:
#         services_info.append({
#             'id': container.short_id,
#             'name': container.name,
#             'status': container.status
#         })
#
#     ACTIVE_CONTAINERS.inc()
#     return jsonify({'services': services_info}), 200
#
#
# if __name__ == '__main__':
#     app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {'/metrics': make_wsgi_app()})
#     port = int(os.getenv('ORCHESTRATOR_PORT', 8080))
#     app.run(host='0.0.0.0', port=port, debug=False)