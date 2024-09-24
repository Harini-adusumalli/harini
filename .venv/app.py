from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
import stripe
from models import get_all_products, get_product_by_id, mysql

app = Flask(__name__)
app.config.from_object('config.Config')

jwt = JWTManager(app)
stripe.api_key = app.config['STRIPE_SECRET_KEY']

# Product Routes
@app.route('/products', methods=['GET'])
def get_products():
    products = get_all_products()
    return jsonify(products)

@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = get_product_by_id(id)
    if product:
        return jsonify(product)
    else:
        return jsonify({"error": "Product not found"}), 404

# Authentication Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data['name']
    email = data['email']
    password = data['password']
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
    mysql.connection.commit()
    cur.close()
    
    return jsonify(message="User registered"), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
    user = cur.fetchone()
    cur.close()
    
    if user:
        access_token = create_access_token(identity=email)
        return jsonify(access_token=access_token)
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# Cart Routes
@app.route('/cart', methods=['POST'])
@jwt_required()
def add_to_cart():
    data = request.get_json()
    user_id = data['user_id']
    product_id = data['product_id']
    quantity = data['quantity']
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)", (user_id, product_id, quantity))
    mysql.connection.commit()
    cur.close()
    
    return jsonify(message="Product added to cart"), 201

@app.route('/cart', methods=['GET'])
@jwt_required()
def view_cart():
    user_id = request.args.get('user_id')
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM cart WHERE user_id = %s", [user_id])
    cart_items = cur.fetchall()
    cur.close()
    
    return jsonify(cart_items)

# Order Routes
@app.route('/orders', methods=['POST'])
@jwt_required()
def place_order():
    data = request.get_json()
    user_id = data['user_id']
    total_price = data['total_price']
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO orders (user_id, total_price) VALUES (%s, %s)", (user_id, total_price))
    mysql.connection.commit()
    cur.close()
    
    return jsonify(message="Order placed"), 201

# Payment Route using Stripe
@app.route('/payment', methods=['POST'])
@jwt_required()
def make_payment():
    data = request.get_json()
    amount = data['amount']
    token = data['token']
    
    try:
        charge = stripe.Charge.create(
            amount=int(amount * 100),  # amount in cents
            currency='usd',
            source=token,
            description='E-commerce payment'
        )
        return jsonify({"status": "Payment successful"}), 200
    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(port=5000, debug=True)
