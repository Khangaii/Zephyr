from flask import Flask, render_template, Response, redirect, url_for, request, session, jsonify
from flask_socketio import SocketIO, emit
import cv2
import random
import string
from functools import wraps

app = Flask(__name__, template_folder='template')
app.secret_key = 'tkdldjchlrh!!'
socketio = SocketIO(app)

camera = None  # Global variable to store the Camera instance
current_admin = None  # Global variable to store the current admin
access_code = None  # Global variable to store the one-time access code
current_mode = 'automatic'  # Global variable to store the current mode

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

def control_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session and request.remote_addr != current_admin:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    global current_admin
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            if current_admin and current_admin != request.remote_addr:
                # Prompt the user to confirm if they want to take control
                return render_template('confirm_login.html')
            session['logged_in'] = True
            current_admin = request.remote_addr
            socketio.emit('control_update', {'current_admin': current_admin}, broadcast=True)
            return redirect(url_for('index'))
        else:
            return 'Invalid credentials'
    return render_template('login.html')

@app.route('/confirm_login', methods=['POST'])
def confirm_login():
    global current_admin
    if request.form['confirm'] == 'yes':
        # Emit an event to notify the current admin to log out
        socketio.emit('force_logout', broadcast=True)
        session['logged_in'] = True
        current_admin = request.remote_addr
        socketio.emit('control_update', {'current_admin': current_admin}, broadcast=True)
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    global current_admin
    session.pop('logged_in', None)
    current_admin = None
    socketio.emit('control_update', {'current_admin': None}, broadcast=True)
    return redirect(url_for('index'))

@app.route('/')
def index():
    global current_admin
    is_admin = 'logged_in' in session
    if is_admin and current_admin is None:
        current_admin = request.remote_addr
        socketio.emit('control_update', {'current_admin': current_admin}, broadcast=True)
    is_in_control = is_admin and current_admin == request.remote_addr
    return render_template('index.html', logged_in=is_admin, access_code=access_code, resolution=camera.resolution, is_in_control=is_in_control)

@app.route('/video_feed')
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

@app.route('/generate_access_code')
@login_required
def generate_access_code():
    global access_code
    access_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return redirect(url_for('index'))

@app.route('/disable_access_code', methods=['POST'])
@control_required
def disable_access_code():
    global access_code
    access_code = None
    return jsonify({'status': 'success'})

@app.route('/set_mode', methods=['POST'])
@control_required
def set_mode():
    global current_mode
    mode = request.form.get('mode')
    preset = request.form.get('preset')
    
    if mode:
        current_mode = mode
    if preset and current_mode == 'presets':
        current_mode = preset

    if current_mode == 'automatic':
        camera.enable_face_tracking()
    elif current_mode == 'manual':
        camera.disable_face_tracking()
    else:
        camera.disable_face_tracking()
        # Add other preset modes here

    socketio.emit('mode_update', {'mode': mode, 'preset': preset}, broadcast=True)
    return jsonify({'status': 'success'})

@app.route('/get_mode')
def get_mode():
    global current_mode
    return jsonify({'mode': current_mode})

@app.route('/take_control', methods=['POST'])
def take_control():
    global current_admin, access_code
    access_code_input = request.form.get('access_code')
    if 'logged_in' in session or (access_code and access_code_input == access_code):
        current_admin = request.remote_addr
        access_code = None  # Invalidate the access code after use
        socketio.emit('control_update', {'current_admin': current_admin}, broadcast=True)
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid access code'})

@app.route('/relinquish_control', methods=['POST'])
def relinquish_control():
    global current_admin
    if request.remote_addr == current_admin:
        current_admin = None
        socketio.emit('control_update', {'current_admin': None}, broadcast=True)
        # Emit an event to trigger the admin to take control
        socketio.emit('admin_take_control', broadcast=True)
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'You do not have control'})

def start_app(camera_instance):
    global camera
    camera = camera_instance
    socketio.run(app, host='0.0.0.0', debug=True, use_reloader=False)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)
