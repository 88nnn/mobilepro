import cv2
import pytesseract
import time
import os

# 사진 촬영 함수
def capture_image(filename="car_image.jpg"):
    os.system(f"fswebcam -r 1280x720 --no-banner {filename}")
    print(f"Image captured: {filename}")
    return filename

# 번호판 감지 및 인식 함수
def detect_license_plate(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Canny edge detection
    edged = cv2.Canny(blurred, 50, 200)

    # Contours 찾기
    contours, _ = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    license_plate = None
    for contour in contours:
        approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
        if len(approx) == 4:  # 사각형인 경우
            license_plate = approx
            break

    if license_plate is not None:
        x, y, w, h = cv2.boundingRect(license_plate)
        roi = gray[y:y+h, x:x+w]
        text = pytesseract.image_to_string(roi, config="--psm 8")
        return text.strip(), image

    return None, image

def main():
    # 이미지 촬영
    image_path = capture_image()

    # 번호판 인식
    plate_text, processed_image = detect_license_plate(image_path)

    if plate_text:
        print(f"Detected License Plate: {plate_text}")
    else:
        print("License plate not detected.")

    # 결과 표시 및 저장
    cv2.imwrite("processed_image.jpg", processed_image)
    print("Processed image saved as 'processed_image.jpg'")

if __name__ == "__main__":
    main()

