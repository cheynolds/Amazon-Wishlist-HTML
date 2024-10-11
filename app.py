from flask import Flask, render_template
import psycopg2

app = Flask(__name__)

from dotenv import load_dotenv
import os

load_dotenv()

# PostgreSQL connection settings
db_config = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

def get_products():
    """Fetch product data from PostgreSQL."""
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT asin, title, subtitle, price, stock_status, date_added, product_link, affiliate_link, image_url, reviews, stars, pattern, style, wishlist_name FROM product_data")
        products = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        product_list = [dict(zip(columns, product)) for product in products]
        return product_list
    except Exception as e:
        print(f"Failed to fetch products: {e}")
        return []

@app.route('/products')
def product_list():
    products = get_products()
    return render_template('products.html', products=products)

if __name__ == '__main__':
    app.run(debug=True)
