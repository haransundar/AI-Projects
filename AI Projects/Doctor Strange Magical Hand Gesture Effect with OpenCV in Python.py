import math
import cv2
from cvzone.HandTrackingModule import HandDetector

detector = HandDetector()

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
shield = cv2.VideoCapture("shield.mp4")

def mapFromTo(x, a, b, c, d):
    return (x - a) / (b - a) * (d - c) + c

def Overlay(background, overlay, x, y, size):
    background_h, background_w, c = background.shape
    imgScale = mapFromTo(size, 200, 20, 1.5, 0.2)
    if overlay is not None and overlay.size != 0:
        overlay = cv2.resize(overlay, (0, 0), fx=imgScale, fy=imgScale)
        h, w, c = overlay.shape
        try:
            if x + w / 2 >= background_w or y + h / 2 >= background_h or x - w / 2 <= 0 or y - h / 2 <= 0:
                return background
            else:
                overlayImage = overlay[..., :3]
                mask = overlay / 255.0
                background[int(y - h / 2):int(y + h / 2), int(x - w / 2):int(x + w / 2)] = (
                            1 - mask) * background[int(y - h / 2):int(y + h / 2), int(x - w / 2):int(x + w / 2)] + overlay
                return background
        except Exception as e:
            print(f"Error in Overlay function: {e}")
            return background
    else:
        print("Overlay image is empty")
        return background

def findDistance(point1, point2):
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

showShield = True
changeTimer = 0

while True:
    success, img = cap.read()
    hands, img = detector.findHands(img)  # Update the way you call findHands
    final = img
    if hands:
        success, shieldImage = shield.read()
        if not success:
            shield.set(cv2.CAP_PROP_POS_FRAMES, 0)
            success, shieldImage = shield.read()
        if shieldImage is not None and shieldImage.size != 0:
            print(f"Shield image shape: {shieldImage.shape}")

    if len(hands) >= 2:
        changeTimer += 1
        hand1_lmList = hands[0]["lmList"] if len(hands) > 0 else None
        hand2_lmList = hands[1]["lmList"] if len(hands) > 1 else None
        if hand1_lmList is not None and hand2_lmList is not None:
            if findDistance(hand1_lmList[9], hand2_lmList[9]) < 30:
                if changeTimer > 100:
                    showShield = not showShield
                    changeTimer = 0
        if showShield:
            for hand in hands:
                bbox = hand["bbox"]
                handSize = bbox[2]
                cx, cy = hand["center"]
                if 1 in detector.fingersUp(hand):
                    final = Overlay(img, shieldImage, cx, cy, handSize)

    elif len(hands) == 1:
        for hand in hands:
            bbox = hand["bbox"]
            handSize = bbox[2]
            cx, cy = hand["center"]
            if 1 in detector.fingersUp(hand):
                final = Overlay(img, shieldImage, cx, cy, handSize)
    cv2.imshow("Doctor Strange", cv2.flip(final, 1))
    cv2.waitKey(2)
