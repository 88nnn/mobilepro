# 세차창 예약 화면(UI-A-001, UI-A-002)
#
# 10w 세차장 목록 및 대기자 수 표시 구현
#
# 11w 세차장 예약 후 예약 정보와 예상 대기 시간 표시
#
# 12w 대기자 정보 업데이트 기능 추가


from flask import Flask, render_template, jsonify, request, session
from flask_wtf import FlaskForm
from flask import redirect
from flask import url_for
# from forms import ReservationForm

import os
import json
from usage_DB import db
from datetime import datetime

app = Flask(__name__)

""" 
usage_DB.py내의 데이터베이스가
recommendations.db라는 이름으로 database파일 아래에 생성됩니다.
base_dir은 현재 디렉토리의 절대 경로입니다.

- base_dir: 절대 경로
- db_path: 데이터베이스 경로
- app.config
- SECRET KEY 

작성자: 이민수
2024-11-17
"""
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, './database/recommendations.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path

# 비지니스 로직이 끝날 때 Commit 실행(DB반영)
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

# 수정 사항에 대한 TRACK
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# SECRET_KEY
secret_file = os.path.join(base_dir, 'secret_json')  # secrets.json파일 위치를 명시
with open(secret_file) as f:
    secrets = json.loads(f.read())['SECRET_KEY']
app.config['SECRET_KEY'] = secrets
# app.config['SECRET_KEY'] = 'SECRET_KEY_ABC'

db.init_app(app)


@app.route("/")
def home():
    return render_template('home.html')


@app.route("/car_wash_select")
def car_wash_select():
    return render_template('car_wash_select.html')


car_wash_status = {
    1: {"waiting_count": 10, "wait_time": 15},
    2: {"waiting_count": 20, "wait_time": 30},
    3: {"waiting_count": 30, "wait_time": 45}

}


@app.route("/car_wash_reservation/<int:car_wash_id>")
def car_wash(car_wash_id):
    if car_wash_id in car_wash_status:
        car_wash = car_wash_status[car_wash_id]
        return render_template("car_wash.html",
                               waiting_count=car_wash["waiting_count"],
                               wait_time=car_wash["wait_time"],
                               car_wash_id=car_wash_id)
    else:
        return "세차장 정보가 없습니다.", 404


@app.route('/reserve_car_wash', methods=['POST'])
def reserve_car_wash():
    car_wash_id = int(request.form.get('car_wash_id'))
    if car_wash_id in car_wash_status:
        reservation_status = f"세차장 {car_wash_id} 예약이 완료되었습니다! "
        car_wash = car_wash_status[int(car_wash_id)]
        car_wash["waiting_count"] += 1
        car_wash["wait_time"] += 5
        return render_template('car_wash.html',
                               reservation_status=reservation_status,
                               waiting_count=car_wash_status[int(car_wash_id)][
                                   "waiting_count"],
                               wait_time=car_wash_status[int(car_wash_id)][
                                   "wait_time"],
                               car_wash_id=car_wash_id)
    else:
        return render_template("car_wash.html",
                               reservation_status="예약 실패",
                               waiting_count=car_wash_status[int(car_wash_id)]
                               ["waiting_count"],
                               wait_time=car_wash_status[int(car_wash_id)][
                                   "wait_time"],
                               car_wash_id=car_wash_id)

    # # db에 정보 삽입


# @app.route('/insert', methods=['POST'])
# def insert():
#     # db
#     return


# # 예약자 추가
# @app.route("/reservationabc", methods=['GET', 'POST'])
# def Reservation_add():
#     form = ReservationForm()
#     if form.validate_on_submit():
#         # 메일이나 아이디나 그런거 받아올거 아래에 적을것
#         # 그냥 아이디만 받아와서 조회해도 될 듯
#         abc = request.form['abc']
#         # 이거 근데 시간을 어떤식으로 리턴하는건지 모르겠네
#         date = datetime.today()
#
#         # 그다음에 삽입하는 코드
#
#         return redirect(url_for('reservation_complete'))
#     return render_template('home.html')

# 로그인 페이지
@app.route('/signup')
def signup():
    return render_template('signup.html')


# 예약 페이지
@app.route('/car_wash_reservation', methods=['POST'])
def car_wash_reservation():
    # 세차장 예약 로직
    return render_template('car_wash_reservation_NOT_USE.html')


# 대기자 확인 페이지
@app.route('/waitlist')
def waitlist():
    return render_template('waitlist.html')


# 예약 완료
@app.route('/reservation/complete')
def reservation_complete():
    return render_template('reservation_complete.html')


# 예약 실패
@app.route('/reservation/failed')
def reservation_failed():
    return render_template('reservation_failed.html')


if __name__ == '__main__':
    # 데베 생성
    with app.app_context():
        db.create_all()
    app.run(debug=True)
