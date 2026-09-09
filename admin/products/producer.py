import pika, json

params = pika.URLParameters('amqps://gbqygyjp:UPi4u72ZmgtgR9dIzRygJ1RoRKpcETl4@kebnekaise.lmq.cloudamqp.com/gbqygyjp')

connection = pika.BlockingConnection(params)

channel = connection.channel()


def publish(method, body):
    properties = pika.BasicProperties(method)
    channel.basic_publish(exchange='', routing_key='main', body=json.dumps(body), properties=properties)
