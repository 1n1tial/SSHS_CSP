import cv2
import numpy as np
import sys
sys.path.append('/home/initial/CSP/darknet/') 
# cd darknet
import darknet2

# Load YOLO with Darknet
configPath = "/home/initial/CSP/darknet/cfg/yolov4.cfg"
weightPath = "/home/initial/CSP/darknet/yolov4.weights"
metaPath = "/home/initial/CSP/darknet/cfg/coco.data"

network, class_names, class_colors = darknet2.load_network(
    configPath,
    metaPath,
    weightPath,
    batch_size=1
)

# Load video file
cap = cv2.VideoCapture("road_video.mp4")

# Define the function to select ROI
roi = None
selecting_roi = False

def select_roi(event, x, y, flags, param):
    global roi, selecting_roi
    if event == cv2.EVENT_LBUTTONDOWN:
        selecting_roi = True
        roi = [(x, y)]
    elif event == cv2.EVENT_MOUSEMOVE and selecting_roi:
        roi[1:] = [(x, y)]
    elif event == cv2.EVENT_LBUTTONUP:
        selecting_roi = False
        roi.append((x, y))

# Display first frame for ROI selection
ret, frame = cap.read()
cv2.namedWindow("Select ROI")
cv2.setMouseCallback("Select ROI", select_roi)

while True:
    temp_frame = frame.copy()
    if len(roi) == 2:
        cv2.rectangle(temp_frame, roi[0], roi[1], (0, 255, 0), 2)
    cv2.imshow("Select ROI", temp_frame)
    key = cv2.waitKey(1)
    if key == 27:  # Press 'ESC' to exit ROI selection
        break

cv2.destroyWindow("Select ROI")

# Verify ROI is correctly selected
if len(roi) != 2:
    print("ROI not selected properly. Exiting.")
    cap.release()
    exit()

# Extract ROI coordinates
x1, y1 = roi[0]
x2, y2 = roi[1]

# Define functions to check if the detected object is a cyclist or pedestrian
def is_cyclist(label):
    return label in ["bicycle", "motorbike"]

def is_pedestrian(label):
    return label == "person"

cyclist_count = 0
pedestrian_count = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    darknet_image = darknet2.make_image(frame.shape[1], frame.shape[0], 3)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    darknet2.copy_image_from_bytes(darknet_image, frame_rgb.tobytes())

    detections = darknet2.detect_image(network, class_names, darknet_image, thresh=0.5)
    darknet2.free_image(darknet_image)

    for label, confidence, bbox in detections:
        x, y, w, h = map(int, bbox)
        if (x - w // 2 > x1 and x + w // 2 < x2 and y - h // 2 > y1 and y + h // 2 < y2):
            color = class_colors[label]
            if is_cyclist(label):
                cyclist_count += 1
                cv2.rectangle(frame, (x - w // 2, y - h // 2), (x + w // 2, y + h // 2), color, 2)
                cv2.putText(frame, f"Cyclist ({label})", (x - w // 2, y - h // 2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            elif is_pedestrian(label):
                pedestrian_count += 1
                cv2.rectangle(frame, (x - w // 2, y - h // 2), (x + w // 2, y + h // 2), color, 2)
                cv2.putText(frame, "Pedestrian", (x - w // 2, y - h // 2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    cv2.rectangle(frame, roi[0], roi[1], (255, 0, 0), 2)
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1)
    if key == 27:  # Press 'ESC' to exit
        break

cap.release()
cv2.destroyAllWindows()

print(f"Total cyclists entering ROI: {cyclist_count}")
print(f"Total pedestrians entering ROI: {pedestrian_count}")
