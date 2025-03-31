from ultralytics import YOLO

# Load YOLOv8 model (choose the appropriate model architecture)
model = YOLO('yolov8n.yaml')  # Use 'yolov8s.yaml', 'yolov8m.yaml', etc. as needed

# Train the model
model.train(data='D:\AI-Powered Real-Time Traffic Management with Advanced Object Detection\data\data.yaml', epochs=50, batch=16, imgsz=640)

# Save the trained model
model.save('yolov8_trained.pt')
