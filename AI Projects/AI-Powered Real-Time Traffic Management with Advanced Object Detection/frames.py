import cv2
import os

# Path to your directory containing videos and coco.names
base_dir = r'D:\AI-Powered Real-Time Traffic Management with Advanced Object Detection\datas'

# Create a directory to save the frames
extracted_frames_dir = os.path.join(base_dir, 'extracted_frames')
os.makedirs(extracted_frames_dir, exist_ok=True)

# Path to your video files (assuming they are directly in the 'datas' folder)
video_files = [f for f in os.listdir(base_dir) if f.endswith('.mp4')]

frame_count = 0

for video_file in video_files:
    video_path = os.path.join(base_dir, video_file)
    cap = cv2.VideoCapture(video_path)
    success, image = cap.read()
    while success:
        frame_filename = f"frame_{frame_count}.jpg"
        cv2.imwrite(os.path.join(extracted_frames_dir, frame_filename), image)
        success, image = cap.read()
        frame_count += 1
    cap.release()

print("Frames extracted successfully.")
