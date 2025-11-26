import psutil
import json
import time
import os
from kafka import KafkaProducer
from dotenv import load_dotenv

load_dotenv()

NODE_NAME = os.getenv("NODE_NAME", "node1")  # تعیین Node از env یا خط فرمان
CPU_THRESHOLD = float(os.getenv("CPU_THRESHOLD", 95))
RAM_THRESHOLD = float(os.getenv("RAM_THRESHOLD", 90))
HDD_THRESHOLD = float(os.getenv("HDD_THRESHOLD", 80))
TOPIC_NAME = os.getenv("TOPIC_NAME", "infra-alerts")
KAFKA_SERVER = os.getenv("KAFKA_SERVER", "localhost:9092")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def check_system():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    print(f"[{NODE_NAME}] CPU: {cpu}%, RAM: {ram}%, HDD: {disk}%")

    alerts = []
    if disk > HDD_THRESHOLD:
        alerts.append(("HDD", disk))
    if ram > RAM_THRESHOLD:
        alerts.append(("RAM", ram))
    if cpu > CPU_THRESHOLD:
        alerts.append(("CPU", cpu))

    return alerts

while True:
    alerts = check_system()
    for res_type, value in alerts:
        data = {
            "node": NODE_NAME,
            "type": res_type,
            "value": value
        }
        producer.send(TOPIC_NAME, data)
        producer.flush()
        print(f"[{NODE_NAME}] sent alert:", data)

    time.sleep(5)
