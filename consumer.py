import os
import json
import time
import pika
from sqlalchemy import create_engine, text
from app.engine_parser import parse_formulas
from app.engine_pre_processor import process_formula_variables
from app.engine_eval import eval_formula

# Variáveis de ambiente
env_rabbit = os.getenv("RABBIT_URL", "amqp://guest:guest@rabbitmq:5672/")
env_db    = os.getenv("POSTGRES_URL", None)

# Configura DB se definido
if env_db:
    engine = create_engine(env_db)
    from sqlalchemy.exc import SQLAlchemyError

QUEUE_NAME = "engine_queue"


def get_rabbit_connection(max_tries=10, delay=5):
    params = pika.URLParameters(env_rabbit)
    for attempt in range(1, max_tries + 1):
        try:
            conn = pika.BlockingConnection(params)
            print(f"[worker] Conectado ao RabbitMQ na tentativa {attempt}")
            return conn
        except pika.exceptions.AMQPConnectionError:
            print(f"[worker] RabbitMQ indisponível, retry {attempt}/{max_tries} em {delay}s…")
            time.sleep(delay)
    raise RuntimeError("Não foi possível conectar ao RabbitMQ após várias tentativas.")


def callback(ch, method, properties, body):
    try:
        msg = json.loads(body)
    except json.JSONDecodeError:
        print("[worker] Mensagem inválida (JSON). Ignorando.")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    payload = msg.get("payload")
    results = msg.get("results")
    req_id = msg.get("request_id")

    if payload is None or results is None:
        print("[worker] Mensagem sem payload ou result. Ignorando.")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    # Se houver engine e payload, podemos reprocessar opcionalmente
    # (normalmente o motor já rodou na API)
    # >>> Caso queira reavaliar, descomente abaixo:
    # extracted = parse_formulas({"data": payload})
    # processed = process_formula_variables(extracted, {"data": payload})
    # results = eval_formula(processed, extracted)

    # Persiste no banco se existir request_id e engine configurado
    if req_id is not None and env_db:
        try:
            with engine.begin() as conn:
                conn.execute(
                    text("INSERT INTO responses(request_id, result) VALUES(:rid, :r)"),
                    {"rid": req_id, "r": json.dumps(results)}
                )
            print(f"[worker] Response salva para request_id={req_id}")
        except SQLAlchemyError as err:
            print(f"[worker] Erro ao salvar no DB: {err}")
    else:
        print(f"[worker] Processado sem salvar (request_id={req_id})")

    ch.basic_ack(delivery_tag=method.delivery_tag)


def consume():
    connection = get_rabbit_connection()
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    print(f"[*] Worker aguardando mensagens na fila '{QUEUE_NAME}'…")
    channel.start_consuming()


if __name__ == "__main__":
    consume()
