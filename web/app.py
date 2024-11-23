from flask import Flask, render_template, Response, redirect, url_for, request, session
import cv2
from tracking.camera import Camera
from functools import wraps

app = Flask(__name__, template_folder='template')
app.secret_key = 'tkdldjchlrh!!'

camera = None  # Global variable to store the Camera instance

# Dummy credentials
USERNAME = 'admin'
PASSWORD = 'password'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return 'Invalid credentials'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/video_feed')
@login_required
def video_feed():
    def gen_frames():
        while True:
            frame = camera.get_frame()
            if frame is not None:
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/toggle_face_tracking')
@login_required
def toggle_face_tracking():
    camera.toggle_face_tracking()
    return redirect(url_for('index'))

def start_app(camera_instance):
    global camera
    camera = camera_instance
    app.run(debug=True, use_reloader=False)

if __name__ == '__main__':
    app.run(debug=True)
