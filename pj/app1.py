from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import cv2
import pytesseract
from datetime import datetime

app = Flask(__name__)

# 저장 디렉터리 설정
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detect', methods=['POST'])
def detect():
    try:
        # 실시간 웹캠 화면에서 번호판 인식
        cam = cv2.VideoCapture(0)
        ret, frame = cam.read()
        if not ret:
            return jsonify({'success': False, 'message': '카메라를 읽을 수 없습니다.'})

        # 현재 시간으로 이미지 저장
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        image_path = os.path.join(UPLOAD_FOLDER, f'plate_{timestamp}.png')
        cv2.imwrite(image_path, frame)

        # 번호판 인식
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, config='--psm 6')
        cam.release()

        # 인식 결과 반환
        return jsonify({'success': True, 'image_path': image_path, 'detected_text': text.strip()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

