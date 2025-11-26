# 🖥️ Infrastructure Monitoring System using Apache Kafka

این پروژه یک سیستم مانیتورینگ زیرساخت (Infrastructure Monitoring) است که چندین Node (سرور) را بررسی کرده و در صورتی که میزان CPU / RAM / HDD از حد مجاز عبور کند، یک پیام هشدار (Alert) به Kafka ارسال می‌کند.  

یک Consumer این پیام‌ها را دریافت کرده و درون دیتابیس PostgreSQL ذخیره می‌کند.  
همچنین Consumer آخرین وضعیت هر Node را در خروجی نمایش می‌دهد.

---

## 📌 ساختار پروژه

```
server_kafka/
│
├── producer_nodes/
│   ├── node1.py
│   ├── node2.py
│   ├── node3.py
│   └── .env
│
├── consumer/
│   └── consumer.py
│
├── db/
│   └── init_sql.sql
│
└── README.md
```

---

## ⚙️ پیش‌نیازها

### نرم‌افزارهای لازم:
- Python 3.10+
- Apache Kafka
- Zookeeper (در نسخه‌های Kafka < 3.4)
- PostgreSQL
- Git
- pip packages:
  - `psutil`
  - `kafka-python`
  - `python-dotenv`
  - `psycopg2`

نصب کتابخانه‌ها:

```bash
pip install psutil kafka-python python-dotenv psycopg2
```

---

## 📥 Database Setup (PostgreSQL)

فایل ساخت جدول:

```sql
CREATE TABLE infra_alerts (
    id SERIAL PRIMARY KEY,
    node VARCHAR(50),
    type VARCHAR(10),
    value NUMERIC,
    timestamp TIMESTAMP
);
```

ساخت جدول:

```bash
psql -U postgres -d infra_db -f db/init_sql.sql
```

---

## 🚀 اجرای Kafka

### شروع Zookeeper:

```bash
bin/zookeeper-server-start.sh config/zookeeper.properties
```

### اجرای Kafka Server:

```bash
bin/kafka-server-start.sh config/server.properties
```

### ساخت Topic:

```bash
bin/kafka-topics.sh --create --topic infra-alerts --bootstrap-server localhost:9092
```

---

## 📡 تنظیم `.env` (مشترک برای همه Nodeها)

```
CPU_THRESHOLD=20
RAM_THRESHOLD=30
HDD_THRESHOLD=60
TOPIC_NAME=infra-alerts
KAFKA_SERVER=localhost:9092
```

---

## 🖥️ اجرای Node ها

هر Node یک نام متفاوت دارد (بدون تغییر کد):

### Node1:

```bash
set NODE_NAME=node1
python producer_nodes/node1.py
```

### Node2:

```bash
set NODE_NAME=node2
python producer_nodes/node2.py
```

### Node3:

```bash
set NODE_NAME=node3
python producer_nodes/node3.py
```

---

## 🔍 اجرای Consumer

```bash
python consumer/consumer.py
```

خروجی مثال:

```
node1 → CPU: 35%, RAM: 42%, HDD: 71%
node1 → CPU: 50%, RAM: 42%, HDD: 71%
node2 → CPU: 21%, RAM: 33%, HDD: 55%
```

تمام پیام‌ها نیز در دیتابیس ذخیره می‌شوند.

---

## 📦 Git Setup

### ایجاد ریپو جدید:

```bash
git init
git add .
git commit -m "Initial commit: infra monitoring system"
git branch -M main
git remote add origin https://github.com/USERNAME/infra-monitoring-kafka.git
git push -u origin main
```

---

## 🔒 فایل‌هایی که نباید وارد GitHub شوند

فایل `.gitignore`:

```
.env
__pycache__/
*.pyc
```

---

## 🧩 قابلیت‌های آینده (Optional)

- داشبورد گرافیکی با Grafana / Prometheus  
- هشدار پیامکی یا تلگرام هنگام عبور Threshold  
- API برای نمایش آخرین وضعیت Nodeها  
- Dockerization برای اجرای ساده‌تر  


