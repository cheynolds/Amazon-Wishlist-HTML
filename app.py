from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
import psycopg2

app = Flask(__name__)

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# PostgreSQL connection parameters
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


PRODUCTS_PER_PAGE = 20  # or any number of products you want to load per "page"


def connect_to_db():
    """Establishes connection to PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        cursor = conn.cursor()
        return conn, cursor
    except Exception as e:
        print(f"Failed to connect to PostgreSQL: {e}")
        return None, None

def get_wishlists():
    """Fetch distinct wishlist names from PostgreSQL."""
    try:
        # Connect to PostgreSQL
        conn, cursor = connect_to_db()
        if not conn:
            return
        cursor.execute("SELECT DISTINCT wishlist_name FROM product_data ORDER BY wishlist_name")
        wishlists = cursor.fetchall()
        return [wishlist[0] for wishlist in wishlists]
    except Exception as e:
        print(f"Failed to fetch wishlists: {e}")
        return []

def get_products_by_wishlist(wishlist_name, in_stock=True):
    """Fetch products from a specific wishlist, with optional stock filtering."""
    conn, cursor = connect_to_db()
    try:
        if in_stock:
            # Query to get only products that are in stock for the specific wishlist
            cursor.execute("""
                SELECT asin, title, price, last_pricechange, last_pricechange_percent, product_link, image_url, stock_status
                FROM product_data
                WHERE wishlist_name = %s AND stock_status = 'In Stock' AND price != 0.00
            """, (wishlist_name,))
        else:
            # Query to get all products for the specific wishlist, regardless of stock status
            cursor.execute("""
                SELECT asin, title, price, last_pricechange, last_pricechange_percent, product_link, image_url, stock_status
                FROM product_data
                WHERE wishlist_name = %s
            """, (wishlist_name,))

        products = cursor.fetchall()

        # Convert to list of dictionaries
        columns = [desc[0] for desc in cursor.description]
        product_list = [dict(zip(columns, product)) for product in products]

        return product_list

    except Exception as e:
        print(f"Error fetching products for wishlist {wishlist_name}: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_product_by_asin(asin):
    """Fetch product data based on the ASIN."""
    conn, cursor = connect_to_db()
    try:
        cursor.execute("""
            SELECT asin, title, price, last_pricechange, last_pricechange_percent, product_link, image_url, stock_status, reviews, stars
            FROM product_data
            WHERE asin = %s
        """, (asin,))
        product = cursor.fetchone()

        # Convert to a dictionary if product is found
        if product:
            columns = [desc[0] for desc in cursor.description]
            product_dict = dict(zip(columns, product))
            return product_dict

        return None  # Return None if no product is found
    except Exception as e:
        print(f"Error fetching product by ASIN {asin}: {e}")
        return None
    finally:
        cursor.close()
        conn.close()



def get_products():
    """Fetch product data from PostgreSQL."""
    try:
        # Connect to PostgreSQL
        conn, cursor = connect_to_db()
        if not conn:
            return
        cursor.execute("""
            SELECT asin, title, subtitle, price_added, price, stock_status, date_added, product_link, affiliate_link, image_url, 
            reviews, stars, pattern, style, wishlist_name, last_pricechange, last_pricechange_percent 
            FROM product_data
        """)
        products = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        product_list = [dict(zip(columns, product)) for product in products]
        return product_list
    except Exception as e:
        print(f"Failed to fetch products: {e}")
        return []

@app.route('/api/products')
def api_products():
    # Fetch the page number from query parameters, default to 1
    page = int(request.args.get('page', 1))
    
    PRODUCTS_PER_PAGE = 20  # Define how many products per page
    offset = (page - 1) * PRODUCTS_PER_PAGE

    # Fetch products from the database with limit and offset
    conn, cursor = connect_to_db()
    cursor.execute("""
        SELECT asin, title, price, stars, stock_status, image_url, product_link
        FROM product_data
        ORDER BY title ASC
        LIMIT %s OFFSET %s
    """, (PRODUCTS_PER_PAGE, offset))
    
    products = cursor.fetchall()
    
    # Convert to a list of dictionaries
    product_list = [
        {
            'asin': row[0],
            'title': row[1],
            'price': row[2],
            'stars': row[3],
            'stock_status': row[4],
            'image_url': row[5],
            'product_link': row[6]
        }
        for row in products
    ]

    # If it's an AJAX request (for infinite scroll), return JSON data
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(product_list)

    # Otherwise, render the page normally with the initial products
    return render_template('products.html', products=product_list)







@app.route('/products')
def products():
    # Fetch the current page (optional, initially 1)
    page = 1

    # Connect to the database
    conn, cursor = connect_to_db()

    # Query to count the total number of products for pagination
    cursor.execute("SELECT COUNT(*) FROM product_data")
    total_products = cursor.fetchone()[0]

    # Query to fetch products for the first page
    query = """
    SELECT asin, title, price, stars, stock_status, image_url, product_link 
    FROM product_data 
    ORDER BY title ASC 
    LIMIT %s OFFSET %s
    """
    offset = (page - 1) * PRODUCTS_PER_PAGE
    cursor.execute(query, (PRODUCTS_PER_PAGE, offset))
    results = cursor.fetchall()

    # Map the results to a dictionary to pass to the template
    products = [
        {
            'asin': row[0],
            'title': row[1],
            'price': row[2],
            'stars': row[3],
            'stock_status': row[4],
            'image_url': row[5],
            'product_link': row[6]
        }
        for row in results
    ]

    cursor.close()
    conn.close()

    return render_template('products.html', products=products, total_products=total_products, PRODUCTS_PER_PAGE=PRODUCTS_PER_PAGE)


# Route for the index/home page
@app.route('/')
def index():
    return redirect(url_for('products'))

# @app.route('/product/<asin>')
# def product_detail(asin):
#     # Fetch product details
#     product = get_product_by_asin(asin)
#
#     # Fetch pricing history for the product
#     history_query = """
#     SELECT price, updated_at FROM product_data_history WHERE asin = %s ORDER BY updated_at ASC
#     """
#     conn, cursor = connect_to_db()
#     cursor.execute(history_query, (asin,))
#     pricing_history = cursor.fetchall()
#
#     # Convert pricing history to JSON format for Chart.js
#     history_data = {
#         "prices": [row[0] for row in pricing_history],
#         "dates": [row[1].strftime('%Y-%m-%d') for row in pricing_history]
#     }
#
#     return render_template('product_detail.html', product=product, history_data=history_data)

