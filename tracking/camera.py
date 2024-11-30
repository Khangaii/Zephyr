import threading
import cv2
from picamera2 import Picamera2, Preview
from tracking.face_tracking import FaceTracker
import time

class Camera:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Camera, cls).__new__(cls)
        return cls._instance

    def __init__(self, resolution=(640, 480), framerate=30, face_tracking=False):
        if hasattr(self, '_initialized') and self._initialized:
            return

        print("Initializing Camera class.")
        self.resolution = resolution
        self.framerate = framerate
        self.face_tracking = face_tracking

        self.picam2 = None
        self.running = False
        self.lock = threading.Lock()
        self.frame = None
        self.faces = []  # Store detected faces
        self.new_frame_available = False  # Flag to indicate if a new frame is available
        self.face_tracker = FaceTracker()

        self._initialize_camera()
        self._initialized = True

    def _initialize_camera(self):
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
                    for face in faces:
                        bbox = face[:4].astype(int)
                        startX, startY, width, height = bbox
                        endX = startX + width
                        endY = startY + height
                        cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)

                with self.lock:
                    self.frame = frame
                    self.new_frame_available = True  # Set the flag to indicate a new frame is available
            except Exception as e:
                print(f"Error capturing frame: {e}")

    def get_frame(self):
        with self.lock:
            self.new_frame_available = False  # Reset the flag when the frame is accessed
            return self.frame

    def is_new_frame_available(self):
        with self.lock:
            return self.new_frame_available

    def get_faces(self):
        with self.lock:
            self.new_frame_available = False  # Reset the flag when the frame is accessed
            return self.faces

    def stop(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join()
        if self.picam2:
            self.picam2.stop()

    def toggle_face_tracking(self):
        self.face_tracking = not self.face_tracking

    def enable_face_tracking(self):
        self.face_tracking = True
    
    def disable_face_tracking(self):
        self.face_tracking = False

    def __del__(self):
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
