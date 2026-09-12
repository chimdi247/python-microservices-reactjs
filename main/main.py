from dataclasses import dataclass
import os

from flask import Flask, jsonify, abort
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
import requests

from producer import publish

ADMIN_SERVICE_URL = os.environ.get('ADMIN_SERVICE_URL', 'http://admin:8000')

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    'SQLALCHEMY_DATABASE_URI', 'mysql://root:root@db-main/main'
)
CORS(app)

db = SQLAlchemy(app)


@dataclass
class Product(db.Model):
    id: int
    title: str
    image: str
    likes: int

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    title = db.Column(db.String(200))
    image = db.Column(db.String(200))
    likes = db.Column(db.Integer, default=0)


@dataclass
class ProductUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer)

    UniqueConstraint('user_id', 'product_id', name='user_product_unique')


@app.route('/api/products')
def index():
    return jsonify(Product.query.all())


@app.route('/api/products/<int:id>/like', methods=['POST'])
def like(id):
    req = requests.get(f'{ADMIN_SERVICE_URL}/api/user')
    json = req.json()

    try:
        productUser = ProductUser(user_id=json['id'], product_id=id)
        db.session.add(productUser)

        product = db.session.get(Product, id)
        if product is not None:
            product.likes = (product.likes or 0) + 1

        db.session.commit()

        publish('product_liked', id)
    except:
        db.session.rollback()
        abort(400, 'You already liked this product')

    return jsonify({
        'message': 'success'
    })


SAMPLE_PRODUCTS = [
    {'id': 1, 'title': 'Classic White Sneakers', 'image': 'https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=600&q=80'},
    {'id': 2, 'title': 'Leather Backpack', 'image': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&q=80'},
    {'id': 3, 'title': 'Wireless Headphones', 'image': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&q=80'},
]


def seed_sample_products():
    if Product.query.count() > 0:
        return
    for item in SAMPLE_PRODUCTS:
        db.session.add(Product(id=item['id'], title=item['title'], image=item['image'], likes=0))
    db.session.commit()
    print(f"Seeded {len(SAMPLE_PRODUCTS)} sample products.")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Creates tables if they don't already exist
        print("Database tables created successfully.")
        seed_sample_products()
    app.run(debug=True, host='0.0.0.0')
