import cv2
import numpy as np

# Initialize the webcam
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # Flip the frame horizontally
    frame = cv2.flip(frame, 1)
    
    # Define the region of interest for hand detection
    roi = frame[100:400, 100:400]
    
    # Convert the ROI to grayscale
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to the grayscale image
    blur = cv2.GaussianBlur(gray, (35, 35), 0)
    
    # Threshold the blurred image
    _, thresh = cv2.threshold(blur, 127, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Find contours in the thresholded image
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # Find the contour with the maximum area
        max_contour = max(contours, key=cv2.contourArea)
        
        # Draw the contour on the ROI
        cv2.drawContours(roi, [max_contour], -1, (0, 255, 0), 3)
        
        # Find the convex hull of the contour
        hull = cv2.convexHull(max_contour)
        
        # Draw the convex hull on the ROI
        cv2.drawContours(roi, [hull], -1, (0, 0, 255), 2)
        
        # Find convexity defects
        hull = cv2.convexHull(max_contour, returnPoints=False)
        defects = cv2.convexityDefects(max_contour, hull)
        
        if defects is not None:
            count_defects = 0
            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                start = tuple(max_contour[s][0])
                end = tuple(max_contour[e][0])
                far = tuple(max_contour[f][0])
                
                # Calculate the angles between the defects
                a = np.linalg.norm(np.array(start) - np.array(end))
                b = np.linalg.norm(np.array(start) - np.array(far))
                c = np.linalg.norm(np.array(end) - np.array(far))
                angle = np.arccos((b**2 + c**2 - a**2) / (2*b*c)) * 57.2957795
                
                # If the angle is less than 90 degrees, consider it a defect
                if angle <= 90:
                    count_defects += 1
                    cv2.circle(roi, far, 4, (0, 0, 255), -1)
            
            # Display the number of defects
            cv2.putText(frame, f"Defects: {count_defects}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    # Display the frame and ROI
    cv2.imshow('Frame', frame)
    cv2.imshow('ROI', roi)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