@app.route('/product/<asin>')
def product_detail(asin):
    # Connect to the database
    conn, cursor = connect_to_db()

    # Fetch product details, including price_added and date_added
    product_query = """
    SELECT price_added, date_added, price, reviews, stars, stock_status, image_url, product_link, title
    FROM product_data WHERE asin = %s
    """
    cursor.execute(product_query, (asin,))
    product = cursor.fetchone()

    # Fetch pricing history for the product
    history_query = """
    SELECT price, updated_at FROM product_data_history WHERE asin = %s ORDER BY updated_at ASC
    """
    cursor.execute(history_query, (asin,))
    pricing_history = cursor.fetchall()

    # Add the initial price and date from the product_data table as the first point in the chart
    if product:
        price_added = product[0]
        date_added = product[1].strftime('%Y-%m-%d') if product[1] else None
    else:
        price_added, date_added = None, None

    # Convert pricing history to JSON format for Chart.js, including the added price and date
    history_data = {
        "prices": [price_added] + [row[0] for row in pricing_history] if price_added else [row[0] for row in pricing_history],
        "dates": [date_added] + [row[1].strftime('%Y-%m-%d') for row in pricing_history] if date_added else [row[1].strftime('%Y-%m-%d') for row in pricing_history]
    }

    # Map the product details to a dictionary to pass to the template
    product_data = {
        "title": product[8] if product else "Unknown Product",
        "price": product[2] if product else "N/A",
        "reviews": product[3] if product else "N/A",
        "stars": product[4] if product else "N/A",
        "stock_status": product[5] if product else "N/A",
        "image_url": product[6] if product else "N/A",
        "product_link": product[7] if product else "#",
        "last_pricechange": None,  # You can add the logic to compute this if needed
        "last_pricechange_percent": None  # You can add the logic to compute this if needed
    }

    # Close the database connection
    cursor.close()
    conn.close()

    return render_template('product_detail.html', product=product_data, history_data=history_data)








@app.route('/top_price_changes')
def top_price_changes():
    # Fetch the page number from query parameters, default to 1
    page = int(request.args.get('page', 1))
    
    PRODUCTS_PER_PAGE = 20  # Define how many products per page
    offset = (page - 1) * PRODUCTS_PER_PAGE

    # Fetch products from the database with limit and offset
    conn, cursor = connect_to_db()
    cursor.execute("""
        SELECT asin, title, price, last_pricechange, last_pricechange_percent, stars, stock_status, image_url, product_link
        FROM product_data
        ORDER BY last_pricechange_percent ASC
        LIMIT %s OFFSET %s
    """, (PRODUCTS_PER_PAGE, offset))
    
    products = cursor.fetchall()
    
    # Convert to a list of dictionaries
    product_list = [
        {
            'asin': row[0],
            'title': row[1],
            'price': row[2],
            'last_pricechange': row[3],
            'last_pricechange_percent': row[4],
            'stars': row[5],
            'stock_status': row[6],
            'image_url': row[7],
            'product_link': row[8]
        }
        for row in products
    ]

    # If it's an AJAX request (for infinite scroll), return JSON data
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(product_list)

    # Otherwise, render the page normally with the initial products
    return render_template('top_price_changes.html', products=product_list)





@app.route('/categories')
def categories():
    wishlists = get_wishlists()
    return render_template('categories.html', wishlists=wishlists)

@app.route('/wishlist/<wishlist_name>')
def wishlist_products(wishlist_name):
    # Fetch products by wishlist name, only if they're in stock
    products = get_products_by_wishlist(wishlist_name, in_stock=True)
    return render_template('wishlist_products.html', products=products, wishlist_name=wishlist_name)



@app.route('/search', methods=['GET', 'POST'])
def search():
    search_query = request.args.get('q', '')  # Get the search query from the URL parameters
    conn, cursor = connect_to_db()

    # SQL query to search products by title or ASIN
    search_query = f"%{search_query}%"  # Prepare for SQL LIKE statement
    query = """
    SELECT asin, title, price, stars, stock_status, image_url, product_link
    FROM product_data
    WHERE title ILIKE %s OR asin ILIKE %s
    """
    cursor.execute(query, (search_query, search_query))
    results = cursor.fetchall()

    # Map the results to a dictionary to pass to the template
    products = [
        {
            'asin': row[0],
            'title': row[1],
            'price': row[2],
            'stars': row[3],
            'stock_status': row[4],
            'image_url': row[5],
            'product_link': row[6]
        }
        for row in results
    ]

    cursor.close()
    conn.close()

    return render_template('search_results.html', products=products, search_query=request.args.get('q', ''))


if __name__ == '__main__':
    app.run(debug=True)