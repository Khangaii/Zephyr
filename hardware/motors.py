import pigpio
import time
import threading
from utils.presets import preset_left_to_right, preset_up_down, preset_circle, preset_zig_zag

class FanMotor:
    def __init__(self, base_pin, tilt_pin, fan_pin, camera_resolution=(640, 480)):
        self.base_pin = base_pin
        self.tilt_pin = tilt_pin
        self.fan_pin = fan_pin
        self.camera_resolution = camera_resolution

        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("pigpio daemon is not running")

        self.pi.set_mode(self.base_pin, pigpio.OUTPUT)
        self.pi.set_mode(self.tilt_pin, pigpio.OUTPUT)
        self.pi.set_mode(self.fan_pin, pigpio.OUTPUT)

        self.current_base_angle = 90
        self.current_tilt_angle = 90

        self.rotation_thread = None
        self.rotation_lock = threading.Lock()
        self.stop_rotation = False
        self.preset_thread = None

    def angle_to_pulse_width(self, angle):
        pulse_width = 500 + (angle / 180) * 2000
        return max(500, min(2500, pulse_width))

    def rotate_to(self, base_angle, tilt_angle):
        print(f"Rotating to base angle: {base_angle}, tilt angle: {tilt_angle}")
        with self.rotation_lock:
            self.stop_rotation = True
            if self.rotation_thread is not None:
                self.rotation_thread.join()

            self.stop_rotation = False
            self.rotation_thread = threading.Thread(target=self._smooth_rotate, args=(base_angle, tilt_angle))
            self.rotation_thread.start()

    def _smooth_rotate(self, target_base_angle, target_tilt_angle):
        step_size = 0.5
        delay = 0.005

        while not self.stop_rotation and (self.current_base_angle != target_base_angle or self.current_tilt_angle != target_tilt_angle):
            if self.current_base_angle < target_base_angle:
                self.current_base_angle = min(self.current_base_angle + step_size, target_base_angle)
            elif self.current_base_angle > target_base_angle:
                self.current_base_angle = max(self.current_base_angle - step_size, target_base_angle)

            if self.current_tilt_angle < target_tilt_angle:
                self.current_tilt_angle = min(self.current_tilt_angle + step_size, target_tilt_angle)
            elif self.current_tilt_angle > target_tilt_angle:
                self.current_tilt_angle = max(self.current_tilt_angle - step_size, target_tilt_angle)

            base_pulse_width = self.angle_to_pulse_width(self.current_base_angle)
            tilt_pulse_width = self.angle_to_pulse_width(self.current_tilt_angle)

            self.pi.set_servo_pulsewidth(self.base_pin, base_pulse_width)
            self.pi.set_servo_pulsewidth(self.tilt_pin, tilt_pulse_width)

            time.sleep(delay)

        self.pi.set_servo_pulsewidth(self.base_pin, 0)
        self.pi.set_servo_pulsewidth(self.tilt_pin, 0)

    def rotate_to_coordinates(self, x, y):
        center_x = self.camera_resolution[0] // 2
        center_y = self.camera_resolution[1] // 2

        offset_x = x - center_x
        offset_y = y - center_y

        threshold = 48

        if abs(offset_x) < threshold and abs(offset_y) < threshold:
            # print("Face is close enough to the center. No movement needed.")
            return

        k_base = 0.25
        k_tilt = 0.25

        delta_base_angle = -(offset_x / center_x) * 25 * k_base
        delta_tilt_angle = -(offset_y / center_y) * 25 * k_tilt

        new_base_angle = self.current_base_angle + delta_base_angle
        new_tilt_angle = self.current_tilt_angle + delta_tilt_angle

        new_base_angle = max(0, min(180, new_base_angle))
        new_tilt_angle = max(0, min(180, new_tilt_angle))

        self.rotate_to(new_base_angle, new_tilt_angle)

    def turn_fan_on(self):
        self.pi.write(self.fan_pin, 1)
        # print("Fan turned on")

    def turn_fan_off(self):
        self.pi.write(self.fan_pin, 0)
        # print("Fan turned off")

    def stop(self):
        self.pi.set_servo_pulsewidth(self.base_pin, 0)
        self.pi.set_servo_pulsewidth(self.tilt_pin, 0)
        self.stop_rotation = True
        # print("Stopping the rotation")

    def cleanup(self):
        self.stop()
        self.turn_fan_off()
        self.pi.stop()

    def preset_left_to_right(self):
        self.preset_thread = threading.Thread(target=preset_left_to_right, args=(self,))
        self.preset_thread.start()

    def preset_up_down(self):
        self.preset_thread = threading.Thread(target=preset_up_down, args=(self,))
        self.preset_thread.start()

    def preset_circle(self):
        self.preset_thread = threading.Thread(target=preset_circle, args=(self,))
        self.preset_thread.start()

    def preset_zig_zag(self):
        self.preset_thread = threading.Thread(target=preset_zig_zag, args=(self,))
        self.preset_thread.start()

    def start_continuous_rotation(self, direction):
        self.stop_rotation = False
        self.rotation_thread = threading.Thread(target=self._continuous_rotate, args=(direction,))
        self.rotation_thread.start()

    def stop_continuous_rotation(self):
        self.stop_rotation = True
        if self.rotation_thread is not None:
            self.rotation_thread.join()
        self.stop_rotation = False
        self.pi.set_servo_pulsewidth(self.base_pin, 0)
        self.pi.set_servo_pulsewidth(self.tilt_pin, 0)

    def _continuous_rotate(self, direction):
        step_size = 5
        delay = 0.05
        while not self.stop_rotation:
            if direction == 'up':
                self.current_tilt_angle = min(self.current_tilt_angle + step_size, 180)
            elif direction == 'down':
                self.current_tilt_angle = max(self.current_tilt_angle - step_size, 0)
            elif direction == 'left':
                self.current_base_angle = min(self.current_base_angle + step_size, 180)
            elif direction == 'right':
                self.current_base_angle = max(self.current_base_angle - step_size, 0)
            print(f"Base angle: {self.current_base_angle}, Tilt angle: {self.current_tilt_angle}")
            self.pi.set_servo_pulsewidth(self.tilt_pin, self.angle_to_pulse_width(self.current_tilt_angle))
            self.pi.set_servo_pulsewidth(self.base_pin, self.angle_to_pulse_width(self.current_base_angle))
            time.sleep(delay)

