import threading
import cv2
import numpy as np
from picamera2 import Picamera2, Preview
from tracking.face_tracking import FaceTracker
import time

class Camera:
    def __init__(self, resolution=(640, 480), framerate=30, face_tracking=False):
        """
        Initialize the Camera class.
        :param resolution: Tuple for the resolution of the video feed (default is 640x480).
        :param framerate: Frames per second (default is 30).
        :param face_tracking: Boolean to enable face tracking (default is False).
        """
        print("Initializing Camera class.")
        self.resolution = resolution
        self.framerate = framerate
        self.face_tracking = face_tracking

        self.picam2 = None
        self.running = False
        self.lock = threading.Lock()
        self.frame = None
        self.faces = []  # Store detected faces
        self.face_tracker = FaceTracker("tracking/dnn/res10_300x300_ssd_iter_140000.caffemodel", "tracking/dnn/deploy.prototxt.txt")

        self._initialize_camera()

    def _initialize_camera(self):
        """
        Attempt to initialize the camera with retries.
        """
        if self.picam2 is not None:
            print("Camera is already initialized.")
            return

        retries = 5
        for _ in range(retries):
            try:
                self.picam2 = Picamera2()
                self.picam2.configure(self.picam2.create_preview_configuration(main={"size": self.resolution, "format": "RGB888"}))
                self.picam2.start()
                print("Camera initialized successfully.")
                return
            except RuntimeError as e:
                print(f"Failed to initialize camera: {e}")
                self.picam2 = None
                time.sleep(1)  # Wait before retrying

        print("Failed to initialize camera after multiple attempts.")

    def start(self):
        """
        Start the camera stream in a separate thread.
        """
        if self.running:
            print("Camera is already running.")
            return

        if self.picam2 is None:
            print("Camera is not initialized.")
            return

        self.running = True
        self.thread = threading.Thread(target=self._capture_frames, daemon=True)
        self.thread.start()

    def _capture_frames(self):
        """
        Continuously capture frames from the camera.
        """
        while self.running:
            try:
                frame = self.picam2.capture_array()
                if frame is None:
                    print("Failed to grab frame from the camera.")
                    continue

                if self.face_tracking:
                    faces = self.face_tracker.detect_faces(frame)
                    with self.lock:
                        self.faces = faces  # Update detected faces
                    for (startX, startY, endX, endY) in faces:
                        cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)

                with self.lock:
                    self.frame = frame
            except Exception as e:
                print(f"Error capturing frame: {e}")

    def get_frame(self):
        """
        Retrieve the latest frame.
        :return: The latest captured frame (or None if not available).
        """
        with self.lock:
            return self.frame

    def get_faces(self):
        """
        Retrieve the latest detected faces.
        :return: The latest detected faces (or an empty list if not available).
        """
        with self.lock:
            return self.faces

    def stop(self):
        """
        Stop the camera stream and release resources.
        """
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join()
        if self.picam2:
            self.picam2.stop()

    def toggle_face_tracking(self):
        """
        Toggle the face tracking feature.
        """
        self.face_tracking = not self.face_tracking

    def __del__(self):
        """
        Ensure resources are released on deletion.
        """
        self.stop()

if __name__ == "__main__":
    # Test the Camera module
    camera = Camera(face_tracking=True)
    camera.start()

    try:
        while True:
            frame = camera.get_frame()
            if frame is not None:
                cv2.imshow("Camera Feed", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        pass
    finally:
        camera.stop()
        cv2.destroyAllWindows()
