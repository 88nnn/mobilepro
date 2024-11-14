# 세차창 예약 화면(UI-A-001, UI-A-002)
#
# 10w 세차장 목록 및 대기자 수 표시 구현
#
# 11w 세차장 예약 후 예약 정보와 예상 대기 시간 표시
#
# 12w 대기자 정보 업데이트 기능 추가


from flask import Flask
from flask import render_template
from flask import request

from flask_wtf import FlaskForm
from flask import redirect
from flask import url_for
from forms import ReservationForm
import secrets

import sqlite3
from database import reservations_db
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SECRET_KEY_ABC'


# 세차장 목록 및 대기자수를 보여주는 기본 화면
@app.route("/")
def home():
    return render_template('home.html')


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
@app.route('/reservation')
def reservation():
    return render_template('reservation.html')


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
    with app.app_context():
        reservations_db.init_db()
    app.run(debug=True)
