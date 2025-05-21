import pika, json

def publish_to_queue(rabbit_url: str, queue_name: str, message: dict):
    params     = pika.URLParameters(rabbit_url)
    connection = pika.BlockingConnection(params)
    channel    = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_publish(
        exchange="",
        routing_key=queue_name,
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    connection.close()
