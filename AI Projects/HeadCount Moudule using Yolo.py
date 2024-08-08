import cv2
import torch
import numpy as np

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')

# Function to detect people in the frame
def detect_people(frame):
    results = model(frame)
    labels, confidences, boxes = results.xyxyn[0][:, -1], results.xyxyn[0][:, -2], results.xyxyn[0][:, :-2]
    
    people_count = 0
    
    for i in range(len(labels)):
        if labels[i] == 0:  # Class ID 0 corresponds to 'person'
            people_count += 1
            box = boxes[i].cpu().numpy()
            x1, y1, x2, y2 = int(box[0] * frame.shape[1]), int(box[1] * frame.shape[0]), int(box[2] * frame.shape[1]), int(box[3] * frame.shape[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, "Person", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    return frame, people_count

def main():
    cap = cv2.VideoCapture(0)  # Change this to the video file path if needed
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame, people_count = detect_people(frame)
        cv2.putText(frame, f"People Count: {people_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        cv2.imshow('Head Count', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
