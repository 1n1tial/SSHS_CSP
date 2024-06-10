import cv2
import numpy as np
import json
import sys
import supervision as sv
from ultralytics import YOLO
import socket



host = '0.0.0.0'
port = 4000


MODEL = "models/yolov8x.pt"
from ultralytics import YOLO
model = YOLO(MODEL)
model.fuse()

# a function that takes a list of numbers and a max value and counts how many numbers are in equally devided intervals of the max value
# used for printing the results of the counter
def count_intervals(numbers, max_value, num_intervals):
    intervals = np.linspace(0, max_value, num_intervals + 1)
    counts = np.zeros(num_intervals)
    for number in numbers:
        for i in range(num_intervals):
            if intervals[i] < number <= intervals[i + 1]:
                counts[i] += 1
    return counts.tolist()
    
class Counter:
    def __init__(self, start:tuple, end:tuple, video_file:str):
        self.start = start
        self.end = end
        self.video_file = video_file
        self.video_file = '/home/initial/CSP/assets/' + self.video_file + '.mp4'
        
        self.selected_classes = {'person':0, 'bicycle':1, 'motorcycle':3, 'car':2, 'bus':5, 'truck':7}
        self.byte_tracker = {'person': sv.ByteTrack(track_activation_threshold=0.25, lost_track_buffer=30, minimum_matching_threshold=0.8, frame_rate=30),
                             'bicycle': sv.ByteTrack(track_activation_threshold=0.25, lost_track_buffer=30, minimum_matching_threshold=0.8, frame_rate=30),
                             'motorcycle': sv.ByteTrack(track_activation_threshold=0.25, lost_track_buffer=30, minimum_matching_threshold=0.8, frame_rate=30),
                             'car': sv.ByteTrack(track_activation_threshold=0.25, lost_track_buffer=30, minimum_matching_threshold=0.8, frame_rate=30),
                             'bus': sv.ByteTrack(track_activation_threshold=0.25, lost_track_buffer=30, minimum_matching_threshold=0.8, frame_rate=30),
                             'truck': sv.ByteTrack(track_activation_threshold=0.25, lost_track_buffer=30, minimum_matching_threshold=0.8, frame_rate=30)}
        self.line_zones = {'person': sv.LineZone(start=sv.Point(*self.start), end=sv.Point(*self.end)),
                           'bicycle': sv.LineZone(start=sv.Point(*self.start), end=sv.Point(*self.end)),
                           'motorcycle': sv.LineZone(start=sv.Point(*self.start), end=sv.Point(*self.end)),
                           'car': sv.LineZone(start=sv.Point(*self.start), end=sv.Point(*self.end)),
                           'bus': sv.LineZone(start=sv.Point(*self.start), end=sv.Point(*self.end)),
                           'truck': sv.LineZone(start=sv.Point(*self.start), end=sv.Point(*self.end))}
        self.counter = {
            'person': 0,
            'bicycle': 0,
            'motorcycle': 0,
            'car': 0,
            'bus': 0,
            'truck': 0
        }
        self.frame_counter = {
            'person': [],
            'bicycle': [],
            'motorcycle': [],
            'car': [],
            'bus': [],
            'truck': []
        }
        
    def process(self):
        try:
            cap = cv2.VideoCapture(self.video_file)
            length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        except Exception as e:
            print(e)
            return {'error': str(e)}
        
        def callback(frame: np.ndarray, index:int) -> np.ndarray:
            results = model(frame, verbose=False)[0]
            for key in self.selected_classes:
                detections = sv.Detections.from_ultralytics(results)
                detections = detections[detections.class_id == self.selected_classes[key]]
                detections = self.byte_tracker[key].update_with_detections(detections)
                self.line_zones[key].trigger(detections)
                if self.line_zones[key].in_count + self.line_zones[key].out_count > self.counter[key]:
                    self.counter[key] = self.line_zones[key].in_count + self.line_zones[key].out_count
                    self.frame_counter[key].append(index)
            return None
        
        try:
            sv.process_video(
                source_path = self.video_file,
                target_path = self.video_file.replace(".mp4", "-result.mp4"),
                callback=callback
            )
        except Exception as e:
            print(e)
            return {'error': str(e)}
        return {key: count_intervals(self.frame_counter[key], length, 6) for key in self.frame_counter}


def calculate(roi_coordinates):
    asdf = []
    for roi in roi_coordinates:
        counter = Counter(roi['start'], roi['end'], roi['video'])
        a = counter.process()
        try:
            if a['error']:
                return a
        except KeyError:
            a['color'] = roi['color']
        asdf.append(a)
    return asdf


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen()
    print("Waiting for ROI coordinates...")
    while 1:
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            data = conn.recv(1024)
            roi_coordinates = json.loads(data.decode())
            print(roi_coordinates)
            print("calculating...")
            roi_counters = calculate(roi_coordinates)
            # Send results back to the client
            results = json.dumps(roi_counters)
            conn.sendall(results.encode())
            print("Results sent to client")
            print("Waiting for ROI coordinates...")



