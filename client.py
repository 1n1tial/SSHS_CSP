import cv2
import json
import socket
import sys
import argparse
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--video", help="Path to the video file", default="test")
args = parser.parse_args()

path_str = 'assets\\' + args.video + '.mp4'

if not Path(path_str).exists():
    print("Video file not found. Exiting.")
    sys.exit()

# Load video file
cap = cv2.VideoCapture(path_str)

# Display first frame for ROI selection
ret, frame = cap.read()

# add a button with text "Finish" on the top right corner
frame = cv2.rectangle(frame, (frame.shape[1]-110, 5), (frame.shape[1]-5, 35), (0, 0, 0), -1)
frame = cv2.putText(frame, "Finish", (frame.shape[1]-100, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

# Function to select multiple ROIs
x0, y0 = -1, -1
rois = {'blue':[], 'green':[], 'red':[]}
selecting_roi = False
current_roi = []
color = (255, 0, 0)
current_frame = frame.copy()
running = True

# function to draw colored rois
def draw_rois(img, rois):
    for color, roi in rois.items():
        if color == 'blue':
            color = (255, 0, 0)
        elif color == 'green':
            color = (0, 255, 0)
        elif color == 'red':
            color = (0, 0, 255)
        if roi:
            img = cv2.line(img, roi[0], roi[1], color, 2)
    return img

# function to draw small colored rectangles as buttons on the top left corner according to the color of the roi
def draw_buttons(img, rois):
    for color, roi in rois.items():
        if not roi:
            continue
        if color == 'blue':
            color = (255, 0, 0)
            img = cv2.rectangle(img, (10, 10), (60, 30), color, -1)
        elif color == 'green':
            color = (0, 255, 0)
            img = cv2.rectangle(img, (10, 60), (60, 80), color, -1)
        elif color == 'red':
            color = (0, 0, 255)
            img = cv2.rectangle(img, (10, 110), (60, 130), color, -1)
    return img


def select_roi(event, x, y, flags, param):
    global selecting_roi, current_roi, x0, y0, color, current_frame, rois, running
    if event == cv2.EVENT_LBUTTONDOWN:
        selecting_roi = True
        current_roi = [(x, y)]
        x0,y0=x,y
    elif event == cv2.EVENT_MOUSEMOVE and selecting_roi:
        frame_copy = current_frame.copy()
        cv2.line(frame_copy, (x0,y0),(x,y),color,2)
        cv2.imshow('Select ROIs', frame_copy)
    elif event == cv2.EVENT_LBUTTONUP:
        selecting_roi = False
        current_roi.append((x, y))
        if x0 != x and y0 != y:
            if color == (255, 0, 0):
                rois['blue'] = current_roi
                current_frame = draw_rois(frame.copy(), rois)
                current_frame = draw_buttons(current_frame, rois)
                if len(rois['green']) == 0:
                    color = (0, 255, 0)
                elif len(rois['red']) == 0:
                    color = (0, 0, 255)
                else:
                    color = None
            elif color == (0, 255, 0):
                rois['green'] = current_roi
                current_frame = draw_rois(frame.copy(), rois)
                current_frame = draw_buttons(current_frame, rois)
                if len(rois['blue']) == 0:
                    color = (255,0, 0)
                elif len(rois['red']) == 0:
                    color = (0, 0, 255)
                else:
                    color = None
            elif color == (0, 0, 255):
                rois['red'] = current_roi
                current_frame = draw_rois(frame.copy(), rois)
                current_frame = draw_buttons(current_frame, rois)
                if len(rois['green']) == 0:
                    color = (0, 255, 0)
                elif len(rois['blue']) == 0:
                    color = (255,0,0)
                else:
                    color = None
            else:
                print("All ROIs selected.")
            current_roi = []
        else:
            current_roi = []
        cv2.imshow('Select ROIs', current_frame)
    elif event == cv2.EVENT_LBUTTONDBLCLK:
        c = 0
        if 10<x<60 and 10<y<30:
            c = 'blue'
        elif 10<x<60 and 60<y<80:
            c = 'green'
        elif 10<x<60 and 110<y<130:
            c = 'red'
        elif frame.shape[1]-110<x<frame.shape[1]-5 and 5<y<35:
            running = False
        if c:
            rois[c] = []
            current_frame = draw_rois(frame.copy(), rois)
            current_frame = draw_buttons(current_frame, rois)
            cv2.imshow('Select ROIs', current_frame)
            color = (255, 0, 0) if c == 'blue' else (0, 255, 0) if c == 'green' else (0, 0, 255)
        
        
cv2.namedWindow("Select ROIs")
cv2.imshow("Select ROIs", frame)
cv2.setMouseCallback("Select ROIs", select_roi)

while running:
    cv2.waitKey(1)

cv2.destroyWindow("Select ROIs")
cap.release()

# Verify ROIs are correctly selected
if not rois['blue'] and not rois['green'] and not rois['red']:
    print("No ROIs selected. Exiting.")
    sys.exit()

# Prepare ROIs coordinates
roi_coordinates = [
    {"start":roi[0], "end":roi[1], "color":color, "video":args.video} for color, roi in rois.items() if len(roi) == 2
]

# Send ROI coordinates to the remote server
host = '10.9.8.3'  # Replace with the remote server IP address
port = 4000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((host, port))
    s.sendall(json.dumps(roi_coordinates).encode())
    print("ROI coordinates sent to the remote server")

    # Receive the results from the server
    data = b''
    while True:
        packet = s.recv(4096)
        data += packet
        if packet:
            break

    results = json.loads(data.decode())
    print("Results received from the remote server")
    
    try:
        if results['error']:
            print(f"Error: {results['error']}")
            sys.exit()
    except TypeError:
        pass

    # Print the results
    for result in results:
        print(f"Total cyclists entering ROI {result['color']}: {result['person']}")
        print(f"Total pedestrians entering ROI {result['color']}: {result['bicycle']}")
        print(f"Total cars entering ROI {result['color']}: {result['car']}")
        print(f"Total trucks entering ROI {result['color']}: {result['truck']}")
        print(f"Total buses entering ROI {result['color']}: {result['bus']}")
        print(f"Total motorcycles entering ROI {result['color']}: {result['motorcycle']}")