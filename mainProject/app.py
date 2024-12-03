# 세차창 예약 화면(UI-A-001, UI-A-002)
#
# 10w 세차장 목록 및 대기자 수 표시 구현
#
# 11w 세차장 예약 후 예약 정보와 예상 대기 시간 표시
#
# 12w 대기자 정보 업데이트 기능 추가
from flask import Flask, render_template, session, jsonify, request, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
import os
import json
from usage_DB import db, CAR_WASH_MODELS, User, Product, Purchase, seed_data
from recommand import recommend_combination, get_weekly_top_product, get_user_frequent_product
from datetime import datetime, timedelta
# timestamp 변환 예시
timestamp_str = datetime.now().isoformat()  # ISO 형식으로 변환

import cv2
import pytesseract
import numpy as np

import time
app = Flask(__name__)

# usage_DB.py내의 데이터베이스가
# recommendations.db라는 이름으로 database파일 아래에 생성됩니다.
# base_dir은 현재 디렉토리의 절대 경로입니다.
#
# - base_dir: 절대 경로
# - db_path: 데이터베이스 경로
# - app.config
# - SECRET KEY
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, './database/recommendations.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path

app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

secret_file = os.path.join(base_dir, 'secret_json')
with open(secret_file) as f:
    secrets = json.loads(f.read())
app.config['SECRET_KEY'] = secrets['SECRET_KEY']

db.init_app(app)

# def home()
#  - 세차장 기본 화면 /car_wash_select로 이동한다.
@app.route("/")
def home():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for("update_recommendations", user_id=1))
    return redirect(url_for("update_recommendations", user_id=user_id))
    

##############################################
##############################################


# 사용자 ID를 세션에서 가져오는 API
@app.route('/app/get_user_id', methods=['GET'])
def get_user_id():
    user_id = session.get('user_id')  # 세션에서 user_id 가져오기
    if user_id is None:
        jsonify({"error": "사용자가 로그인되지 않았습니다."}), 401
        return redirect(url_for('login_page'))
    return jsonify({"user_id": user_id})


@app.route('/update_recommendations/<int:user_id>', methods=['GET'])
def update_recommendations(user_id):
    # recommand.py에서 가공된 추천 정보 불러오기
    weekly_top_product = get_weekly_top_product()
    frequent_product = get_user_frequent_product(user_id)
    top_rated_product_recommendation, recommendations = recommend_combination(user_id)

    # 2. 추천 상품 조합을 상품명 리스트로 변환
    # recommended_product_ids = [comb["product_combination"] for comb in recommendations]
    # 추천 내역을 화면 템플릿에 출력
    recommended_products = [
        {
            "name": "고객님의 단골상품",
            "product": frequent_product.name if frequent_product else None,
            "description": frequent_product.description if frequent_product else "기본 설명 없음",
            "style": "red-dashed"
        },
        {
            "name": "차 관리 최적 상품 1",
            "product": recommendations[0]["product_combination"] if recommendations else None,
            "description": f"평점: {recommendations[0]['rating']:.1f}" if recommendations else "기본 설명 없음",
            "style": "blue-solid"
        },
        {
            "name": "차 관리 최적 상품 2",
            "product": recommendations[1]["product_combination"] if len(recommendations) > 1 else None,
            "description": f"평점: {recommendations[1]['rating']:.1f}" if len(recommendations) > 1 else "기본 설명 없음",
            "style": "blue-dashed"
        },
        {
            "name": "평점 최고 상품",
            "product": top_rated_product_recommendation.name if top_rated_product_recommendation else None,
            "description": top_rated_product_recommendation.description if top_rated_product_recommendation else "기본 설명 없음",
            "style": "red-solid"
        },
        {
            "name": "이번 주의 추천 상품",
            "product": weekly_top_product.name if weekly_top_product else None,
            "description": weekly_top_product.description if weekly_top_product else "기본 설명 없음",
            "style": "black-solid"
        },
    ]
    valid_products = [p for p in recommended_products if p.get("product")]
    print(valid_products)  # 전달된 데이터 구조 식별용 코드
    return render_template('product_selection.html', recommended_products=valid_products)

# 구매 정보 저장 API
@app.route('/app/save_purchase', methods=['POST'])
def save_purchase():
    try:
        data = request.get_json() #request.json()
        user_id = data.get('user_id')
        product_id = data.get('product_id')
        timestamp = data.get('timestamp')
        duration_seconds = data.get('duration_seconds')

        if not user_id or not product_id:
            return jsonify({"error": "필수 정보가 누락되었습니다."}), 400

        # 재구매 여부 확인
        is_repeat = Purchase.query.filter_by(user_id=user_id, product_id=product_id).count() > 0

        # 데베에 구매내역 저장
        new_purchase = Purchase(
            user_id=user_id,
            product_id=product_id,
            timestamp=datetime.utcfromtimestamp(timestamp / 1000),  # 밀리초를 초로 변환
            duration_seconds=duration_seconds or 0,  # duration_seconds는 선택적
            is_repeat=is_repeat
        )
        db.session.add(new_purchase)
        db.session.commit()

        # 구매횟수와 재구매횟수를 갱신
        product = Product.query.get(product_id)
        if product:
            product.purchase_count += 1
            if is_repeat:
                product.repurchase_count += 1
            db.session.commit()

        return jsonify({'message': 'Purchase saved successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 사용내역 조회 API
@app.route('/app/usage/<int:user_id>', methods=['GET'])
def get_usage_details(user_id):
    purchases = Purchase.query.filter_by(user_id=user_id).all()
    usage_details = []
    total_cost = 0

    for purchase in purchases:
        product = Product.query.get(purchase.product_id)
        if product:
            cost = (product.price_per_minute / 60) * purchase.duration_seconds
            total_cost += cost
            usage_details.append({
                "product_name": product.name,
                "timestamp": purchase.timestamp.isoformat(),  # 타임스탬프 ISO 형식으로 반환
                "duration_seconds": purchase.duration_seconds,
                "cost": round(cost)
            })

    return jsonify({
        "usage_details": usage_details,
        "total_cost": round(total_cost)
    })

@app.route('/app/rate_product', methods=['POST'])
def rate_product():
    try:
        data = request.json
        product_id = data.get('product_id')
        rating = data.get('rating')  # 1~5 범위의 평점

        if not product_id or rating is None:
            return jsonify({'error': 'Missing product_id or rating'}), 400

        if not (1 <= rating <= 5):
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400

        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # 평점 업데이트
        total_rating = product.average_rating * product.rating_count + rating
        product.rating_count += 1
        product.average_rating = total_rating / product.rating_count

        db.session.commit()
        return jsonify({'message': 'Rating saved successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# HTML 페이지 렌더링
@app.route('/rate_product', methods=['GET'])
def rate_product_page():
    products = Product.query.all()
    return render_template('rate_product.html', products=products)

# HTML에서 평점 제출 처리
@app.route('/submit_rating', methods=['POST'])
def submit_rating():
    try:
        product_id = request.form.get('product_id')
        rating = float(request.form.get('rating'))

        if not product_id or not (1 <= rating <= 5):
            return jsonify({'error': 'Invalid data'}), 400

        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # 평점 업데이트
        total_rating = product.average_rating * product.rating_count + rating
        product.rating_count += 1
        product.average_rating = total_rating / product.rating_count

        db.session.commit()
        return jsonify({'message': 'Rating submitted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # 데베 생성
    try:
        with app.app_context():
            #db.create_all()
            seed_data()
            print("Database initialized")
    except Exception as e:
        print(f"Failed to initailize the database{e}")
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000)