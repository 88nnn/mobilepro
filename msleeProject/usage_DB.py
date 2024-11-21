# from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import random
from datetime import datetime, timedelta

db = SQLAlchemy()

# Models
class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    mail = db.Column(db.String(50), unique=True, nullable=False)
    car_type = db.Column(db.String(10), unique=False, nullable=True)  # e.g.,
    # "Small", "Medium",
    # "Large"

class Product(db.Model):
    __tablename__ = "product"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    purchase_count = db.Column(db.Integer, default=0)
    repurchase_count = db.Column(db.Integer, default=0)

class Purchase(db.Model):
    __tablename__ = "purchase"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_repeat = db.Column(db.Boolean, default=False)

if __name__ == '__main__':
    # 데베 생성
    with app.app_context():
        db.create_all()
    app.run(debug=True)
