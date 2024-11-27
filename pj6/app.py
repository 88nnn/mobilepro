import cv2
import pytesseract
import numpy as np
from flask import Flask, render_template, Response, jsonify, request

# Flask 애플리케이션 생성
app = Flask(__name__)

# IP Webcam URL (휴대폰에서 IP Webcam을 실행하고 제공된 URL로 교체)
url = 'http://223.194.135.161:8080/video'  # 자신의 IP Webcam URL로 변경

# 웹캡 캡처
cap = cv2.VideoCapture(url)

# 번호판 인식 함수
def process_frame(frame):
    # 그레이스케일 변환
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 이미지 이진화 (노이즈를 줄이기 위해 블러처리 후 adaptiveThreshold 사용)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    adaptive_thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    # 외곽선 찾기
    contours, _ = cv2.findContours(adaptive_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

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
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)  # 초록색 테두리

            # 번호판 영역 추출
            plate = frame[y:y + h, x:x + w]

            # Tesseract OCR로 번호판 텍스트 추출 (한글+영어 설정)
            text = pytesseract.image_to_string(plate, config='--psm 8 -l kor+eng')  # 한글+영어 설정

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
            cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)  # 번호판 텍스트 표시
        
        # 인식된 프레임을 JPEG 형식으로 변환
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# 기본 페이지 (스트리밍 페이지)
@app.route('/')
def index():
    return render_template('index.html')

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

    # 번호판 인식
    text = process_frame(frame)
    if text:
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

# 서버 실행
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

