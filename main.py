import threading
import time
import hardware.motors as motors
from tracking.camera import Camera
from web.app import start_app
from utils.shared_state import shared_state

def joystick_control():
    # Placeholder for joystick control logic
    pass

def main():
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
            current_mode = shared_state["current_mode"]
            if current_mode == "automatic":
                if camera.is_new_frame_available():
                    faces = camera.get_faces()
                    if len(faces) > 0:
                        # Find the largest face
                        largest_face = max(faces, key=lambda face: face[2] * face[3])
                        (startX, startY, width, height) = largest_face
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
                            motors.rotate_to(90, 135)
            elif current_mode == "manual":
                motors.turn_fan_on()  # Turn on the fan for manual control
                joystick_control()  # Placeholder for joystick control logic
                motors.stop()
            elif current_mode == "standby":
                motors.stop()  # Stop the motors and keep the fan on
            elif current_mode == "left-right":
                pass
            elif current_mode == "up-down":
                pass
            elif current_mode == "circle":
                pass
            elif current_mode == "zig-zag":
                pass

            time.sleep(0.1)  # Adjust the sleep time as needed

    except KeyboardInterrupt:
        pass
    finally:
        # Stop the camera and cleanup motors
        camera.stop()
        motors.cleanup()
        print("Camera and motors stopped successfully.")

if __name__ == "__main__":
    main()
