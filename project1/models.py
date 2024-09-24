from flask_mysqldb import MySQL
from flask import Flask

app = Flask(__name__)
app.config.from_object('config.Config')

mysql = MySQL(app)

def get_all_products():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    cur.close()
    return products

def get_product_by_id(product_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products WHERE id = %s", [product_id])
    product = cur.fetchone()
    cur.close()
    return product
