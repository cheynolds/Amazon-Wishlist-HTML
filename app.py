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
    # Fetch the current page from the query parameters, default to 1
    page = int(request.args.get('page', 1))
    in_stock = int(request.args.get('in_stock', 0))  # Fetch the in_stock filter from query params, default is 0 (show all)

    PRODUCTS_PER_PAGE = 20
    offset = (page - 1) * PRODUCTS_PER_PAGE

    # Connect to the database
    conn, cursor = connect_to_db()

    # Query to count the total number of products (considering in stock filter)
    if in_stock:
        cursor.execute("SELECT COUNT(*) FROM product_data WHERE stock_status = 'In Stock'")
    else:
        cursor.execute("SELECT COUNT(*) FROM product_data")
    total_products = cursor.fetchone()[0]

    # Query to fetch products for the current page (considering in stock filter)
    if in_stock:
        query = """
            SELECT asin, title, price, stars, stock_status, image_url, product_link
            FROM product_data
            WHERE stock_status = 'In Stock'
            ORDER BY title ASC
            LIMIT %s OFFSET %s
        """
    else:
        query = """
            SELECT asin, title, price, stars, stock_status, image_url, product_link
            FROM product_data
            ORDER BY title ASC
            LIMIT %s OFFSET %s
        """

    cursor.execute(query, (PRODUCTS_PER_PAGE, offset))
    results = cursor.fetchall()

    # Map the results to a dictionary
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

    # Check if it's an AJAX request (for infinite scroll)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(products)  # Return JSON data for infinite scroll

    # Render the regular product page (initial load)
    return render_template('products.html', products=products, total_products=total_products, PRODUCTS_PER_PAGE=PRODUCTS_PER_PAGE)




# Route for the index/home page
@app.route('/')
def index():
    return redirect(url_for('products'))


# Route for product detail pages, chart pricing data
@app.route('/product/<asin>')
def product_detail(asin):
    conn, cursor = connect_to_db()

    # Fetch all product details, including price and last_checkdate
    product_query = """
    SELECT asin, title, subtitle, price, price_added, reviews, stars, stock_status, image_url, product_link, 
           affiliate_link, pattern, style, wishlist_name, date_added, last_pricechange, last_pricechange_percent, last_checkdate
    FROM product_data
    WHERE asin = %s
    """
    cursor.execute(product_query, (asin,))
    product = cursor.fetchone()

    # Fetch pricing history
    history_query = """
    SELECT price, updated_at 
    FROM product_data_history 
    WHERE asin = %s 
    ORDER BY updated_at ASC
    """
    cursor.execute(history_query, (asin,))
    pricing_history = cursor.fetchall()

    # Ensure we have the current price and last_checkdate as part of the history
    current_price = product[3]  # Price
    last_checkdate = product[16].strftime('%Y-%m-%d') if product[16] else None  # Last price check date

    # Build history data including price_added, date_added, and current price
    history_data = {
        "prices": [product[4]] + [row[0] for row in pricing_history] + [current_price],  # price_added + history + current price
        "dates": [product[14].strftime('%Y-%m-%d')] + [row[1].strftime('%Y-%m-%d') for row in pricing_history] + [last_checkdate]  # date_added + history + last_checkdate
    }

    # Map the product details to a dictionary
    product_data = {
        "asin": product[0],
        "title": product[1],
        "subtitle": product[2],
        "price": product[3],
        "price_added": product[4],
        "reviews": product[5],
        "stars": product[6],
        "stock_status": product[7],
        "image_url": product[8],
        "product_link": product[9],
        "affiliate_link": product[10],
        "pattern": product[11],
        "style": product[12],
        "wishlist_name": product[13],
        "date_added": product[14].strftime('%Y-%m-%d'),
        "last_pricechange": product[15],
        "last_pricechange_percent": product[16],
        "last_checkdate": last_checkdate  # Adding last check date
    }

    cursor.close()
    conn.close()

    return render_template('product_detail.html', product=product_data, history_data=history_data)