# Initialize the motor
def init(base_pin=27, tilt_pin=17, fan_pin=12, camera_resolution=(640, 480)):
    global motor
    motor = FanMotor(base_pin, tilt_pin, fan_pin, camera_resolution)

# Rotate the fan to the specified angles
def rotate_to(base_angle, tilt_angle):
    motor.rotate_to(base_angle, tilt_angle)

# Rotate the fan to the specified Cartesian coordinates
def rotate_to_coordinates(x, y):
    motor.rotate_to_coordinates(x, y)

# Turn the fan on
def turn_fan_on():
    motor.turn_fan_on()

# Turn the fan off
def turn_fan_off():
    motor.turn_fan_off()

# Stop the fan
def stop():
    motor.stop()

# Cleanup pigpio resources
def cleanup():
    motor.cleanup()

# Test the motor functionality
def test_motor():
    try:
        init()
        print("Testing motor...")

        # Rotate to initial position
        rotate_to(90, 90)
        input("Press Enter to continue...")

        # Rotate to different angles
        rotate_to(45, 45)
        input("Press Enter to continue...")
        rotate_to(135, 135)
        input("Press Enter to continue...")

        # Rotate to coordinates
        rotate_to_coordinates(320, 240)
        input("Press Enter to continue...")
        rotate_to_coordinates(640, 480)
        input("Press Enter to continue...")

        rotate_to(90, 90)
        input("Press Enter to continue...")

        # Turn the fan on and off
        turn_fan_on()
        input("Press Enter to turn the fan off...")
        turn_fan_off()
        input("Press Enter to finish the test...")

        print("Motor test completed successfully.")
    except Exception as e:
        print(f"Error during motor test: {e}")
    finally:
        cleanup()

def init_position():
    try:
        init()
        rotate_to(90, 90)
    except Exception as e:
        print(f"Error during motor test: {e}")
    finally:
        cleanup()

if __name__ == "__main__":
    test_motor()
    # init_position()
