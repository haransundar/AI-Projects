import os
import cv2
import numpy as np
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from sklearn.metrics.pairwise import cosine_similarity
import tkinter as tk
from threading import Thread
from datetime import datetime, timedelta

# Initialize MTCNN for face detection
mtcnn = MTCNN(keep_all=True)

# Initialize FaceNet model
resnet = InceptionResnetV1(pretrained='vggface2').eval()

# Directories
unknown_dir = r'C:\Users\kodesh\Music\facerecognition\unknown'
find_dir = r'C:\Users\kodesh\Music\facerecognition\find'
os.makedirs(unknown_dir, exist_ok=True)
os.makedirs(find_dir, exist_ok=True)

# Preprocessing function
def preprocess_face(face):
    """Preprocess the face image for the model."""
    face = cv2.resize(face, (160, 160))  # Resize face to 160x160
    face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
    face = np.moveaxis(face, -1, 0)  # Change from HWC to CHW format
    face = np.expand_dims(face, axis=0).astype(np.float32)  # Add batch dimension and convert to float32
    face = (face / 255.0)  # Normalize to [0, 1]
    return face

def get_embedding(face):
    """Get face embedding from the model."""
    preprocessed_face = preprocess_face(face)
    with torch.no_grad():
        embedding = resnet(torch.from_numpy(preprocessed_face)).detach().numpy()
    return embedding

def detect_faces(frame):
    """Detect faces and perform comparison with faces in the unknown folder."""
    boxes, _ = mtcnn.detect(frame)
    if boxes is not None:
        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            face = frame[y1:y2, x1:x2]
            
            if face.size == 0:
                continue  # Skip if no face is detected
            
            # Get face embedding
            embedding = get_embedding(face)
            
            # Compare with faces in the unknown folder
            match_found = False
            for filename in os.listdir(unknown_dir):
                unknown_face_path = os.path.join(unknown_dir, filename)
                unknown_face = cv2.imread(unknown_face_path)
                if unknown_face is not None:
                    unknown_embedding = get_embedding(unknown_face)
                    similarity = cosine_similarity(embedding, unknown_embedding)
                    if similarity >= 0.85:  # Increased threshold for higher accuracy
                        match_found = True
                        break

            if match_found:
                # Draw bounding box around face with green color
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green bounding box
            else:
                # Draw bounding box around face with red color
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Red bounding box

def capture_photo_on_keypress(frame):
    """Capture and process photo when 't' key is pressed in the secondary window."""
    global image_counter  # Declare image_counter as global to modify it
    global seen_faces  # Declare seen_faces as global to modify it

    if frame is not None:
        # Get face embedding
        embedding = get_embedding(frame)

        # Compare with faces in the unknown folder
        match_found = False
        for filename in os.listdir(unknown_dir):
            unknown_face_path = os.path.join(unknown_dir, filename)
            unknown_face = cv2.imread(unknown_face_path)
            if unknown_face is not None:
                unknown_embedding = get_embedding(unknown_face)
                similarity = cosine_similarity(embedding, unknown_embedding)
                if similarity >= 0.85:  # Increased threshold for higher accuracy
                    match_found = True
                    break

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if match_found:
            # Display message if a match is found
            update_status("Match Found\nDo not provide Accommodation")
        else:
            # Save the face image to unknown directory with timestamp
            image_filename = os.path.join(unknown_dir, f'face_{timestamp}.jpg')
            cv2.imwrite(image_filename, frame)
            seen_faces[f'face_{timestamp}'] = embedding
            # Display message if no match is found
            update_status("No Match Found\nPlease provide Accommodation")

def update_status(message):
    """Update the status message in the GUI."""
    global status_label
    status_label.config(text=message)

def cleanup_old_photos():
    """Remove photos older than one month from the unknown directory."""
    now = datetime.now()
    for filename in os.listdir(unknown_dir):
        file_path = os.path.join(unknown_dir, filename)
        creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
        if now - creation_time > timedelta(days=30):
            os.remove(file_path)

def update_frame():
    """Update frame from webcam and handle photo capture."""
    global frame_to_capture
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect faces in the frame without displaying match/not found messages
        detect_faces(frame)
        
        # Update the frame for capture
        frame_to_capture = frame
        
        # Display the main frame
        cv2.imshow('Face Recognition', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def capture_photo():
    """Capture and process photo when the button is clicked."""
    if frame_to_capture is not None:
        capture_photo_on_keypress(frame_to_capture)

def create_control_gui():
    """Create GUI with a button to capture photos."""
    global status_label
    window = tk.Tk()
    window.title("Control Window")
    window.geometry("300x150")
    
    # Button to capture photo
    button = tk.Button(window, text="Capture Photo", command=capture_photo, height=2, width=20)
    button.pack(pady=20)
    
    # Label to display status messages
    status_label = tk.Label(window, text="", font=("Helvetica", 12))
    status_label.pack(pady=20)
    
    window.mainloop()

# Initialize global variables
image_counter = 0  # Initialize counter for saving images
seen_faces = {}     # Dictionary to store seen faces and their embeddings

# Initialize the webcam
cap = cv2.VideoCapture(0)

# Create a thread to update the frame from webcam
frame_to_capture = None
frame_thread = Thread(target=update_frame)
frame_thread.start()

# Create the control GUI
create_control_gui()

# Periodically clean up old photos
cleanup_interval = timedelta(hours=24)  # Clean up every 24 hours
next_cleanup = datetime.now() + cleanup_interval

while True:
    now = datetime.now()
    if now >= next_cleanup:
        cleanup_old_photos()
        next_cleanup = now + cleanup_interval
    # Allow other threads to run
    time.sleep(10)
