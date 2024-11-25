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
from usage_DB import db, User, CAR_WASH_MODELS

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
                        mail=user_mail
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

if __name__ == '__main__':
    # 데베 생성
    try:
        with app.app_context():
            db.create_all()
            print("Database initialized")
    except Exception as e:
        print(f"Failed to initailize the database{e}")
    app.run(debug=True)
