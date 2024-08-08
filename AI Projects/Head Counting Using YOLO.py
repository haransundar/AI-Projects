import cv2

import numpy as np




# Load YOLO

net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")




# Set the preferable backend and target to CUDA

net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)

net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)




layer_names = net.getLayerNames()

output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

classes = []

with open("coco.names", "r") as f:

    classes = [line.strip() for line in f.readlines()]




# Initialize webcam

cap = cv2.VideoCapture(0)  # Change the parameter to the appropriate camera index if needed




# Create a named window and set it to fullscreen

cv2.namedWindow("Live Video", cv2.WND_PROP_FULLSCREEN)

cv2.setWindowProperty("Live Video", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)




while True:

    # Capture frame-by-frame

    ret, frame = cap.read()

    if not ret:

        break




    height, width, channels = frame.shape




    # Prepare the frame for YOLO

    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)

    net.setInput(blob)

    outs = net.forward(output_layers)




    # Initialize parameters

    class_ids = []

    confidences = []

    boxes = []




    # Analyze the outputs

    for out in outs:

        for detection in out:

            scores = detection[5:]

            class_id = np.argmax(scores)

            confidence = scores[class_id]

            if confidence > 0.5 and class_id == classes.index("person"):

                center_x = int(detection[0] * width)

                center_y = int(detection[1] * height)

                w = int(detection[2] * width)

                h = int(detection[3] * height)

                x = int(center_x - w / 2)

                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])

                confidences.append(float(confidence))

                class_ids.append(class_id)




    # Apply Non-Max Suppression to remove duplicates

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)




    # Draw bounding boxes and count people

    person_count = 0

    for i in range(len(boxes)):

        if i in indexes:

            x, y, w, h = boxes[i]

            label = str(classes[class_ids[i]])

            if label == "person":

                person_count += 1

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)




    # Display the frame with the count

    cv2.putText(frame, f"People count: {person_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Live Video", frame)




    # Break the loop on 'q' key press

    if cv2.waitKey(1) & 0xFF == ord('q'):

        break




# Release the capture and close windows

cap.release()

cv2.destroyAllWindows()

import cv2

import numpy as np




# Load YOLO

net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")




# Set the preferable backend and target to CUDA

net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)

net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)




layer_names = net.getLayerNames()

output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

classes = []

with open("coco.names", "r") as f:

    classes = [line.strip() for line in f.readlines()]




# Initialize webcam

cap = cv2.VideoCapture(0)  # Change the parameter to the appropriate camera index if needed




# Create a named window and set it to fullscreen

cv2.namedWindow("Live Video", cv2.WND_PROP_FULLSCREEN)

cv2.setWindowProperty("Live Video", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)




while True:

    # Capture frame-by-frame

    ret, frame = cap.read()

    if not ret:

        break




    height, width, channels = frame.shape




    # Prepare the frame for YOLO

    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)

    net.setInput(blob)

    outs = net.forward(output_layers)




    # Initialize parameters

    class_ids = []

    confidences = []

    boxes = []




    # Analyze the outputs

    for out in outs:

        for detection in out:

            scores = detection[5:]

            class_id = np.argmax(scores)

            confidence = scores[class_id]

            if confidence > 0.5 and class_id == classes.index("person"):

                center_x = int(detection[0] * width)

                center_y = int(detection[1] * height)

                w = int(detection[2] * width)

                h = int(detection[3] * height)

                x = int(center_x - w / 2)

                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])

                confidences.append(float(confidence))

                class_ids.append(class_id)




    # Apply Non-Max Suppression to remove duplicates

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)




    # Draw bounding boxes and count people

    person_count = 0

    for i in range(len(boxes)):

        if i in indexes:

            x, y, w, h = boxes[i]

            label = str(classes[class_ids[i]])

            if label == "person":

                person_count += 1

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)




    # Display the frame with the count

    cv2.putText(frame, f"People count: {person_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Live Video", frame)




    # Break the loop on 'q' key press

    if cv2.waitKey(1) & 0xFF == ord('q'):

        break




# Release the capture and close windows

cap.release()

cv2.destroyAllWindows()
