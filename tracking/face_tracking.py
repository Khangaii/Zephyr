import cv2
import numpy as np

class FaceTracker:
    def __init__(self, model_path, config_path, threshold=0.7):
        self.net = cv2.dnn.readNetFromCaffe(config_path, model_path)
        self.threshold = threshold

    def detect_faces(self, frame):
        (h, w) = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0,
                                     (300, 300), (104.0, 177.0, 123.0))
        self.net.setInput(blob)
        detections = self.net.forward()

        faces = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > self.threshold:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                faces.append((startX, startY, endX, endY))
        return faces

    def start_tracking(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            faces = self.detect_faces(frame)
            for (startX, startY, endX, endY) in faces:
                cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)

            cv2.imshow("Face Tracking", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    model_path = "tracking/dnn/res10_300x300_ssd_iter_140000.caffemodel"
    config_path = "tracking/dnn/deploy.prototxt.txt"
    tracker = FaceTracker(model_path, config_path)
    tracker.start_tracking()
