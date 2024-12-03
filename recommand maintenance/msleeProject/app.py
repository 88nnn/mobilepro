# 세차창 예약 화면(UI-A-001, UI-A-002)
#
# 10w 세차장 목록 및 대기자 수 표시 구현
#
# 11w 세차장 예약 후 예약 정보와 예상 대기 시간 표시
#
# 12w 대기자 정보 업데이트 기능 추가
from flask import Flask, render_template, session, jsonify, request, redirect, \
    url_for, Response
from flask_sqlalchemy import SQLAlchemy

import os
import json
from usage_DB import db, CAR_WASH_MODELS, User, Product, Purchase

import cv2
import pytesseract
import numpy as np

import time
from sample_gen import generate_sample_data

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
    return redirect(url_for("car_wash_select"))


@app.route('/sessionInfo')
def sessionInfo():
    user_id = session.get('user_id')
    user_mail = session.get('user_mail')
    user_plate = session.get('user_plate')
    car_type = session.get('car_type')
    reserved_car_wash_id = session.get('reserved_car_wash_id')
    # selected_product = session.get('selected_product') 이거 두개는 로컬 스토리지에 저장됨
    # selected_Product_Id = session.get('selected_Product_Id')
    return (f"User Id: {user_id}<br> User Email: {user_mail}<br> User Plate:"
            f" {user_plate}<br> Car Type: {car_type}<br> Reserved Car Wash "
            f"Id: {reserved_car_wash_id} <br>")


# def car_wash_select()
#  - 세차장 기본 화면을 렌더링한다.

@app.route("/car_wash_select")
def car_wash_select():
    return render_template('car_wash_select.html')


car_wash_status = {
    1: {"waiting_count": 0, "wait_time": 0},
    2: {"waiting_count": 0, "wait_time": 0},
    3: {"waiting_count": 0, "wait_time": 0}

}


def get_waiting_info(car_wash_id):
    car_wash_model = CAR_WASH_MODELS.get(car_wash_id)
    if not car_wash_model:
        return {"waiting_count": 0, "wait_time": 0}
    waiting_count = db.session.query(car_wash_model).count()
    wait_time = waiting_count * 10  # 한 사람당 대기 시간 10분으로 계산
    return {"waiting_count": waiting_count, "wait_time": wait_time}


# user 등록
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = int(time.time())
        user_mail = request.form['mail']
        # new_user = User(id=user_id,
        #                 mail_address=user_mail
        #                 )
        session['user_id'] = user_id
        session['user_mail'] = user_mail
        # db.session.add(new_user)
        # db.session.commit()
        return render_template('registration_complete.html')
    return render_template('register.html')


@app.route('/registration_complete')
def registration_complete():
    return """<script>
    	window.location = document.referrer;
    	</script>"""


@app.route('/logout')
def logout():
    session.pop('user_mail', None)  # 세션에서 이메일 제거
    session.pop('user_id', None)
    session.pop('user_plate', None)
    session.pop('reserved_car_wash_id', None)
    session.pop('car_type', None)
    return render_template("logout.html")


@app.route("/update_waiting_info", methods=["POST"])
def update_waiting_info():
    car_wash_id = int(request.form.get("car_wash_id"))

    info = get_waiting_info(car_wash_id)

    response = {
        "success": True,
        "waiting_count": info["waiting_count"],
        "wait_time": info["wait_time"]
    }

    return jsonify(response)


def save_reservation(car_wash_model, email):
    new_reservation = car_wash_model(user_mail=email)
    db.session.add(new_reservation)
    db.session.commit()


# @app.route('/car_wash_reservation_new/<int:car_wash_id>', methods=['GET',
#                                                                    'POST'])
# def car_wash_reservation_new(car_wash_id):
#     car_wash_model = CAR_WASH_MODELS.get(car_wash_id)
#     if not car_wash_model:
#         return "세차장 정보가 없습니다.", 404
#     if request.method == 'POST':
#         email = session.get('user_mail')
#         save_reservation(car_wash_model, email)
#         session['reserved_car_wash_id'] = car_wash_id
#         return ("예약 완료")
#     else:
#        "carwashreservationnew오류"

