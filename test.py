import socket
import json
import cv2
import numpy as np
import darknet

# Load YOLO model using Darknet
config_path = "./yolov3.cfg"
weights_path = "./yolov3.weights"
meta_path = "./coco.data"

network, class_names, class_colors = darknet.load_network(
    config_path,
    meta_path,
    weights_path,
    batch_size=1
)

# Function to receive ROI coordinates
def receive_roi_coordinates():
    host = '0.0.0.0'
    port = 5000

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print("Waiting for ROI coordinates...")
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            data = conn.recv(1024)
            roi_coordinates = json.loads(data.decode())
            return roi_coordinates

# Receive ROI coordinates
roi_coordinates = receive_roi_coordinates()

def is_cyclist(label):
    return label in ["bicycle", "motorbike"]

def is_pedestrian(label):
    return label == "person"

# Load video file
cap = cv2.VideoCapture("road_video.mp4")

cyclist_count = 0
pedestrian_count = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    darknet_image = darknet.make_image(frame.shape[1], frame.shape[0], 3)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    darknet.copy_image_from_bytes(darknet_image, frame_rgb.tobytes())

    detections = darknet.detect_image(network, class_names, darknet_image, thresh=0.5)
    darknet.free_image(darknet_image)

    for label, confidence, bbox in detections:
        x, y, w, h = map(int, bbox)
        for roi in roi_coordinates:
            x1, y1, x2, y2 = roi["x1"], roi["y1"], roi["x2"], roi["y2"]
            if (x - w // 2 > x1 and x + w // 2 < x2 and y - h // 2 > y1 and y + h // 2 < y2):
                color = class_colors[label]
                if is_cyclist(label):
                    cyclist_count += 1
                    print(f"Cyclist entered ROI. Count: {cyclist_count}")
                elif is_pedestrian(label):
                    pedestrian_count += 1
                    print(f"Pedestrian entered ROI. Count: {pedestrian_count}")
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1)
    if key == 27:  # Press 'ESC' to exit
        break

cap.release()
cv2.destroyAllWindows()

print(f"Total cyclists entering ROI: {cyclist_count}")
print(f"Total pedestrians entering ROI: {pedestrian_count}")
