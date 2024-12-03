from IPython.utils.tz import utcnow
import random
from datetime import datetime, timedelta, UTC
from future.backports.datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pygments.lexer import default
# timestamp 변환 예시
timestamp_str = datetime.now().isoformat()  # ISO 형식으로 변환

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recommendations.db'
db = SQLAlchemy(app)

# Models
# 이용자 관련 정보를 다루는 테이블
class User(db.Model):
    __tablename__ = "user"
    # 유저 등록 id, int(time.time())으로 어느 시간대인지에 따라 부여
    id = db.Column(db.Integer, primary_key=True)
    # 유저 이메일 정보(50자 이내), 가입 시 유저로부터 습득
    mail_address = db.Column(db.String(50), unique=True, nullable=False)

    car_type = db.Column(db.String(10), unique=False, nullable=True)

# 상품(및 구매회수) 관련 정보를 다루는 테이블
class Product(db.Model):
    __tablename__ = "product"
    # 상품 식별 id, 한 상품당 하나씩 부여, 주로 호출용.
    id = db.Column(db.Integer, primary_key=True)
    # 상품명, 식별용.
    name = db.Column(db.String(50), nullable=False, unique=True)
    # 총 구매 회수, Product 모델의 id가 한 번 호출될 때마다 증가++
    purchase_count = db.Column(db.Integer, default=0)
    # 재 구매 회수
    repurchase_count = db.Column(db.Integer, default=0)
    # Purchase의 is_repeat과 같이 증가
    # is_repeat에서 user_id와 product_id를 필터로 Purchase를 쿼리해서, 같은 쿼리가 하나라도 있으면 증가++
    cost = db.Column(db.Integer, default=0)
    average_rating = db.Column(db.Float, default=0.0)  # 평균 평점
    rating_count = db.Column(db.Integer, default=0) # 평점 수

    # 읽기 전용 속성으로 초기화
    def __init__(self, id, name, cost):
        self.id = id
        self.name = name
        self.cost = cost

# 구매(명세서) 관련 정보를 다루는 테이블
class Purchase(db.Model):
    __tablename__ = "purchase"
    # 사용 내역 id, 몇번째 사용 내역인지에 따라 순서대로 부여
    id = db.Column(db.Integer, primary_key=True)
    # 유저 등록 id 삽입
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # 상품 식별 id 삽입
    product_ids = db.Column(db.JSON, nullable=False)
    # 총 구매 시간대 저장, timestamp=start_date + timedelta(days=random.randint(0, 13))
    timestamps = db.Column(db.JSON, nullable=False)
    # 재구매 여부 확인
    is_repeat = db.Column(db.Boolean, default=False)
    durations = db.Column(db.JSON, nullable=False)
    all_cost = db.Column(db.Integer, default=0)

# 1번째 세차장
class CarWash1(db.Model):
    __tablename__ = "carwash1"
    id = db.Column(db.Integer, primary_key=True)
    user_mail = db.Column(db.String(50), db.ForeignKey('user.mail_address'),
                          nullable=False)
    reservation_date = db.Column(db.DateTime, default=datetime.utcnow,
                                 nullable=True, unique=False)
# 2번째 세차장
class CarWash2(db.Model):
    __tablename__ = "carwash2"
    id = db.Column(db.Integer, primary_key=True)
    user_mail = db.Column(db.String(50), db.ForeignKey('user.mail_address'),
                          nullable=False)
    reservation_date = db.Column(db.DateTime, default=datetime.utcnow,
                                 nullable=True, unique=False)
# 3번째 세차장
class CarWash3(db.Model):
    __tablename__ = "carwash3"
    id = db.Column(db.Integer, primary_key=True)
    user_mail = db.Column(db.String(50), db.ForeignKey('user.mail_address'),
                          nullable=False)
    reservation_date = db.Column(db.DateTime, default=datetime.utcnow,
                                 nullable=True, unique=False)
# 전체 세차장(3개) 테이블 모음
CAR_WASH_MODELS = {
    1: CarWash1,
    2: CarWash2,
    3: CarWash3,
}

# 초기 데이터 추가 함수
def seed_data():
    db.drop_all()
    db.create_all()

    # Product 데이터 추가
    products = [
        Product(id=0, name="진공청소기", cost=2),
        Product(id=1, name="보통 수압", cost=7),
        Product(id=2, name="고수압", cost=8),
        Product(id=3, name="에어건", cost=2),
        Product(id=4, name="폼건", cost=10),
        Product(id=5, name="거품솔 별도 대여", cost=3)
    ]
    db.session.add_all(products)

    # User 데이터 추가
    users = [
        User(id=i, mail_address=f"User{i}@hansung.com", car_type=random.choice(["Small", "Medium", "Large"]))
        for i in range(1, 11)
    ]
    db.session.add_all(users)

    # Purchase 데이터 추가
    start_date = datetime.now() - timedelta(days=14)  # 2주 전 시작
    for _ in range(60):  # 60개의 구매 데이터 생성
        user = random.choice(users)
        purchased_products = random.sample(products, random.randint(1, 6))  # 1~6개 상품 중복 없이 선택
        total_cost = 0
        durations = []
        for product in purchased_products:
            duration_seconds = random.randint(30, 1200)  # 30초~20분
            is_repeat = Purchase.query.filter(Purchase.user_id == user.id,
                                              Purchase.product_ids.contains([product.id])).count() > 0
            total_cost += duration_seconds * product.cost
            durations.append(duration_seconds)
        purchase = Purchase(
            user_id=user.id,
            product_ids=[product.id for product in purchased_products], # 여러 상품 id(옵션)를 배열로 저장
            timestamps = (start_date + timedelta(days=random.randint(0, 13))).isoformat(),  # ISO 형식 문자열로 변환
            is_repeat=is_repeat,
            durations=durations,  # 각 상품에 대한 시간을 배열로 저장
            all_cost = total_cost
        )
        db.session.add(purchase)

        # Product의 purchase_count 및 repurchase_count 업데이트
        for product in purchased_products:
            product.purchase_count += 1
            if is_repeat:
                product.repurchase_count += 1
            # 평점 갱신 (랜덤으로 1~5 평점 추가)
            random_rating = random.randint(1, 5)
            product.average_rating = (
                (product.average_rating * product.rating_count + random_rating) / (product.rating_count + 1)
            )
            product.rating_count += 1

    db.session.commit()
"""
if __name__ == '__main__':
    ## Flask 앱 컨텍스트 내에서 실행
    with app.app_context():
        #db.drop_all()  # 기존 테이블 삭제
        #db.create_all()  # 새로운 테이블 생성
        # 초기 상품Product 데이터 설정
        seed_data()
        #db.session.commit()
    app.run(debug=True)
"""



