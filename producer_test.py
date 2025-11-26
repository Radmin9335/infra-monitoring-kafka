from kafka import KafkaProducer
import psutil
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()  # خواندن فایل env

CPU_TH = int(os.getenv("CPU_THRESHOLD"))
RAM_TH = int(os.getenv("RAM_THRESHOLD"))
HDD_TH = int(os.getenv("HDD_THRESHOLD"))
NODE = os.getenv("NODE_NAME")

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

while True:
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    hdd = psutil.disk_usage('/').percent

    print(cpu, ram, hdd)

    if cpu > CPU_TH:
        producer.send("infra-alerts", {"node": NODE, "type": "CPU", "value": cpu})

    if ram > RAM_TH:
        producer.send("infra-alerts", {"node": NODE, "type": "RAM", "value": ram})

    if hdd > HDD_TH:
        producer.send("infra-alerts", {"node": NODE, "type": "HDD", "value": hdd})

    producer.flush()
    time.sleep(2)
