import time

class MockFanMotor:
    def __init__(self, base_pin, tilt_pin, fan_pin, camera_resolution=(640, 480)):
        """
        Initialize the MockFanMotor class.
        :param base_pin: GPIO pin connected to the base motor (MG996R).
        :param tilt_pin: GPIO pin connected to the tilt motor (MG90S).
        :param fan_pin: GPIO pin connected to the fan.
        :param camera_resolution: Resolution of the camera feed (default is 640x480).
        """
        self.base_pin = base_pin
        self.tilt_pin = tilt_pin
        self.fan_pin = fan_pin
        self.camera_resolution = camera_resolution

        # Initialize current angles
        self.current_base_angle = 90
        self.current_tilt_angle = 90

    def rotate_to(self, base_angle, tilt_angle):
        """
        Rotate the fan to the specified angles.
        :param base_angle: Angle for the base motor (0 to 180 degrees).
        :param tilt_angle: Angle for the tilt motor (0 to 180 degrees).
        """
        print(f"Rotating fan to base angle {base_angle} and tilt angle {tilt_angle}")
        # time.sleep(0.5)  # Simulate time for the servos to reach the position

        # Update current angles
        self.current_base_angle = base_angle
        self.current_tilt_angle = tilt_angle

    def rotate_to_coordinates(self, x, y):
        """
        Rotate the fan to the specified Cartesian coordinates.
        :param x: X-coordinate from the camera feed.
        :param y: Y-coordinate from the camera feed.
        """
        # Calculate the center of the camera feed
        center_x = self.camera_resolution[0] // 2
        center_y = self.camera_resolution[1] // 2

        # Calculate the offset from the center
        offset_x = x - center_x
        offset_y = y - center_y

        # Map the offset to changes in angles (assuming 180 degrees range for both servos)
        delta_base_angle = (offset_x / center_x) * 90
        delta_tilt_angle = -(offset_y / center_y) * 90

        # Calculate the new angles
        new_base_angle = self.current_base_angle + delta_base_angle
        new_tilt_angle = self.current_tilt_angle + delta_tilt_angle

        # Ensure the angles are within the valid range
        new_base_angle = max(0, min(180, new_base_angle))
        new_tilt_angle = max(0, min(180, new_tilt_angle))

        # Rotate to the new angles
        self.rotate_to(new_base_angle, new_tilt_angle)

    def turn_fan_on(self):
        """
        Turn the fan on.
        """
        print("Fan turned on")

    def turn_fan_off(self):
        """
        Turn the fan off.
        """
        print("Fan turned off")

    def stop(self):
        """
        Stop the fan (turn off PWM signals).
        """
        self.turn_fan_off()
        print("Stopping the fan")

    def cleanup(self):
        """
        Cleanup resources.
        """
        print("Cleaning up resources")

# Initialize the motor
def init(base_pin=17, tilt_pin=18, fan_pin=27, camera_resolution=(640, 480)):
    global motor
    motor = MockFanMotor(base_pin, tilt_pin, fan_pin, camera_resolution)

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

# Cleanup resources
def cleanup():
    motor.cleanup()
