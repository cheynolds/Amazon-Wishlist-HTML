import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
# PostgreSQL connection setup
db_config = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    print("Connected to PostgreSQL database.")

    # Query to retrieve data
    cursor.execute("SELECT * FROM product_data;")
    rows = cursor.fetchall()

    # Check if any data was returned
    if rows:
        print("Data in product_data:")
        for row in rows:
            print(row)
    else:
        print("No data found in product_data.")

except Exception as e:
    print(f"Failed to connect to PostgreSQL: {e}")
finally:
    # Clean up
    if cursor:
        cursor.close()
    if conn:
        conn.close()
