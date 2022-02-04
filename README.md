# MMF-meta
Эта библиотека - часть проекта Model Management Framework.

Отвечает за serving

### Пример использования
```shell
mmfserve serve-rabbit
```

Конфигурация
```dotenv
RABBIT__USER=core
RABBIT__PASSWORD=somesecret
RABBIT_HOST=localhost
EXCHANGE_NAME=test_exchange
QUEUE_NAME=test_queue
MAIN_SCRIPT=main.py
```
[Подробная документация](https://mm-framework.github.io/docs/)
