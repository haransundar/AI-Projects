import cv2
import mediapipe as mp
import pygame
import numpy as np

# Initialize PyGame and mixer
pygame.init()
pygame.mixer.init()

# Load drum sounds
snare_sound = pygame.mixer.Sound('snare.wav')
hihat_sound = pygame.mixer.Sound('hihat.wav')
bass_sound = pygame.mixer.Sound('bass.wav')

# Initialize Mediapipe Hand Detector
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils

# Define regions for different drum sounds
regions = {
    'snare': ((100, 200), (100, 200)),  # ((x1, x2), (y1, y2))
    'hihat': ((300, 400), (100, 200)),
    'bass': ((200, 300), (300, 400)),
}

def play_sound(region_name):
    if region_name == 'snare':
        snare_sound.play()
    elif region_name == 'hihat':
        hihat_sound.play()
    elif region_name == 'bass':
        bass_sound.play()

cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, img = cap.read()
    if not success:
        break

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = hands.process(img_rgb)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            for region, ((x1, x2), (y1, y2)) in regions.items():
                for lm in hand_landmarks.landmark:
                    h, w, c = img.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    if x1 < cx < x2 and y1 < cy < y2:
                        play_sound(region)

    # Draw regions on the frame
    for region, ((x1, x2), (y1, y2)) in regions.items():
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, region, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    cv2.imshow('Virtual Drum Kit', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pygame.quit()
