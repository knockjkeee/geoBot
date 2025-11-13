FROM python:3.11-slim

LABEL maintainer="your-email@example.com"
LABEL description="Flask Producer Service for Kafka Microservices"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN mkdir -p logs

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5500/health')" || exit 1

CMD ["python", "appWeb.py"]