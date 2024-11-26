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
from usage_DB import db, CAR_WASH_MODELS, User, Product, Purchase

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
    return redirect(url_for("car_wash_select"))


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

        new_user = User(id=user_id,
                        mail_address=user_mail
                        )
        session['user_mail'] = user_mail
        db.session.add(new_user)
        db.session.commit()
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
            new_reservation = car_wash_model(user_mail=email)
            db.session.add(new_reservation)
            db.session.commit()
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
    # reservations = (db.session.query(car_wash_model, User)
    #                 .join(User, car_wash_model.user_mail == User.mail)
    #                 .add_columns(car_wash_model.reservation_date, User.mail)
    #                 .all())

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
@app.route('/update_car_type', methods = ['GET', 'POST'])
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
        user_id = data.get('user_id')
        product_id = data.get('product_id')

        if not user_id or not product_id:
            return jsonify({'error': 'Missing user_id or product_id'}), 400

        # 재구매 여부 확인
        is_repeat = Purchase.query.filter_by(user_id=user_id, product_id=product_id).count() > 0

        # Save the purchase to the database
        new_purchase = Purchase(user_id=user_id, product_id=product_id, is_repeat=is_repeat)
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

##############################################
##############################################

# IP Webcam URL (휴대폰에서 IP Webcam을 실행하고 제공된 URL로 교체)
url = 'http:// example.com/video'  # 자신의 IP Webcam URL로 변경

# 웹캡 캡처
cap = cv2.VideoCapture(url)


# 번호판 인식 함수
def process_frame(frame):
    # 이미지를 그레이스케일로 변환
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Otsu의 이진화 방법을 사용하여 이진 이미지 생성
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 윤곽선 찾기
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        if cv2.contourArea(contour) < 1000:
            continue

        # 윤곽선의 경계 사각형을 구함
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h

        # 번호판과 비슷한 비율을 가진 영역을 찾음
        if aspect_ratio > 2 and aspect_ratio < 6:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # 번호판 영역을 잘라내어 OCR로 텍스트를 추출
            plate = frame[y:y + h, x:x + w]
            text = pytesseract.image_to_string(plate,
                                               config='--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789')

            return text.strip()
    return None


# 웹캠 스트리밍을 위한 함수
def gen_frames():
    frame_skip = 5  # 몇 프레임마다 인식할지 설정 (5프레임마다 한번 인식)
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 일정 간격마다 번호판 인식
        if frame_count % frame_skip == 0:
            text = process_frame(frame)
            if text:
                cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 0, 255), 2)

        frame_count += 1

        # 프레임을 JPEG 형식으로 인코딩하여 전송
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
    # 웹캠에서 현재 프레임을 읽어 인식 처리
    ret, frame = cap.read()
    if not ret:
        return jsonify({'result': 'failure'})

    # 번호판 인식
    text = process_frame(frame)
    if text:
        return jsonify({'result': 'success', 'plate': text})
    else:
        return jsonify({'result': 'failure'})


# 번호판 인식 실패 시 재시도 및 고객센터 문의
@app.route('/retry', methods=['POST'])
def retry():
    return redirect(url_for('index'))


# 고객센터 문의 페이지 (실제 문의 페이지로 연결할 수 있음)
@app.route('/contact_support')
def contact_support():
    return render_template('contact_support.html')


# 상품 선택 화면 (상품 선택 화면은 다른 팀원이 작성한 페이지로 연결)
@app.route('/product_selection')
def product_selection():
    return redirect(
        'http://your-team-member-product-selection-url')  # 다른 팀원의 URL로 변경


if __name__ == '__main__':
    # 데베 생성
    try:
        with app.app_context():
            db.create_all()
            print("Database initialized")
    except Exception as e:
        print(f"Failed to initailize the database{e}")
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000)