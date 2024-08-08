import cv2
import mediapipe as mp
import numpy as np

# Setup Mediapipe for hand tracking
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_drawing = mp.solutions.drawing_utils

# Initialize canvas and colors
canvas = np.zeros((480, 640, 3), dtype=np.uint8)
colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
color_index = 0
thickness = 5

# Define gesture recognition functions
def is_drawing_gesture(landmarks):
    # Check if the index finger is extended and other fingers are folded
    return landmarks[8][1] < landmarks[6][1] < landmarks[4][1]  # Simplified logic

def is_change_color_gesture(landmarks):
    # Check if thumb and index finger form a circle (simplified logic)
    return np.linalg.norm(np.array(landmarks[4]) - np.array(landmarks[8])) < 40

def is_change_thickness_gesture(landmarks):
    # Check if a fist is formed (simplified logic)
    return np.linalg.norm(np.array(landmarks[8]) - np.array(landmarks[4])) > 80 and landmarks[8][1] > landmarks[6][1]

# Capture and process frames
cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Process landmarks to recognize gestures
            landmarks = [(lm.x * frame.shape[1], lm.y * frame.shape[0]) for lm in hand_landmarks.landmark]
            index_finger_tip = landmarks[8]  # Index finger tip
            
            if is_drawing_gesture(landmarks):
                cv2.circle(canvas, (int(index_finger_tip[0]), int(index_finger_tip[1])), thickness, colors[color_index], -1)
            elif is_change_color_gesture(landmarks):
                color_index = (color_index + 1) % len(colors)
            elif is_change_thickness_gesture(landmarks):
                thickness = thickness + 1 if thickness < 20 else 1
    
    combined_frame = cv2.addWeighted(frame, 0.5, canvas, 0.5, 0)
    cv2.imshow('Hand Gesture Drawing Application', combined_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
