# 세차창 예약 화면(UI-A-001, UI-A-002)
#
# 10w 세차장 목록 및 대기자 수 표시 구현
#
# 11w 세차장 예약 후 예약 정보와 예상 대기 시간 표시
#
# 12w 대기자 정보 업데이트 기능 추가


from flask import Flask, render_template, jsonify, request, session
from flask import redirect, url_for

import os
import json
from usage_DB import db, User, Product, Purchase
from datetime import datetime
import random
from datetime import datetime, timedelta
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

# 로직이 끝날 때 Commit 실행(DB반영)
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

# 수정 사항 추적
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Load SECRET_KEY
secret_file = os.path.join(base_dir, 'secret_json')  # secrets.json파일 위치를 명시
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


# car_wash(car_wash_id)
#  - car_wash_id를 받아서 각각 세차장 1, 2, 3 화면을 띄워준다.
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


# user 등록
# 메일을 받고, 아이디는 시간을 초단위로 계산해서 user_id로 사용함
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = int(time.time())
        user_mail = request.form['mail']

        # POST 데이터 확인
        print("id ", user_id)
        print("mail: ", user_mail)

        new_user = User(id=user_id,
                        mail=user_mail
                        )
        db.session.add(new_user)

        db.session.commit()
        # response = {
        #     'status': 'success',
        #     'message': 'User created successfully.',
        #     'user_id': user_id
        # }
        # return jsonify(response), 201
        return render_template('registration_complete.html')
    return render_template('register.html')


@app.route('/registration_complete')
def registration_complete():
    return """<script>
    	window.location = document.referrer;
    	</script>"""


if __name__ == '__main__':
    # 데베 생성
    try:
        with app.app_context():
            db.create_all()
            print("Database initialized")
    except Exception as e:
        print(f"Failed to initailize the database{e}")
    app.run(debug=True)
