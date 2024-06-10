# a program that resizes videos to a specified resolution

import cv2
import os
import sys
import argparse

def resize_video(video_path, output_path, width, height):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error opening video file")
        sys.exit()

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, 20.0, (width, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (width, height))
        out.write(frame)

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    print(f"Video resized to {width}x{height} and saved to {output_path}")
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", help="Path to the video file", default="./assets/test5.mp4")
    parser.add_argument("--output", help="Path to save the resized video", default="./assets/test5r.mp4")
    parser.add_argument("--width", help="Width of the resized video", type=int, default=900)
    parser.add_argument("--height", help="Height of the resized video", type=int, default=480)
    args = parser.parse_args()

    if not os.path.exists(args.video):
        print("Video file not found. Exiting.")
        sys.exit()

    resize_video(args.video, args.output, args.width, args.height)
    
if __name__ == "__main__":
    main()