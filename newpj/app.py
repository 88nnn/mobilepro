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

# 데이터베이스 경로 설정
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, './database/recommendations.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path

# SQLAlchemy 설정
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 비밀 키 설정 (외부 JSON 파일에서 로드)
secret_file = os.path.join(base_dir, 'secret_json')
with open(secret_file) as f:
    secrets = json.loads(f.read())
app.config['SECRET_KEY'] = secrets['SECRET_KEY']

# 데이터베이스 초기화
db.init_app(app)

# 기본 페이지 (세차장 선택 페이지로 리디렉션)
@app.route("/")
def home():
    return redirect(url_for("car_wash_select"))

# 세차장 선택 화면 렌더링
@app.route("/car_wash_select")
def car_wash_select():
    return render_template('car_wash_select.html')

# 세차장 대기 정보 업데이트
car_wash_status = {
    1: {"waiting_count": 0, "wait_time": 0},
    2: {"waiting_count": 0, "wait_time": 0},
    3: {"waiting_count": 0, "wait_time": 0}
}

# 대기 정보 가져오는 함수
def get_waiting_info(car_wash_id):
    car_wash_model = CAR_WASH_MODELS.get(car_wash_id)
    if not car_wash_model:
        return {"waiting_count": 0, "wait_time": 0}
    waiting_count = db.session.query(car_wash_model).count()
    wait_time = waiting_count * 10  # 한 사람당 대기 시간 10분으로 계산
    return {"waiting_count": waiting_count, "wait_time": wait_time}

# 유저 등록 페이지
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = int(time.time())  # 유저 ID는 현재 시간을 사용
        user_mail = request.form['mail']

        # 새로운 유저 데이터베이스에 추가
        new_user = User(id=user_id, mail_address=user_mail)
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

# 로그아웃 처리
@app.route('/logout')
def logout():
    session.pop('user_mail', None)  # 세션에서 이메일 제거
    return render_template("logout.html")

# 대기 정보 업데이트 API
@app.route("/update_waiting_info", methods=["POST"])
def update_waiting_info():
    car_wash_id = int(request.form.get("car_wash_id"))

    # 대기 정보 가져오기
    info = get_waiting_info(car_wash_id)

    response = {
        "success": True,
        "waiting_count": info["waiting_count"],
        "wait_time": info["wait_time"]
    }

    return jsonify(response)

# 세차장 예약 처리
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

    reservations = db.session.query(car_wash_model.user_mail, car_wash_model.reservation_date).all()

    return render_template("car_wash.html", waiting_count=waiting_info["waiting_count"],
                           wait_time=waiting_info["wait_time"], car_wash_id=car_wash_id,
                           reservations=reservations, reservation_status=reservation_status)

# 예약 완료 페이지
@app.route('/reservation_complete')
def reservation_complete():
    return render_template('reservation_complete.html')

# 차량 종류 업데이트 페이지
@app.route('/update_car_type', methods=['GET', 'POST'])
def update_car_type():
    if 'user_mail' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        car_type = request.form['car_type']
        user_mail = session['user_mail']
        user = User.query.filter_by(mail_address=user_mail).first()
        if user:
            user.car_type = car_type
            db.session.commit()
            return redirect(url_for('다른 팀원 페이지 or 예약 완료 페이지'))
    return render_template('update_car_type.html')

# IP Webcam URL (자신의 IP Webcam URL로 변경)
url = 'http://192.168.0.8:8080/video'

# 웹캡 캡처
cap = cv2.VideoCapture(url)

# 번호판 인식 함수
def process_frame(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    adaptive_thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    contours, _ = cv2.findContours(adaptive_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        if cv2.contourArea(contour) < 1000:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h
        if aspect_ratio > 2 and aspect_ratio < 6:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
            plate = frame[y:y + h, x:x + w]
            text = pytesseract.image_to_string(plate, config='--psm 8 -l kor+eng')

            return text.strip()
    return None

# 웹캡 스트리밍을 위한 함수
def gen_frames():
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        text = process_frame(frame)
        if text:
            cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

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
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# 번호판 인식 버튼 클릭 시
@app.route('/recognize', methods=['POST'])
def recognize():
    ret, frame = cap.read()
    if not ret:
        return jsonify({'result': 'failure'})

    text = process_frame(frame)
    if text:
        return jsonify({'result': 'success', 'plate': text})
    else:
        return jsonify({'result': 'failure'})

# 번호판 인식 실패 시 재시도 페이지
@app.route('/retry', methods=['GET'])
def retry():
    return render_template('index.html')

# 고객센터 페이지
@app.route('/contact', methods=['GET'])
def contact():
    return render_template('contact.html')

# 상품 선택 화면 (상품 선택 화면은 다른 팀원 작성한 페이지로 연결)
@app.route('/product_selection')
def product_selection():
    plate_number = request.args.get('plate_number')
    if plate_number:
        return render_template('product_selection.html', plate_number=plate_number)  # 상품 선택 페이지로 렌더링
    else:
        return jsonify({'error': '번호판 번호가 필요합니다.'}), 400

# 수동 번호 입력 처리
@app.route('/manual_entry', methods=['POST'])
def manual_entry():
    plate_number = request.form.get('plate_number')
    if plate_number:
        # 번호판 처리 후 상품선택 페이지로 리디렉션
        return render_template('product_selection.html', plate_number=plate_number)
    return jsonify({'error': '번호판 번호가 필요합니다.'}), 400

if __name__ == '__main__':
    # 데이터베이스 초기화
    try:
        with app.app_context():
            db.create_all()  # 데이터베이스 테이블 생성
            print("Database initialized")
    except Exception as e:
        print(f"Failed to initialize the database: {e}")

    # Flask 서버 실행
    app.run(host='0.0.0.0', port=5000)

