import json
import psycopg2
from kafka import KafkaConsumer
from dotenv import load_dotenv
import os
import logging

# تنظیمات logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# تنظیمات از environment variables
KAFKA_SERVER = os.getenv("KAFKA_SERVER", "kafka:9092")
TOPIC_NAME = os.getenv("TOPIC_NAME", "infra-alerts")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "infra_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "radmin9335")

def create_db_connection():
    """ایجاد اتصال به دیتابیس"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        logger.info(f"✅ Connected to database at {DB_HOST}:{DB_PORT}")
        return conn
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

def create_kafka_consumer():
    """ایجاد Kafka consumer"""
    try:
        consumer = KafkaConsumer(
            TOPIC_NAME,
            bootstrap_servers=KAFKA_SERVER,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='infra-monitor-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        logger.info(f"✅ Connected to Kafka at {KAFKA_SERVER}")
        return consumer
    except Exception as e:
        logger.error(f"❌ Kafka connection failed: {e}")
        raise

def init_database(conn):
    """ایجاد جدول اگر وجود ندارد"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                node_name VARCHAR(50) NOT NULL,
                alert_type VARCHAR(20) NOT NULL,
                value FLOAT NOT NULL,
                threshold JSONB,
                timestamp FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        logger.info("✅ Database table initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

def save_alert(conn, data):
    """ذخیره alert در دیتابیس"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alerts (node_name, alert_type, value, threshold, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            data.get('node'),
            data.get('type'),
            data.get('value'),
            json.dumps(data.get('threshold', {})),
            data.get('timestamp')
        ))
        conn.commit()
        cursor.close()
        logger.info(f"💾 Alert saved: {data.get('node')} - {data.get('type')} - {data.get('value')}%")
    except Exception as e:
        logger.error(f"❌ Failed to save alert: {e}")
        conn.rollback()

def main():
    """تابع اصلی"""
    logger.info("🚀 Starting consumer...")
    
    try:
        # ایجاد اتصال به دیتابیس
        db_conn = create_db_connection()
        init_database(db_conn)
        
        # ایجاد Kafka consumer
        consumer = create_kafka_consumer()
        
        logger.info("👂 Listening for messages...")
        
        # پردازش پیام‌ها
        for message in consumer:
            try:
                data = message.value
                logger.info(f"📥 Received message: {data}")
                
                # ذخیره در دیتابیس
                save_alert(db_conn, data)
                
            except Exception as e:
                logger.error(f"❌ Error processing message: {e}")
                
    except KeyboardInterrupt:
        logger.info("🛑 Consumer stopped by user")
    except Exception as e:
        logger.error(f"❌ Consumer crashed: {e}")
    finally:
        if 'db_conn' in locals():
            db_conn.close()
            logger.info("🔚 Database connection closed")
        if 'consumer' in locals():
            consumer.close()
            logger.info("🔚 Kafka consumer closed")

if __name__ == "__main__":
    main()