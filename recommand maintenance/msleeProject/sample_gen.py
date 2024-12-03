from usage_DB import User, Product, Purchase
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


def generate_sample_data():
    users = [User(car_type=random.choice(["Small", "Medium", "Large"])) for _ in
             range(10)]
    products = [Product(name=f"Product {i}") for i in range(1, 6)]
    db.session.add_all(users + products)
    db.session.commit()

    # 구매내역 생성(60)
    start_date = datetime.utcnow() - timedelta(days=14)
    for _ in range(60):
        user = random.choice(users)
        product = random.choice(products)
        is_repeat = random.choice([True, False])
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


if __name__ == '__main__':
    with app.app_context():
        generate_sample_data()