# car_wash(car_wash_id)
@app.route('/car_wash_reservation/<int:car_wash_id>', methods=['GET', 'POST'])
@app.route('/car_wash/<int:car_wash_id>', methods=['GET', 'POST'])
def car_wash_reservation(car_wash_id):
    car_wash_model = CAR_WASH_MODELS.get(car_wash_id)
    if not car_wash_model:
        return "세차장 정보가 없습니다.", 404

    if request.method == 'POST':
        if 'user_mail' in session:
            email = session['user_mail']
            # save_reservations(car_wash_model, email)
            # new_reservation = car_wash_model(user_mail=email)
            # db.session.add(new_reservation)
            # db.session.commit()

            session['reserved_car_wash_id'] = car_wash_id
            print(f"세차장 {car_wash_id} 예약완료")
            reservation_status = f"세차장 {car_wash_id} 예약이 완료되었습니다!"
            return redirect(url_for('reservation_complete'))
        else:
            reservation_status = "로그인이 필요합니다."
    else:
        reservation_status = None

    waiting_info = get_waiting_info(car_wash_id)

    reservations = (db.session.query(car_wash_model.user_mail,
                                     car_wash_model.reservation_date).all())

    return render_template("car_wash.html",
                           waiting_count=waiting_info["waiting_count"],
                           wait_time=waiting_info["wait_time"],
                           car_wash_id=car_wash_id,
                           reservations=reservations,
                           reservation_status=reservation_status)


# 예약 완료 페이지
@app.route('/reservation_complete')
def reservation_complete():
    return render_template('reservation_complete.html')


# 차 기종 따로 추가
@app.route('/update_car_type', methods=['GET', 'POST'])
def update_car_type():
    if 'user_mail' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # 현재 세션의 user_mail을 가져와서
        # car_type이랑 같이 user_mail이 같은 User에 저장
        car_type = request.form['car_type']
        user_mail = session['user_mail']
        user = User.query.filter_by(mail_address=user_mail).first()
        if user:
            user.car_type = car_type
            db.session.commit()
            return redirect(
                url_for('다른 팀원 페이지 or 예약 완료 페이지'))  # 업데이트 후 세차장 선택 페이지로 리디렉션

    return render_template('update_car_type.html')


##############################################

##############################################

# API 사용내역 갱신 API
@app.route('/api/usage/<int:user_id>', methods=['GET'])
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
                "duration_seconds": purchase.duration_seconds,
                "cost": round(cost)
            })

    return jsonify({
        "usage_details": usage_details,
        "total_cost": round(total_cost)
    })


# 구매 정보 저장 API
@app.route('/api/save_purchase', methods=['POST'])
def save_purchase():
    try:
        data = request.json
        # user_id = data.get('user_id')
        user_id = session.get('user_id')
        product_id = data.get('product_id')
        if not user_id or not product_id:
            return jsonify({'error': 'Missing user_id or product_id'}), 400

        # 재구매 여부 확인
        is_repeat = Purchase.query.filter_by(user_id=user_id,
                                             product_id=product_id).count() > 0

##############
        # 세션에서 user_mail, car_type, user_id를 가져와서 UserDB에 추가
        user_mail = session.get('user_mail')
        car_type = session.get('car_type')
        # user db를 데베에 저장 (이민수)
        user = User.query.get(user_id)
        if not user:  # 유저가 없을 경우에만 새 유저 생성
             new_user = User(id=user_id, mail_address=user_mail,
                        car_type=car_type)
             db.session.add(new_user)
             db.session.commit()

        # 세션에서 car_wash_id도 가져와서 carwashDB에 추가
        # 홈화면으로 돌아가면 대기자가 갱신되어있음
        car_wash_id = session.get('reserved_car_wash_id')
        car_wash_model = CAR_WASH_MODELS.get(car_wash_id)
        save_reservation(car_wash_model, user_mail)
        # db.session.add()
        # Save the purchase to the database
        new_purchase = Purchase(user_id=user_id, product_id=product_id,
                                is_repeat=is_repeat)
        db.session.add(new_purchase)
        db.session.commit()
##############
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


##############################################

##############################################

