from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# Get the database URL from environment variable
DB_URL = os.environ.get("DATABASE_URL")

def get_db():
    conn = psycopg2.connect(DB_URL)
    return conn

def init_db():
    if not DB_URL:
        return
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS product (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                sold_count INTEGER DEFAULT 0
            )
        ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = get_db()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute('SELECT * FROM product')
        products = cur.fetchall()
    conn.close()
    return render_template('index.html', products=products)

@app.route('/analytics')
def analytics():
    conn = get_db()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute('SELECT * FROM product')
        products_rows = cur.fetchall()
    conn.close()
    
    products = []
    total_sales = 0
    total_items = 0
    
    for row in products_rows:
        p = dict(row)
        p['total_sales'] = p['price'] * p['sold_count']
        products.append(p)
        total_sales += p['total_sales']
        total_items += p['sold_count']
        
    return render_template('analytics.html', 
                         products=products, 
                         total_sales=total_sales, 
                         total_items=total_items)

@app.route('/update_sale', methods=['POST'])
def update_sale():
    product_id = request.form.get('product_id')
    change = int(request.form.get('change', 0))
    
    conn = get_db()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute('SELECT * FROM product WHERE id = %s', (product_id,))
        product = cur.fetchone()
        
        if product:
            new_count = max(0, product['sold_count'] + change)
            cur.execute('UPDATE product SET sold_count = %s WHERE id = %s', (new_count, product_id))
            conn.commit()
    
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form.get('name')
    price = float(request.form.get('price', 0))
    
    if name and price >= 0:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute('INSERT INTO product (name, price) VALUES (%s, %s)', (name, price))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('DELETE FROM product WHERE id = %s', (product_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
