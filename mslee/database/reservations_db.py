import sqlite3
from flask import g

# # 데이터 베이스 파일 경로
db_path = './database/car_wash_reservations.db'

# 데이터 베이스 연결 함수
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(db_path)
        return g.db


# 요청이 끝난 후 데이터 베이스 연결을 닫는 함수
def close_db():
    db = g.pop('db', None)
    if db is not None:
        db.close()


# 예약자 정보를 저장할 쿼리문
create_table_query = """
CREATE TABLE IF NOT EXISTS Reservations(
    reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    car_model TEXT NOT NULL,
    reservation_date DATE NOT NULL,
    reservation_time TIME NOT NULL,
    contact_mail TEXT NOT NULL
    )
"""


# 데이터 베이스 초기화 함수
def init_db():
    db = get_db()
    try:
        db.execute(create_table_query)
        db.commit()
        print("예약자 테이블 생성 성공")
    except sqlite3.DatabaseError as e:
        db.rollback()
        print(f"데이터베이스 에러 발생: {e}")
    finally:
        close_db()


# 예약 정보 삽입 함수
def insert_reservation(name, car_model, reservation_date, reservation_time,
                       contact_mail, carwash_id):
    db = get_db()

    print("예약 정보 삽입 완료")


# 예약자 정보 조회 함수
def get_reservations(carwash_id):
    cursor = db.cursor()

# 갱신

# 삭제