# IP Webcam URL (휴대폰에서 IP Webcam을 실행하고 제공된 URL로 교체)
url = 'http:// example.com/video'  # 자신의 IP Webcam URL로 변경

# 웹캡 캡처
cap = cv2.VideoCapture(url)


# 번호판 인식 함수
def process_frame(frame):
    # 그레이스케일 변환
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 이미지 이진화 (노이즈를 줄이기 위해 블러처리 후 adaptiveThreshold 사용)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    adaptive_thresh = cv2.adaptiveThreshold(blurred, 255,
                                            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                            cv2.THRESH_BINARY, 11, 2)

    # 외곽선 찾기
    contours, _ = cv2.findContours(adaptive_thresh, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        # 너무 작은 컨투어는 제외
        if cv2.contourArea(contour) < 1000:
            continue

        # 각 컨투어에 대해 직사각형 테두리 그리기
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h  # 번호판의 비율

        # 번호판과 비슷한 비율(너비가 높이보다 몇 배 긴 형태)을 찾기
        if aspect_ratio > 2 and aspect_ratio < 6:
            # 초록색 테두리로 번호판 영역을 표시
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0),
                          3)  # 초록색 테두리

            # 번호판 영역 추출
            plate = frame[y:y + h, x:x + w]

            # Tesseract OCR로 번호판 텍스트 추출 (한글+영어 설정)
            text = pytesseract.image_to_string(plate,
                                               config='--psm 8 -l kor+eng')  # 한글+영어 설정

            return text.strip()

    return None


# 웹캡 스트리밍을 위한 함수
def gen_frames():
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 번호판 인식 처리
        text = process_frame(frame)
        if text:
            cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 0, 255), 2)  # 번호판 텍스트 표시

        # 인식된 프레임을 JPEG 형식으로 변환
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# 기본 페이지 (스트리밍 페이지)
@app.route('/index.html')
def index():
    return render_template('index.html', result=None)


# 스트리밍 라우트
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# 번호판 인식 버튼 클릭 시
@app.route('/recognize', methods=['POST'])
def recognize():
    ################################## 확인용 #####################
    ################################수정하실 때 주석처리하세요########
    text = '1234가나다'
    session['user_plate'] = text
    return jsonify({'result': 'success', 'plate': text})
    ##########################################################
    ##################################################
    ret, frame = cap.read()
    if not ret:
        return jsonify({'result': 'failure'})

    # 번호판 인식
    text = process_frame(frame)
    if text:
        # session['user_plate'] = text
        return jsonify({'result': 'success', 'plate': text})
    else:
        return jsonify({'result': 'failure'})


# 재시도 페이지 (번호판 인식 실패 시)
@app.route('/retry', methods=['GET'])
def retry():
    return render_template('index.html')


# 고객센터 페이지
@app.route('/contact', methods=['GET'])
def contact():
    return render_template('contact.html')

#########################################

#########################################
# 제품 선택 화면
@app.route('/product_selection')
def product_selection():
    return render_template('product_selection.html', user_id=session['user_id'])


@app.route('/option_selection', methods=['GET'])
def option_selection():
    # selected_product_id = session.get('selected_product_id', None)
    # return render_template('option_selection.html',
    #                        selected_product_id=selected_product_id)
    return render_template('option_selection.html')


@app.route('/save-selection', methods=['POST'])
def save_selection():
    # 요청에서 데이터 추출
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')

    # 선택된 제품을 저장하는 로직 구현
    # 필요하다면 Purchase 테이블 등의 모델에 저장
    new_purchase = Purchase(user_id=user_id, product_id=product_id)
    db.session.add(new_purchase)
    db.session.commit()

    return jsonify(
        {"success": True, "message": "Selected product saved to database."})


@app.route('/payment_service')
def payment_service():
    return render_template('payment_service.html')


@app.route('/end_service')
def end_service():
    return render_template('end_service.html')


@app.route('/usage_summary')
def usage_summary():
    return render_template('usage_summary.html')


if __name__ == '__main__':
    # 데베 생성
    try:
        with app.app_context():
            db.create_all()
            print("Database initialized")
            # generate_sample_data()
            # print("Sample data generated")
    except Exception as e:
        print(f"Failed to initailize the database{e}")
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
