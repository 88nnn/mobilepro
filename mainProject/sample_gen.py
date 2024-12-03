from IPython.utils.tz import utcnow
import random
from datetime import datetime, timedelta, UTC

from pyarrow import nulls

from usage_DB import db, User, Product, Purchase
import random
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import app

# ai 추천 알고리즘 적용을 위한 데모 구매 내역 랜덤 생성
def generate_sample_data():
    #
    users = [User(car_type=random.choice(["Small", "Medium", "Large"])) for _ in range(10)]
    #
    products = [Product(name=f"Product {i}") for i in range(1, 6)]
    # 생성된 유저와 상품 관련 데모 테이블 저장
    db.session.add_all(users + products)
    # 저장 내용 갱신
    db.session.commit()
    
    # 구매내역 생성(60개)
    start_date = datetime.utcnow() - timedelta(days=14)
    for _ in range(60):
        user = random.choice(users)
        product = random.choice(products)
        # 재구매 여부 확인
        is_repeat = Purchase.query.filter_by(user_id=user.id, product_id=product.id).count() > 0
        purchase = Purchase(
            user_id=user.id,
            product_id=product.id,
            timestamp=start_date + timedelta(days=random.randint(0, 13)),
            is_repeat=is_repeat
        )
        product.purchase_count += 1
        if is_repeat:
            product.repurchase_count += 1
        db.session.add(purchase)
    
    db.session.commit()

with app.app_context():
    generate_sample_data()
