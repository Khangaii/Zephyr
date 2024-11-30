import cv2
import numpy as np

class FaceTracker:
    def __init__(self, model_path='tracking/dnn/face_detection_yunet_2022mar.onnx', threshold=0.95):
        self.net = cv2.FaceDetectorYN.create(model_path, "", (320, 320), threshold, 0.3, 5000)
        self.threshold = threshold

    def detect_faces(self, frame):
        (h, w) = frame.shape[:2]
        self.net.setInputSize((w, h))
        faces = self.net.detect(frame)
        if faces[1] is not None:
            return faces[1][:, :4]  # Return only the bounding box coordinates
        return []

    def start_tracking(self):
        self.cap = cv2.VideoCapture(0)
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            faces = self.detect_faces(frame)
            for face in faces:
                bbox = face[:4].astype(int)
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[0] + bbox[2], bbox[1] + bbox[3]), (0, 255, 0), 2)

            cv2.imshow("Face Tracking", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    model_path = "tracking/dnn/face_detection_yunet_2022mar.onnx"
    tracker = FaceTracker(model_path)
    tracker.start_tracking()
