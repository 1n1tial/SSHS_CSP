# Description: This script is the server side of the application. It listens for incoming connections from the client side, receives the ROI coordinates from the client, processes the video and sends the results back to the client.

# Import necessary libraries
import cv2
import numpy as np
import json
import sys
import supervision as sv
from ultralytics import YOLO
import sockets

# Define the host and port number(must be the same as the client)
host = '0.0.0.0'
port = 4000

# Load the YOLO model
MODEL = "models/yolov8x.pt"
model = YOLO(MODEL)
model.fuse()

# a function that takes a list of numbers and a max value and counts how many numbers are in each equally devided intervals of the max value
# used for printing the graph results of the counter
# to see how many objects entered the ROI in each interval of the video
def count_intervals(numbers, max_value, num_intervals):
    intervals = np.linspace(0, max_value, num_intervals + 1)
    counts = np.zeros(num_intervals)
    for number in numbers:
        for i in range(num_intervals):
            if intervals[i] < number <= intervals[i + 1]:
                counts[i] += 1
    return counts.tolist() # a list of counts of numbers in each interval
    
# a class that takes the start and end coordinates of the ROI, the video file path and processes the video to count the number of objects that entered the ROI
class Counter:
    def __init__(self, start:tuple, end:tuple, video_file:str):
        self.start = start
        self.end = end
        self.video_file = video_file
        self.video_file = '/home/initial/CSP/assets/' + self.video_file + '.mp4'
        
        self.selected_classes = {'person':0, 'bicycle':1, 'motorcycle':3, 'car':2, 'bus':5, 'truck':7}
        self.byte_tracker = {
            'person': sv.ByteTrack(track_activation_threshold=0.25, lost_track_buffer=30, minimum_matching_threshold=0.7, frame_rate=30),
            'bicycle': sv.ByteTrack(track_activation_threshold=0.25, lost_track_buffer=30, minimum_matching_threshold=0.7, frame_rate=30),
            'motorcycle': sv.ByteTrack(track_activation_threshold=0.25, lost_track_buffer=30, minimum_matching_threshold=0.7, frame_rate=30),
            'car': sv.ByteTrack(track_activation_threshold=0.25, lost_track_buffer=30, minimum_matching_threshold=0.7, frame_rate=30),
            'bus': sv.ByteTrack(track_activation_threshold=0.25, lost_track_buffer=30, minimum_matching_threshold=0.7, frame_rate=30),
            'truck': sv.ByteTrack(track_activation_threshold=0.25, lost_track_buffer=30, minimum_matching_threshold=0.7, frame_rate=30)
        } # initialize the byte tracker for each class
        self.line_zones = {
            'person': sv.LineZone(start=sv.Point(*self.start), end=sv.Point(*self.end)),
            'bicycle': sv.LineZone(start=sv.Point(*self.start), end=sv.Point(*self.end)),
            'motorcycle': sv.LineZone(start=sv.Point(*self.start), end=sv.Point(*self.end)),
            'car': sv.LineZone(start=sv.Point(*self.start), end=sv.Point(*self.end)),
            'bus': sv.LineZone(start=sv.Point(*self.start), end=sv.Point(*self.end)),
            'truck': sv.LineZone(start=sv.Point(*self.start), end=sv.Point(*self.end))
        } # initialize the line zone for each class with the start and end coordinates of the ROI
        self.counter = {
            'person': 0,
            'bicycle': 0,
            'motorcycle': 0,
            'car': 0,
            'bus': 0,
            'truck': 0
        } # initialize the counter for each class
        self.frame_counter = {
            'person': [],
            'bicycle': [],
            'motorcycle': [],
            'car': [],
            'bus': [],
            'truck': []
        } # initialize the frame counter for each class --> it is a list that contains at which frame number an object entered the ROI
        
    def process(self): # a function that processes the video and returns the counter for each class
        try:
            cap = cv2.VideoCapture(self.video_file)
            length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) # get the total number of frames in the video
        except Exception as e: # in case the video file is not found
            print(e)
            return {'error': str(e)} # instead of the counter, return the error message to the client
        
        def callback(frame: np.ndarray, index:int) -> np.ndarray: # define a callable function that takes a frame and the frame number and processes the frame
            results = model(frame, verbose=False)[0] # process the frame using the YOLO model
            for key in self.selected_classes:
                detections = sv.Detections.from_ultralytics(results)
                detections = detections[detections.class_id == self.selected_classes[key]] # select only the class that we are interested in
                detections = self.byte_tracker[key].update_with_detections(detections) # update the byte tracker with the detections
                self.line_zones[key].trigger(detections) # trigger the line zone with the detections and update the counter if detection enters the ROI
                if self.line_zones[key].in_count + self.line_zones[key].out_count > self.counter[key]: # if the counter is updated(the object entered the ROI), append the frame number to the frame counter
                    self.counter[key] = self.line_zones[key].in_count + self.line_zones[key].out_count
                    self.frame_counter[key].append(index)
            return None
        
        try:
            sv.process_video(
                source_path = self.video_file,
                target_path = self.video_file.replace(".mp4", "-result.mp4"),
                callback=callback
            ) # process the video using the callback function
        except Exception as e:
            print(e)
            return {'error': str(e)}
        return {key: count_intervals(self.frame_counter[key], length, 6) for key in self.frame_counter} # use the count_intervals function to count the number of objects that entered the ROI in each interval of the video, and then return the calculated list for each class


def calculate(roi_coordinates):
    asdf = [] # list that will contain the final result to send to the client
    for roi in roi_coordinates: # for each roi 
        counter = Counter(roi['start'], roi['end'], roi['video']) # define the counter object
        a = counter.process() # and process the counter
        try:
            if a['error']:
                return a # if an error message is returned, return the error message to the client
        except KeyError:
            a['color'] = roi['color'] # if no error, add the color of the ROI to the result, so that the client will know which ROI the result belongs to
        asdf.append(a)
    return asdf


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # create a socket object
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # make sure the socket is reusable
    s.bind((host, port)) # bind the socket to the host and port defined above, so that the client can connect to it
    s.listen() # start listening for incoming connections
    print("Waiting for ROI coordinates...")
    while 1: # while the server is running, keep waiting for incoming connections
        conn, addr = s.accept() # accept the incoming connection
        with conn:
            print(f"Connected by {addr}")
            data = conn.recv(1024) # receive the ROI coordinates from the client(1024 bytes is enough for the coordinates)
            roi_coordinates = json.loads(data.decode()) # decode the received data to a list of dictionaries
            print(roi_coordinates)
            print("calculating...")
            roi_counters = calculate(roi_coordinates) # calculate the counter for each ROI
            results = json.dumps(roi_counters) # Send results back to the client
            conn.sendall(results.encode())
            print("Results sent to client")
            print("Waiting for ROI coordinates...")



