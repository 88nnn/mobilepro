from datetime import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import random
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recommendations.db'
db = SQLAlchemy(app)



# Models
class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    mail_address= db.Column(db.String(50), unique=True, nullable=False)
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


class CarWash1(db.Model):
    __tablename__ = "carwash1"
    id = db.Column(db.Integer, primary_key=True)
    user_mail = db.Column(db.String(50), db.ForeignKey('user.mail_address'),
                          nullable=False)
    reservation_date = db.Column(db.DateTime, default=datetime.utcnow,
                                 nullable=True, unique=False)

class CarWash2(db.Model):
    __tablename__ = "carwash2"
    id = db.Column(db.Integer, primary_key=True)
    user_mail = db.Column(db.String(50), db.ForeignKey('user.mail_address'),
                          nullable=False)
    reservation_date = db.Column(db.DateTime, default=datetime.utcnow,
                                 nullable=True, unique=False)

class CarWash3(db.Model):
    __tablename__ = "carwash3"
    id = db.Column(db.Integer, primary_key=True)
    user_mail = db.Column(db.String(50), db.ForeignKey('user.mail_address'),
                          nullable=False)
    reservation_date = db.Column(db.DateTime, default=datetime.utcnow,
                                 nullable=True, unique=False)

CAR_WASH_MODELS = {
    1: CarWash1,
    2: CarWash2,
    3: CarWash3,
}

if __name__ == '__main__':
    # 데베 생성
    with app.app_context():
        db.create_all()
    app.run(debug=True)
