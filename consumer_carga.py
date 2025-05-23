#!/usr/bin/env python3
import os
import json
import subprocess
import time
import pika

# URL do RabbitMQ (padrão se não estiver no .env)
RABBIT_URL = os.getenv("RABBIT_URL", "amqp://guest:guest@rabbitmq:5672/")
QUEUE_NAME = "carga_queue"

def callback(ch, method, properties, body):
    """
    Callback chamado para cada mensagem da fila `carga_queue`.
    Executa `teste_carga.py` passando a mensagem JSON pelo stdin.
    """
    msg = json.loads(body)
    try:
        proc = subprocess.run(
            ["python", "teste_carga.py"],
            input=json.dumps(msg),
            text=True,
            capture_output=True
        )
        if proc.returncode != 0:
            print(f"[carga] ERRO (code={proc.returncode}) ao processar request_id={msg.get('request_id')}")
            print(proc.stderr)
        else:
            print(f"[carga] Sucesso request_id={msg.get('request_id')}")
            print(proc.stdout)
    except Exception as e:
        print(f"[carga] Exceção durante o teste de carga: {e}")
    finally:
        # Confirma o consumo da mensagem mesmo em caso de erro
        ch.basic_ack(delivery_tag=method.delivery_tag)

def consume():
    """
    Tenta conectar ao RabbitMQ indefinidamente.
    Quando conectado, declara a fila e passa a consumir.
    """
    params = pika.URLParameters(RABBIT_URL)
    connection = None

    while not connection:
        try:
            connection = pika.BlockingConnection(params)
        except pika.exceptions.AMQPConnectionError:
            print("[carga] RabbitMQ indisponível, aguardando 5s para retry...")
            time.sleep(5)

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    print(f"[carga] Conectado ao RabbitMQ. Aguardando mensagens em '{QUEUE_NAME}'…")
    channel.start_consuming()

if __name__ == "__main__":
    consume()
