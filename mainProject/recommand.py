#html 화면과 연계해서 추천 상품에 강조 표시
from usage_DB import db, User, Product, Purchase
from datetime import datetime, timedelta, UTC
from collections import Counter
from itertools import combinations
# datetime 라이브러리로 현재시간을 받아올 수 있으며,
# timedelta 라이브러리로 datetime 객체의 더하기, 빼기를 수행할 수 있다.
# 출처: https://csshark.tistory.com/113 [컴퓨터하는 상어:티스토리]
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
utc_now = datetime.utcnow()

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from itertools import combinations

# 상품 조합 추천 딥러닝 알고리즘
def recommend_combination(user_id):
    # 1. 유저 구매 정보 및 차량 타입 가져오기
    user_purchases = Purchase.query.filter_by(user_id=user_id).all()
    user_car_type = User.query.get(user_id).car_type

    # 모든 상품 정보 가져오기
    products = Product.query.all()

    # 2~6개까지 가능한 모든 조합 생성
    all_combinations = []
    for r in range(2, len(products) + 1):
        for comb in combinations(products, r):
            # 상품 아이디 리스트 생성
            product_ids = [product.id for product in comb]

            # 조합에 해당하는 Purchase 데이터 필터링
            purchase_count = Purchase.query.filter(Purchase.product_ids.in_(product_ids)).count()
            # 조합에 해당하는 Product 데이터 필터링 및 평균 평점 계산
            average_rating = (
                db.session.query(func.avg(Product.average_rating))
                .filter(Product.id.in_(product_ids))
                .scalar()
            )
            average_rating = average_rating if average_rating is not None else 0
            all_combinations.append({
                "product_combination": ", ".join([product.name for product in comb]),
                "purchase_count": purchase_count,
                "rating": average_rating
            })

    # 2. 벡터화 (텍스트 기반 유사도 분석)
    product_texts = [comb["product_combination"] for comb in all_combinations]
    vectorizer = CountVectorizer()
    product_vectors = vectorizer.fit_transform(product_texts)

    # 유저가 구매한 상품들에 대해 벡터화
    user_products = ", ".join([Product.query.filter(Product.id.in_(p.product_ids)).all()[0].name for p in user_purchases])
    user_vector = vectorizer.transform([user_products])

    # 3. 유사도 계산
    similarity_scores = cosine_similarity(user_vector, product_vectors).flatten()

    # 4. 평점, 구매 횟수 가중치 반영
    for idx, comb in enumerate(all_combinations):
        comb["score"] = (
            similarity_scores[idx] * 0.5
            + comb["rating"] * 0.2
            + comb["purchase_count"] * 0.3
        )

    # 5. 같은 차종 사용자의 데이터 활용 (추가 가중치)
    same_car_users = User.query.filter_by(car_type=user_car_type).all()
    same_car_user_ids = [user.id for user in same_car_users]

    same_car_purchases = Purchase.query.filter(Purchase.user_id.in_(same_car_user_ids)).all()
    same_car_products = ", ".join([Product.query.filter(Product.id.in_(p.product_ids)).all()[0].name for p in same_car_purchases])
    same_car_vector = vectorizer.transform([same_car_products])

    same_car_similarity_scores = cosine_similarity(same_car_vector, product_vectors).flatten()
    for idx in range(len(all_combinations)):
        all_combinations[idx]["score"] += same_car_similarity_scores[idx] * 0.2

    # 6. 가장 평점이 높은 상품 추가 추천
    top_rated_product = Product.query.order_by(Product.average_rating.desc()).first()
    top_rated_product_recommendation = {
        "product_combination": top_rated_product.name,
        "rating": top_rated_product.average_rating,
        "score": 5.0  # 높은 점수로 추가
    }

    # 7. 결과 반환 (상위 2개 조합
    # + 가장 평점 높은 상품)
    recommendations = sorted(all_combinations, key=lambda x: x["score"], reverse=True)[:2]

    return top_rated_product_recommendation, recommendations

# 2주 전까지의 가장 자주 등장한 상품 조합을 찾는 함수
def get_weekly_top_product():
    # 2주 전 날짜 계산
    two_weeks_ago = datetime.now() - timedelta(weeks=2)

    # 2주 전까지의 구매 내역을 조회
    purchases = Purchase.query.filter(Purchase.timestamps >= two_weeks_ago).all()

    # 모든 product_ids 조합을 하나의 리스트로 합침
    all_combinations = []
    for purchase in purchases:
        # 각 purchase의 product_ids에서 가능한 모든 조합을 생성 (크기 2 이상)
        for r in range(2, len(purchase.product_ids) + 1):
            all_combinations.extend(combinations(purchase.product_ids, r))

    # 각 조합의 출현 빈도 계산
    combination_counter = Counter(all_combinations)

    # 가장 많이 등장한 조합을 반환
    most_frequent_combinations = combination_counter.most_common()

    return most_frequent_combinations

# 유저 개인의 최다 구매한 상품 조합들을 찾는 함수
def get_user_frequent_product(user_id):
    # 해당 user_id로 구매 내역을 조회
    purchases = Purchase.query.filter_by(user_id=user_id).all()

    # 모든 product_ids 조합을 하나의 리스트로 합침
    all_combinations = []
    for purchase in purchases:
        # 각 purchase의 product_ids에서 가능한 모든 조합을 생성 (크기 2 이상)
        for r in range(2, len(purchase.product_ids) + 1):
            all_combinations.extend(combinations(purchase.product_ids, r))

    # 각 조합의 출현 빈도 계산
    combination_counter = Counter(all_combinations)

    # 가장 많이 등장한 조합을 반환
    most_frequent_combinations = combination_counter.most_common()

    return most_frequent_combinations

"""
구매 내역 가져오기: Purchase.query.filter_by(user_id=user_id).all()를 사용해 해당 user_id에 해당하는 모든 구매 내역을 조회합니다.
product_ids 합치기: 각 구매 내역의 product_ids를 all_product_ids 리스트에 하나로 합칩니다.
빈도 계산: Counter를 사용해 각 상품 ID가 몇 번 등장하는지 세고, 이를 most_common() 메서드를 사용해 가장 많이 등장한 상품들을 구합니다.
결과 반환: 최다 구매 상품들의 배열을 반환합니다.
"""

"""
if __name__ == '__main__':
    user_id = 1
    print(recommend_combination(user_id))
    print(recommend_combination(user_id))
    print(get_weekly_top_product())
    print(get_user_frequent_product(user_id))


def get_highest_repurchase_product():
    return Product.query.order_by(Product.repurchase_count.desc()).first()

def get_top_product_by_car_type(car_type):
    users = User.query.filter_by(car_type=car_type).all()
    user_ids = [user.id for user in users]
    purchases = db.session.query(Purchase.product_id, db.func.count(Purchase.id)).\
                filter(Purchase.user_id.in_(user_ids)).\
                group_by(Purchase.product_id).\
                order_by(db.func.count(Purchase.id).desc()).first()
    return Product.query.get(purchases[0]) if purchases else None
"""