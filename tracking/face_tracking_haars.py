import cv2
import numpy as np

class FaceTracker:
    def __init__(self, cascade_path="tracking/haarcascade/haarcascade_frontalface_default.xml"):
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        self.cap = None

    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=2)
        return faces

    def start_tracking(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Cannot access the camera")
            return

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            faces = self.detect_faces(frame)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            cv2.imshow("Face Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    tracker = HaarFaceTracker()
    tracker.start_tracking()
