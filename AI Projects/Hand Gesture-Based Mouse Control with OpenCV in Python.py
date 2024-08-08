import cv2
import numpy as np
import pyautogui

# Initialize the webcam
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    roi = frame[100:400, 100:400]

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (35, 35), 0)
    _, thresh = cv2.threshold(blur, 127, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        max_contour = max(contours, key=cv2.contourArea)
        
        if cv2.contourArea(max_contour) > 1000:  # Ensure the contour is large enough
            hull = cv2.convexHull(max_contour, returnPoints=False)
            defects = cv2.convexityDefects(max_contour, hull)

            if hull is not None and len(hull) > 0:
                for i in range(defects.shape[0]):
                    s, e, f, d = defects[i, 0]
                    start = tuple(max_contour[s][0])
                    end = tuple(max_contour[e][0])
                    far = tuple(max_contour[f][0])

                    if i == 0:
                        screen_x = np.interp(start[0], [0, roi.shape[1]], [0, pyautogui.size().width])
                        screen_y = np.interp(start[1], [0, roi.shape[0]], [0, pyautogui.size().height])
                        pyautogui.moveTo(screen_x, screen_y)
                    elif i == 1:
                        pyautogui.click()

                cv2.drawContours(roi, [cv2.convexHull(max_contour)], -1, (0, 0, 255), 2)

    cv2.imshow('Frame', frame)
    cv2.imshow('ROI', roi)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
