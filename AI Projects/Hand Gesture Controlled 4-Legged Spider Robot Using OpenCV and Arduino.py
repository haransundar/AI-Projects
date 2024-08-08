import cv2
import mediapipe as mp
import serial
import time

# Initialize the Arduino connection
arduino = serial.Serial(port='COM4', baudrate=9600, timeout=2)  # Extended timeoutexe

# Initialize Mediapipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Define a function to send commands to Arduino
def send_command(command):
    try:
        arduino.write(command.encode())
        time.sleep(0.1)  # Small delay to ensure command is processed
    except serial.SerialTimeoutException:
        print("Write timeout")

# Start capturing video
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Flip the frame horizontally for a later selfie-view display
    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Example of detecting open/closed hand
            thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].y
            index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y
            
            # Assuming forward button is represented by closing the hand and backward by opening
            if thumb_tip > index_tip:
                gesture = 'F'  # Forward
            else:
                gesture = 'B'  # Backward

            send_command(gesture)
            print(f"Sent command: {gesture}")

    cv2.imshow('Hand Gesture Controlled Robot', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
arduino.close()
