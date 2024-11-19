from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import random
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recommendations.db'
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    car_type = db.Column(db.String(10))  # e.g., "Small", "Medium", "Large"
    mail_address = db.Colum(db.string(30))

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    purchase_count = db.Column(db.Integer, default=0)
    repurchase_count = db.Column(db.Integer, default=0)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_repeat = db.Column(db.Boolean, default=False)

# 데베 생성
with app.app_context():
    db.create_all()
