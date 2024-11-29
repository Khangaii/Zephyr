# wsgi.py
from web.app import app, set_camera
from threading import Thread
from main import main
from tracking.camera import Camera

# Initialize the camera
camera = Camera(face_tracking=True)
camera.start()

# Set the camera instance in the web app
set_camera(camera)

# Start the main application logic in a separate thread without starting the web app
main_thread = Thread(target=main, kwargs={'start_web_app': False})
main_thread.start()

if __name__ == "__main__":
    app.run()
