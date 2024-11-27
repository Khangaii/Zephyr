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

    last_face_detected_time = time.time()

    try:
        # Main loop
        while True:
            if current_mode == "automatic":
                if camera.is_new_frame_available():
                    frame = camera.get_frame()
                    faces = camera.get_faces()
                    if len(faces) > 0:
                        # Assuming the first detected face is the target
                        (startX, startY, width, height) = faces[0]
                        endX = startX + width
                        endY = startY + height
                        centerX = (startX + endX) // 2
                        centerY = (startY + endY) // 2
                        motors.rotate_to_coordinates(centerX, centerY)
                        motors.turn_fan_on()
                        last_face_detected_time = time.time()
                    else:
                        if time.time() - last_face_detected_time > 10:
                            motors.turn_fan_off()
            elif current_mode == "manual":
                joystick_control()  # Placeholder for joystick control logic
            elif current_mode == "standby":
                motors.stop()  # Stop the motors and turn off the fan
            # Add other preset modes here

            time.sleep(0.1)  # Adjust the sleep time as needed

    except KeyboardInterrupt:
        pass
    finally:
        camera.stop()
        motors.cleanup()
        print("Camera and motors stopped successfully.")

if __name__ == "__main__":
    main()
