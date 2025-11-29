import psutil
import json
import time
import os
import logging
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from dotenv import load_dotenv

# تنظیمات logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

NODE_NAME = os.getenv("NODE_NAME", "node1")
CPU_THRESHOLD = float(os.getenv("CPU_THRESHOLD", 20))
RAM_THRESHOLD = float(os.getenv("RAM_THRESHOLD", 30))
HDD_THRESHOLD = float(os.getenv("HDD_THRESHOLD", 60))
TOPIC_NAME = os.getenv("TOPIC_NAME", "infra-alerts")
KAFKA_SERVER = os.getenv("KAFKA_SERVER", "kafka:9092")

def create_producer():
    """ایجاد producer با قابلیت retry برای اتصال به Kafka"""
    max_retries = 5
    retry_delay = 10
    
    for attempt in range(max_retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_SERVER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                request_timeout_ms=30000,
                retries=3,
                reconnect_backoff_ms=1000
            )
            # تست اتصال با ارسال یک پیام تست JSON
            test_data = {"test": "connection", "timestamp": time.time()}
            test_future = producer.send('test-connection', test_data)
            test_future.get(timeout=10)
            logger.info(f"✅ Connected to Kafka at {KAFKA_SERVER}")
            return producer
        except NoBrokersAvailable as e:
            logger.warning(f"⚠️ Attempt {attempt + 1}/{max_retries}: Kafka not available at {KAFKA_SERVER}. Retrying in {retry_delay} seconds...")
            if attempt == max_retries - 1:
                logger.error(f"❌ Failed to connect to Kafka after {max_retries} attempts: {e}")
                raise
            time.sleep(retry_delay)
        except Exception as e:
            logger.warning(f"⚠️ Attempt {attempt + 1}/{max_retries}: Connection issue: {e}. Retrying in {retry_delay} seconds...")
            if attempt == max_retries - 1:
                logger.error(f"❌ Failed to connect to Kafka after {max_retries} attempts")
                raise
            time.sleep(retry_delay)

def check_system():
    """بررسی وضعیت سیستم"""
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent

        logger.info(f"[{NODE_NAME}] CPU: {cpu}%, RAM: {ram}%, HDD: {disk}%")

        alerts = []
        if disk > HDD_THRESHOLD:
            alerts.append(("HDD", disk))
        if ram > RAM_THRESHOLD:
            alerts.append(("RAM", ram))
        if cpu > CPU_THRESHOLD:
            alerts.append(("CPU", cpu))

        return alerts
    except Exception as e:
        logger.error(f"Error checking system metrics: {e}")
        return []

def main():
    """تابع اصلی"""
    logger.info(f"🚀 Starting producer on node: {NODE_NAME}")
    logger.info(f"📊 Thresholds - CPU: {CPU_THRESHOLD}%, RAM: {RAM_THRESHOLD}%, HDD: {HDD_THRESHOLD}%")
    
    try:
        producer = create_producer()
    except Exception as e:
        logger.error(f"Failed to create Kafka producer: {e}")
        return

    check_interval = 5  # ثانیه
    
    try:
        while True:
            alerts = check_system()
            for res_type, value in alerts:
                data = {
                    "node": NODE_NAME,
                    "type": res_type,
                    "value": value,
                    "threshold": {
                        "CPU": CPU_THRESHOLD,
                        "RAM": RAM_THRESHOLD,
                        "HDD": HDD_THRESHOLD
                    },
                    "timestamp": time.time()
                }
                try:
                    future = producer.send(TOPIC_NAME, data)
                    # منتظر تایید ارسال می‌مانیم
                    future.get(timeout=10)
                    logger.info(f"📨 Alert sent from {NODE_NAME}: {res_type}={value}%")
                except Exception as e:
                    logger.error(f"Failed to send alert: {e}")

            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        logger.info("🛑 Producer stopped by user")
    except Exception as e:
        logger.error(f"❌ Producer crashed: {e}")
    finally:
        if 'producer' in locals():
            producer.close()
            logger.info("🔚 Producer closed")

if __name__ == "__main__":
    main()