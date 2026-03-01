from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3

app = Flask(__name__)
DB_PATH = 'cashier.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS product (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    products = conn.execute('SELECT * FROM product').fetchall()
    conn.close()
    return render_template('index.html', products=products)

@app.route('/analytics')
def analytics():
    conn = get_db()
    products_rows = conn.execute('SELECT * FROM product').fetchall()
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
    product = conn.execute('SELECT * FROM product WHERE id = ?', (product_id,)).fetchone()
    
    if product:
        new_count = max(0, product['sold_count'] + change)
        conn.execute('UPDATE product SET sold_count = ? WHERE id = ?', (new_count, product_id))
        conn.commit()
    
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form.get('name')
    price = float(request.form.get('price', 0))
    
    if name and price >= 0:
        conn = get_db()
        conn.execute('INSERT INTO product (name, price) VALUES (?, ?)', (name, price))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    conn = get_db()
    conn.execute('DELETE FROM product WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