@app.route('/top_price_changes')
def top_price_changes():
    # Fetch the page number from query parameters, default to 1
    page = int(request.args.get('page', 1))
    in_stock_only = request.args.get('in_stock', '0') == '1'

    PRODUCTS_PER_PAGE = 20  # Define how many products per page
    offset = (page - 1) * PRODUCTS_PER_PAGE

    # Connect to the database
    conn, cursor = connect_to_db()

    # Modify the query to filter by stock status if needed
    query = """
        SELECT asin, title, price, last_pricechange, last_pricechange_percent, stars, stock_status, image_url, product_link
        FROM product_data
    """
    if in_stock_only:
        query += " WHERE stock_status = 'In Stock' "

    query += " ORDER BY last_pricechange_percent ASC LIMIT %s OFFSET %s"

    cursor.execute(query, (PRODUCTS_PER_PAGE, offset))
    
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
    # Fetch the current page from the query parameters, default to 1
    page = int(request.args.get('page', 1))
    in_stock = int(request.args.get('in_stock', 0))  # 0 = Show all products, 1 = Show in-stock only

    PRODUCTS_PER_PAGE = 20
    offset = (page - 1) * PRODUCTS_PER_PAGE

    # Connect to the database
    conn, cursor = connect_to_db()

    # SQL query to fetch products by wishlist name, with optional stock filter
    if in_stock:
        query = """
        SELECT asin, title, price, stars, stock_status, image_url, product_link
        FROM product_data
        WHERE wishlist_name = %s AND stock_status = 'In Stock'
        LIMIT %s OFFSET %s
        """
    else:
        query = """
        SELECT asin, title, price, stars, stock_status, image_url, product_link
        FROM product_data
        WHERE wishlist_name = %s
        LIMIT %s OFFSET %s
        """
    
    cursor.execute(query, (wishlist_name, PRODUCTS_PER_PAGE, offset))
    products = cursor.fetchall()

    # Map the results to a dictionary
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

    cursor.close()
    conn.close()

    # Check if it's an AJAX request (for infinite scroll)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(product_list)  # Return JSON data for infinite scroll

    # Render the wishlist page with initial products
    return render_template('wishlist_products.html', products=product_list, wishlist_name=wishlist_name)




@app.route('/search', methods=['GET', 'POST'])
def search():
    search_query = request.args.get('q', '')  # Get the search query from the URL parameters
    page = int(request.args.get('page', 1))  # Get the page number for pagination
    in_stock = int(request.args.get('in_stock', 0))  # Fetch the in_stock filter from query params, default is 0 (show all)
    
    PRODUCTS_PER_PAGE = 20
    offset = (page - 1) * PRODUCTS_PER_PAGE

    conn, cursor = connect_to_db()

    # SQL query to search products by title or ASIN with optional stock filter
    search_query_like = f"%{search_query}%"  # Prepare for SQL LIKE statement
    if in_stock:
        query = """
        SELECT asin, title, price, stars, stock_status, image_url, product_link
        FROM product_data
        WHERE (title ILIKE %s OR asin ILIKE %s) AND stock_status = 'In Stock'
        LIMIT %s OFFSET %s
        """
    else:
        query = """
        SELECT asin, title, price, stars, stock_status, image_url, product_link
        FROM product_data
        WHERE title ILIKE %s OR asin ILIKE %s
        LIMIT %s OFFSET %s
        """

    cursor.execute(query, (search_query_like, search_query_like, PRODUCTS_PER_PAGE, offset))
    results = cursor.fetchall()

    # Map the results to a dictionary
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

    # Check if it's an AJAX request (for infinite scroll)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(products)  # Return JSON data for infinite scroll

    # Render the regular search results page (initial load)
    return render_template('search_results.html', products=products, search_query=request.args.get('q', ''))



if __name__ == '__main__':
    app.run(debug=True)