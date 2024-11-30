from flask import Flask, render_template, Response, redirect, url_for, request, session, jsonify
from flask_socketio import SocketIO, emit
import cv2
import random
import string
import time
from functools import wraps
import hardware.motors as motors
from utils.shared_state import shared_state

app = Flask(__name__, template_folder='template')
app.secret_key = 'tkdldjchlrh!!'
socketio = SocketIO(app)

camera = None  # Global variable to store the Camera instance
current_admin = None  # Global variable to store the current admin
access_code = None  # Global variable to store the one-time access code

# Dummy credentials
USERNAME = 'sior'
PASSWORD = 'wpvlfh!!'

def set_camera(camera_instance):
    global camera
    camera = camera_instance

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
        if request.remote_addr != current_admin:
            return jsonify({'status': 'error', 'message': 'You do not have control'})
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
        return redirect(url_for('index'))

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
    mode = request.form.get('mode')
    preset = request.form.get('preset')
    
    if mode:
        shared_state["current_mode"] = mode
    if preset and shared_state["current_mode"] == 'presets':
        shared_state["current_mode"] = preset
        
    camera.disable_face_tracking()
    motors.motor.stop_rotation = True
    if motors.motor.preset_thread is not None:
        motors.motor.preset_thread.join()
    if motors.motor.rotation_thread is not None:
        motors.motor.rotation_thread.join()
    motors.motor.stop_rotation = False

    if shared_state["current_mode"] == 'automatic':
        camera.enable_face_tracking()
    elif shared_state["current_mode"] == 'manual':
        camera.disable_face_tracking()
    else:
        motors.motor.turn_fan_on()
        motors.motor.stop_rotation = False
        if shared_state["current_mode"] == 'standby':
            pass
        elif shared_state["current_mode"] == 'left-right':
            motors.motor.preset_left_to_right()
        elif shared_state["current_mode"] == 'up-down':
            motors.motor.preset_up_down()
        elif shared_state["current_mode"] == 'circle':
            motors.motor.preset_circle()
        elif shared_state["current_mode"] == 'zig-zag':
            motors.motor.preset_zig_zag()

    socketio.emit('mode_update', {'mode': mode, 'preset': preset}, broadcast=True)
    return jsonify({'status': 'success'})

@app.route('/get_mode')
def get_mode():
    return jsonify({'mode': shared_state["current_mode"]})

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

@app.route('/manual_control', methods=['POST'])
@control_required
def manual_control():
    command = request.form.get('command')
    # Stop any ongoing rotation
    motors.motor.stop_rotation = True
    if motors.motor.rotation_thread is not None:
        motors.motor.rotation_thread.join()
    motors.motor.stop_rotation = False
    # Execute manual control commands
    if command == 'up':
        motors.motor.start_continuous_rotation('up')
    elif command == 'down':
        motors.motor.start_continuous_rotation('down')
    elif command == 'left':
        motors.motor.start_continuous_rotation('left')
    elif command == 'right':
        motors.motor.start_continuous_rotation('right')
    elif command == 'stop':
        motors.motor.stop_continuous_rotation()
    return jsonify({'status': 'success'})

def start_app(camera_instance):
    global camera
    camera = camera_instance
    socketio.run(app, host='0.0.0.0', debug=True, use_reloader=False)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True, use_reloader=False)
