from kafka import KafkaConsumer
import json
import psycopg2

# اتصال به دیتابیس
conn = psycopg2.connect(
    dbname="infra_db",
    user="postgres",
    password="radmin9335",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

consumer = KafkaConsumer(
    'infra-alerts',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
    auto_offset_reset='earliest'
)

print("Consumer started. Listening for messages...")

# دیکشنری نگه داشتن آخرین وضعیت هر Node
nodes_status = {}

for msg in consumer:
    data = msg.value
    node = data['node']
    type_ = data['type']
    value = data['value']

    # آپدیت دیتابیس
    cursor.execute("""
        INSERT INTO infra_alerts (node, type, value, timestamp)
        VALUES (%s, %s, %s, NOW())
    """, (node, type_, value))
    conn.commit()

    # آپدیت دیکشنری وضعیت
    if node not in nodes_status:
        nodes_status[node] = {"CPU": "-", "RAM": "-", "HDD": "-"}
    nodes_status[node][type_] = value

    # چاپ وضعیت کامل Node
    status = nodes_status[node]
    print(f"{node} → CPU: {status['CPU']}%, RAM: {status['RAM']}%, HDD: {status['HDD']}%")
