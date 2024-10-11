import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
# Connection parameters
# PostgreSQL connection setup
db_config = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}


try:
    conn = psycopg2.connect(**db_config)
    print("Connected to the database successfully.")
    conn.close()
except Exception as e:
    print(f"Failed to connect: {e}")