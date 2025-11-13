
### Структура проекта
___
>
> geobot/  
> ├── config/ (конфигурации инфраструктуры)  
> ├── data/ (данные сервисов)  
> ├── services/ (функциональные слои)  
> ├── docs/ (документация)  
> ├── docker-compose.yml (главный контейнер)  
> ├── .env (переменыне среды)  
> ├── init.sh (файл развертывания)  
> └── вспомогательные файлы  



### Запуск
___
```bash
sh init.sh
```
Вся инфраструктура развернется в одном контейнере

### Ссылки инфраструктурные
___
> - kafka ui - http://localhost:8090   
> - kafka - SASL_PLAINTEXT://localhost:9092 ,PLAINTEXT_INTERNAL://kafka:9093   
> - zookeeper - http://localhost:2181   
> - elasticsearch - http://localhost:9200   
> - logstash - http://localhost:5005/9600  
> - prometeus - http://localhost:9090  
> - kibana - http://localhost:5601  
> - grafana - http://localhost:3000
> - portainer - http://localhost:9000

### Ссылки функциональные
___
> - LK- http://localhost:5500   
> - ARM - http://localhost:8000  
> - LOG - http://localhost:2181   
> - WORKER-0 - http://localhost:5005/8011  
> - WORKER-1 - http://localhost:5005/8012  
~~> ORCHESTRATOR - http://localhost:8080~~   


### Структура лога
___

```python
elk_document = {
    '@timestamp': data.get('payload', '').get('timestamp', ''), # дата из сервиса
    'service': "logger-service",                                # index для elastic
    'executer': data.get('service'),                            # имя сервиса
    'message': data.get('payload', '').get('message', ''),      # сообщение от сервиса
    'level': random.choice(['info', 'error', 'debug']),         # статус сообщения
    'action': data.get('action', ''),                           # активность
    'data': data.get('payload', '').get('data', {})             # доп данные
}

```

### Структура передачи сообщений
___

```python
message = {
    'service': SERVICE_NAME,                                    # имя сервиса
    'action': 'update_user',                                    # активность
    'payload': {                                                # блок данных
        'message': 'It is update_user',                         # сообщение
        'timestamp': datetime.utcnow().isoformat(),             # время создания события
        'data': request.get_json() if request.is_json else {}   # данные для события
    }
}

```

### Пример фабрики
___
Как от одного сервиса, но с разными активностями обрабатывать сообщения

- Создаем абстрактный класс

```python
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
```
- Наследуемся под реализацию
```python
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
```

- Делаем фабрику которая создает реализации абстрактного класса согласно активности

```python
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
```

- Использование

```python
producer = create_kafka_producer()

payload = message.value
action = payload.get('action')
handler = HandlerFactory.get_handler(action)

handler.process(payload, producer)

```

## Текущая реализация топиков
___
### ЛК:  
> /create_user -> create_user_in   
> /update_user -> update_user_in  
> /info -> info_in  
> /start_task -> task_in

### ARM:
> create_user_in -> info_in   
> update_user_in -> info_in

### WORKER:
> task_in -> info_in 

### LOGGER:
>info_in -> logstash[logger-service] 


## Топики для масштабирования
___

### ЛК
> Исходящие топики:
> 1.	arm_sync_lk — исходящая синхронизация с ARM
> 2.	tg_send — отправка сообщений в ТГ БОТ
> 3.	tg_notify — оповещение в ТГ БОТ
> 4.	tg_robokassa — синхронизация с ТГ   

> Входящие топики:
> 1.	lk_sync_orm — входящая синхронизация с ARM
> 2.	lk_sync_tg — входящая синхронизация с ТГ БОТ

### АРМ
> Исходящие топики:
> 1.	lk_sync_orm — исходящая синхронизация с ЛК
> 2.	tg_send — отправка сообщений в ТГ БОТ
> 3.	worker_start_orm — выдача задачи для WORKER  

> Входящие топики:
> 1.	orm_sync_lk — входящая синхронизация с ЛК
> 2.	worker_done_orm — получение результат выполнения задачи от WORKER
> 3.	orm_sync_tg — входящая синхронизация с ТГ БОТ

### WORKER
> Исходящие топики:
> 1.	worker_done_orm — отправка результат работы в ARM
> 2.	tg_send — отправка сообщений в ТГ БОТ

> Входящие топики:
> 1.	worker_start_orm — получение задания на обработку


### ТГ БОТ
> Исходящие топики:
> 1.	arm_sync_tg — синхроникация с ARM
> 2.	lk_sync_tg — синхронизация с ЛК 

> Входящие топики:
> 1.	tg_send — получение данных на отправку сообщений
> 2.	tg_notify — получение данных для оповещения
> 3.	tg_robokassa — получения данных для маршрутизации пользователя 




