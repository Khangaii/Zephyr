import threading
import time
import hardware.motors as motors
from tracking.camera import Camera
from web.app import start_app

# Global variable to keep track of the current mode
current_mode = "automatic"

def joystick_control():
    # Placeholder for joystick control logic
    pass

def main():
    global current_mode

    # Initialize components
    motors.init()
    print("Motors initialized successfully.")
    
    try:
        print("Initializing camera...")
        camera = Camera(face_tracking=True)
        print("Camera class initialized successfully.")
        camera.start()
        print("Camera started successfully.")
    except Exception as e:
        print(f"Error initializing camera: {e}")
        return

    # Start the web app in a separate thread and pass the camera instance
    print("Starting web app...")
    web_thread = threading.Thread(target=start_app, args=(camera,))
    web_thread.start()
    print("Web app started successfully.")

    try:
        # Main loop
        while True:
            if current_mode == "automatic":
                faces = camera.get_faces()
                if faces:
                    # Assuming the first detected face is the target
                    (startX, startY, endX, endY) = faces[0]
                    centerX = (startX + endX) // 2
                    centerY = (startY + endY) // 2
                    motors.rotate_to(centerX, centerY)
            elif current_mode == "joystick":
                joystick_control()  # Placeholder for joystick control logic

            time.sleep(0.1)  # Adjust the sleep time as needed

    except KeyboardInterrupt:
        pass
    finally:
        camera.stop()
        motors.stop()
        print("Camera and motors stopped successfully.")

if __name__ == "__main__":
    main()
