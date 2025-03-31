import cv2
import torch

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

def detect_vehicles(frame):
    # Perform inference
    results = model(frame)
    
    # Convert results to a DataFrame
    df = results.pandas().xyxy[0]
    
    # Filter detections for vehicles (class 2 corresponds to 'car' in YOLOv5)
    vehicles = df[df['class'] == 2]
    
    # Count the number of detected vehicles
    vehicle_count = len(vehicles)
    
    # Draw bounding boxes on the frame
    for index, row in df.iterrows():
        if row['class'] == 2:
            cv2.rectangle(frame, 
                          (int(row['xmin']), int(row['ymin'])), 
                          (int(row['xmax']), int(row['ymax'])), 
                          (0, 255, 0), 2)
    
    return frame, vehicle_count
