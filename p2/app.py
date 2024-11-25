import cv2
import pytesseract
import numpy as np
from flask import Flask, render_template, Response, jsonify, request, redirect, url_for

# Flask 애플리케이션 생성
app = Flask(__name__)

# IP Webcam URL (휴대폰에서 IP Webcam을 실행하고 제공된 URL로 교체)
url = 'http://192.168.0.101:8080/video'  # 자신의 IP Webcam URL로 변경

# 웹캡 캡처
cap = cv2.VideoCapture(url)

# 번호판 인식 함수
def process_frame(frame):
    # 이미지를 그레이스케일로 변환
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Otsu의 이진화 방법을 사용하여 이진 이미지 생성
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 윤곽선 찾기
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
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
            text = pytesseract.image_to_string(plate, config='--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789')

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
                cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        frame_count += 1

        # 프레임을 JPEG 형식으로 인코딩하여 전송
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# 기본 페이지 (스트리밍 페이지)
@app.route('/')
def index():
    return render_template('index.html', result=None)

# 스트리밍 라우트
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

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
    return redirect('http://your-team-member-product-selection-url')  # 다른 팀원의 URL로 변경

# 서버 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
