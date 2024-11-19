#html 화면과 연계해서 추천 상품에 강조 표시

def get_highest_repurchase_product():
    return Product.query.order_by(Product.repurchase_count.desc()).first()

def get_weekly_top_product():
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    purchases = db.session.query(Purchase.product_id, db.func.count(Purchase.id)).\
                filter(Purchase.timestamp >= one_week_ago).\
                group_by(Purchase.product_id).\
                order_by(db.func.count(Purchase.id).desc()).first()
    return Product.query.get(purchases[0]) if purchases else None

def get_top_product_by_car_type(car_type):
    users = User.query.filter_by(car_type=car_type).all()
    user_ids = [user.id for user in users]
    purchases = db.session.query(Purchase.product_id, db.func.count(Purchase.id)).\
                filter(Purchase.user_id.in_(user_ids)).\
                group_by(Purchase.product_id).\
                order_by(db.func.count(Purchase.id).desc()).first()
    return Product.query.get(purchases[0]) if purchases else None

def get_user_frequent_product(user_id):
    purchases = db.session.query(Purchase.product_id, db.func.count(Purchase.id)).\
                filter(Purchase.user_id == user_id).\
                group_by(Purchase.product_id).\
                order_by(db.func.count(Purchase.id).desc()).first()
    return Product.query.get(purchases[0]) if purchases else None
