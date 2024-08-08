import cv2
import math
import numpy as np
import mediapipe as mp
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.5)

# Initialize webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Function to get current volume
def get_current_volume():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    return volume

# Function to set volume based on hand position
def set_volume(volume_interface, hand_y):
    try:
        # Normalize hand position to volume range (0 to 1)
        normalized_y = 1 - hand_y  # Invert y-axis for more intuitive control
        normalized_y = min(max(normalized_y, 0), 1)  # Clamp between 0 and 1
        volume_interface.SetMasterVolumeLevelScalar(normalized_y, None)
        print(f"Volume set to: {normalized_y}")
    except Exception as e:
        print(f"Error setting volume: {e}")

# Main loop to process video feed
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Flip the frame horizontally
    frame = cv2.flip(frame, 1)

    # Convert the image to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process the frame to detect hands
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        # Get the first detected hand landmarks
        hand_landmarks = results.multi_hand_landmarks[0]

        # Draw hand landmarks on the frame
        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # Get specific landmarks (thumb tip and index finger tip)
        thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        
        # Calculate Euclidean distance between thumb tip and index finger tip
        thumb_x, thumb_y = int(thumb_tip.x * frame.shape[1]), int(thumb_tip.y * frame.shape[0])
        index_x, index_y = int(index_tip.x * frame.shape[1]), int(index_tip.y * frame.shape[0])
        
        # Calculate distance
        distance = math.sqrt((thumb_x - index_x)**2 + (thumb_y - index_y)**2)

        # Map the distance to volume control (normalize to frame width)
        volume_value = distance / frame.shape[1]

        # Get current system volume
        volume_interface = get_current_volume()

        # Set volume based on hand position
        set_volume(volume_interface, volume_value)

        # Display volume level on frame
        cv2.putText(frame, f"Volume: {volume_value:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Display the frame
    cv2.imshow('Hand Gesture Volume Control', frame)

    # Exit if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
