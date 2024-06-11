# Description: This script is used to select multiple ROIs in a video file and send the ROI coordinates to the remote server.
# Usage: python client.py --video <video_file_name>

# Import necessary libraries
import cv2
import json
import socket
import sys
import argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt


parser = argparse.ArgumentParser()
parser.add_argument("--video", help="Path to the video file", default="test")
args = parser.parse_args() # Parse the arguments

path_str = 'assets\\' + args.video + '.mp4' # string that contains path to the video file(video file must be in ./assets folder)

cv2.namedWindow("Initial Window") # Create a window to display the initial message
screen = np.zeros((500,700, 3), dtype="uint8") # black screen
if not Path(path_str).exists(): # if the video file is not found, display an error message and exit
    cv2.putText(screen, f"Video file {path_str} not found.", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(screen, "Press any key to exit.", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imshow("Initial Window", screen)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    sys.exit()
else: # if the video file is found, display a success message and continue
    cv2.putText(screen, f"Video file {path_str} found!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(screen, "Press any key to continue.", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imshow("Initial Window", screen)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    

# Load video file
cap = cv2.VideoCapture(path_str)

# Get the first frame
ret, frame = cap.read()

# add a button with text "Finish" on the top right corner
frame = cv2.rectangle(frame, (frame.shape[1]-110, 5), (frame.shape[1]-5, 35), (0, 0, 0), -1)
frame = cv2.putText(frame, "Finish", (frame.shape[1]-100, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

# Global variables used to select multiple ROIs
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
            color = (0, 0, 255) # set the color
        if roi:
            img = cv2.line(img, roi[0], roi[1], color, 2) # draw the line according to the roi coordinates with the appropriate color
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

# mouse event handler to select multiple rois & input button clicks(the function's name is legacy)
def select_roi(event, x, y, flags, param):
    global selecting_roi, current_roi, x0, y0, color, current_frame, rois, running # declare global variables
    if event == cv2.EVENT_LBUTTONDOWN: # if the left mouse button is clicked, start selecting roi
        selecting_roi = True
        current_roi = [(x, y)]
        x0,y0=x,y
    elif event == cv2.EVENT_MOUSEMOVE and selecting_roi: # if the mouse is moved while selecting roi, draw a line according to the start and end points
        frame_copy = current_frame.copy()
        cv2.line(frame_copy, (x0,y0),(x,y),color,2)
        cv2.imshow('Select ROIs', frame_copy)
    elif event == cv2.EVENT_LBUTTONUP: # when the left mouse button is released, stop selecting roi
        selecting_roi = False
        current_roi.append((x, y))
        if x0 != x and y0 != y: # if the roi is not a point,
            if color == (255, 0, 0):
                rois['blue'] = current_roi # if the current color is set to blue, the roi becomes blue
                current_frame = draw_rois(frame.copy(), rois) # draw the rois on the frame according to the rois
                current_frame = draw_buttons(current_frame, rois) # draw the buttons on the frame according to the rois
                if len(rois['green']) == 0: # cycle the colors of the roi so that the next roi will be of a different color
                    color = (0, 255, 0)
                elif len(rois['red']) == 0:
                    color = (0, 0, 255)
                else:
                    color = None # if all rois are selected, set the color to None
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
                print("All ROIs selected.") # if there is no space for more rois(color=None), print a message
            current_roi = []
        else:
            current_roi = []
        cv2.imshow('Select ROIs', current_frame)
    elif event == cv2.EVENT_LBUTTONDBLCLK:
        c = 0
        if 10<x<60 and 10<y<30:
            c = 'blue' # if the mouse is double clicked on the blue button, set the color to blue
        elif 10<x<60 and 60<y<80:
            c = 'green' # if the mouse is double clicked on the green button, set the color to green
        elif 10<x<60 and 110<y<130:
            c = 'red' # if the mouse is double clicked on the red button, set the color to red
        elif frame.shape[1]-110<x<frame.shape[1]-5 and 5<y<35:
            running = False # if the mouse is double clicked on the finish button, stop the while loop
        if c: # if color is set(button is clicked),
            rois[c] = [] # reset the roi of the color to an empty list(this will remove the roi of the color from the frame)
            current_frame = draw_rois(frame.copy(), rois)
            current_frame = draw_buttons(current_frame, rois)
            cv2.imshow('Select ROIs', current_frame)
            color = (255, 0, 0) if c == 'blue' else (0, 255, 0) if c == 'green' else (0, 0, 255) # change the color back to the color of the button that was clicked(the color that was removed)
        
        
cv2.namedWindow("Select ROIs")
cv2.imshow("Select ROIs", frame)
cv2.setMouseCallback("Select ROIs", select_roi)

while running: # wait for the user to select the rois, and stop when the user clicks the finish button
    cv2.waitKey(1)

cv2.destroyWindow("Select ROIs")
cap.release()

# Verify ROIs are correctly selected
if not rois['blue'] and not rois['green'] and not rois['red']:
    print("No ROIs selected. Exiting.")
    sys.exit()

# Prepare ROIs coordinates
roi_coordinates = [
    {"start":roi[0], "end":roi[1], "color":color, "video":args.video} for color, roi in rois.items() if len(roi) == 2 # if the roi is a line, add the roi to the roi_coordinates
]

# Send ROI coordinates to the remote server
host = '10.9.8.3' # IP address of the remote server
port = 4000 # port number must be the same as the server

# Connect to the server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # create a socket
    s.connect((host, port)) # connect to the server
    s.sendall(json.dumps(roi_coordinates).encode()) # send the roi coordinates to the server
    print("ROI coordinates sent to the remote server")

    # Receive the results from the server
    data = b''
    while True:
        packet = s.recv(4096) # receive data in packets of 4096 bytes(this is enough for the results to be received in one packet)
        data += packet
        if packet:
            break # keep receiving data until I receive a non-empty packet

    results = json.loads(data.decode())
    print("Results received from the remote server")
    
    try:
        if results['error']: # if an error is received, print the error and exit
            print(f"Error: {results['error']}")
            sys.exit()
    except TypeError:
        pass

    # Print the results
    for result in results: # print the results for each roi
        print(f"Total pedestrians entering ROI {result['color']}: {max(np.sum(result['person']) - np.sum(result['bicycle']), 0)}") # pedestrian = person - bicycle
        print(f"Total cyclists entering ROI {result['color']}: {np.sum(result['bicycle'])}")
        print(f"Total cars entering ROI {result['color']}: {np.sum(result['car'])}")
        print(f"Total trucks entering ROI {result['color']}: {np.sum(result['truck'])}")
        print(f"Total buses entering ROI {result['color']}: {np.sum(result['bus'])}")
        print(f"Total motorcycles entering ROI {result['color']}: {np.sum(result['motorcycle'])}")
        print("\n")
        
    # draw graph of the results and print the graph
    classes_list = ['person', 'bicycle', 'motorcycle', 'car', 'bus', 'truck']
    x = [1,2,3,4,5,6]
    for class_name in classes_list:
        plt.cla()
        plt.clf() # clear the previous graph
        for result in results:
            if class_name == 'person':
                plt.plot(x, [max(result['person'][i] - result['bicycle'][i], 0) for i in range(6)], color=result['color']) # pedestrian = person - bicycle
            plt.plot(x, result[class_name], color=result['color']) # plot the results of count in each interval as a line graph
        plt.title(f'{class_name} Count')
        plt.savefig('assets\\graph.png')
        graph = cv2.imread('assets\\graph.png') # save as image and display with cv2
        cv2.imshow('Graph', graph)
        cv2.waitKey(0)
        cv2.destroyAllWindows()