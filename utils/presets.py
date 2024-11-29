import time
import math

def preset_left_to_right(motor):
    """
    Rotate the fan from left to right.
    :param motor: The motor instance to control.
    """
    step_size = 2  # Adjust the step size for smoother movement
    delay = 0.05  # Adjust the delay between steps for smoother movement

    def set_angle(base_angle, tilt_angle):
        base_pulse_width = motor.angle_to_pulse_width(base_angle)
        tilt_pulse_width = motor.angle_to_pulse_width(tilt_angle)
        motor.pi.set_servo_pulsewidth(motor.base_pin, base_pulse_width)
        motor.pi.set_servo_pulsewidth(motor.tilt_pin, tilt_pulse_width)

    # Set tilt to 90 degrees at the start
    set_angle(motor.current_base_angle, 90)
    motor.current_tilt_angle = 90

    while not motor.stop_rotation:
        # Rotate from 0 to 180 degrees
        for angle in range(0, 181, step_size):
            set_angle(angle, 90)
            time.sleep(delay)
            if motor.stop_rotation:
                break

        # Rotate from 180 to 0 degrees
        for angle in range(180, -1, -step_size):
            set_angle(angle, 90)
            time.sleep(delay)
            if motor.stop_rotation:
                break

    # Turn off PWM signals to prevent jitter
    motor.pi.set_servo_pulsewidth(motor.base_pin, 0)
    motor.pi.set_servo_pulsewidth(motor.tilt_pin, 0)

def preset_up_down(motor):
    """
    Rotate the fan up and down.
    :param motor: The motor instance to control.
    """
    step_size = 2  # Adjust the step size for smoother movement
    delay = 0.05  # Adjust the delay between steps for smoother movement

    def set_angle(base_angle, tilt_angle):
        base_pulse_width = motor.angle_to_pulse_width(base_angle)
        tilt_pulse_width = motor.angle_to_pulse_width(tilt_angle)
        motor.pi.set_servo_pulsewidth(motor.base_pin, base_pulse_width)
        motor.pi.set_servo_pulsewidth(motor.tilt_pin, tilt_pulse_width)

    # Set base to 90 degrees at the start
    set_angle(90, motor.current_tilt_angle)
    motor.current_base_angle = 90

    while not motor.stop_rotation:
        # Rotate tilt from 45 to 135 degrees
        for angle in range(45, 136, step_size):
            set_angle(90, angle)
            time.sleep(delay)
            if motor.stop_rotation:
                break

        # Rotate tilt from 135 to 45 degrees
        for angle in range(135, 44, -step_size):
            set_angle(90, angle)
            time.sleep(delay)
            if motor.stop_rotation:
                break

    # Turn off PWM signals to prevent jitter
    motor.pi.set_servo_pulsewidth(motor.base_pin, 0)
    motor.pi.set_servo_pulsewidth(motor.tilt_pin, 0)

def preset_circle(motor):
    """
    Rotate the fan in a circular clockwise motion.
    :param motor: The motor instance to control.
    """
    step_size = 3  # Adjust the step size for smoother movement
    delay = 0.05  # Adjust the delay between steps for smoother movement
    radius = 45  # Radius of the circular motion

    def set_angle(base_angle, tilt_angle):
        base_pulse_width = motor.angle_to_pulse_width(base_angle)
        tilt_pulse_width = motor.angle_to_pulse_width(tilt_angle)
        motor.pi.set_servo_pulsewidth(motor.base_pin, base_pulse_width)
        motor.pi.set_servo_pulsewidth(motor.tilt_pin, tilt_pulse_width)

    # Set initial position
    set_angle(135, 90)
    motor.current_base_angle = 90
    motor.current_tilt_angle = 45

    while not motor.stop_rotation:
        for angle in range(0, 360, step_size):
            base_angle = 90 + radius * math.cos(math.radians(angle))
            tilt_angle = 90 + radius * math.sin(math.radians(angle))
            set_angle(base_angle, tilt_angle)
            time.sleep(delay)
            if motor.stop_rotation:
                break

    # Turn off PWM signals to prevent jitter
    motor.pi.set_servo_pulsewidth(motor.base_pin, 0)
    motor.pi.set_servo_pulsewidth(motor.tilt_pin, 0)

def preset_zig_zag(motor):
    """
    Rotate the fan in a zig-zag motion.
    :param motor: The motor instance to control.
    """
    step_size = 3
    delay = 0.05

    def set_angle(base_angle, tilt_angle):
        base_pulse_width = motor.angle_to_pulse_width(base_angle)
        tilt_pulse_width = motor.angle_to_pulse_width(tilt_angle)
        motor.pi.set_servo_pulsewidth(motor.base_pin, base_pulse_width)
        motor.pi.set_servo_pulsewidth(motor.tilt_pin, tilt_pulse_width)

    # Set initial position
    set_angle(0, 45)
    motor.current_base_angle = 0
    motor.current_tilt_angle = 45

    while not motor.stop_rotation:
        for angle in range(0, 181, step_size):
            set_angle(angle, 45)
            time.sleep(delay)
            if motor.stop_rotation:
                break
        
        for angle in range(180, -1, -step_size):
            set_angle(angle, 135 - 90 * (angle / 180))
            time.sleep(delay)
            if motor.stop_rotation:
                break

        for angle in range(0, 181, step_size):
            set_angle(angle, 135)
            time.sleep(delay)
            if motor.stop_rotation:
                break

        for angle in range(180, -1, -step_size):
            set_angle(angle, 45 + 90 * (angle / 180))
            time.sleep(delay)
            if motor.stop_rotation:
                break

    # Turn off PWM signals to prevent jitter
    motor.pi.set_servo_pulsewidth(motor.base_pin, 0)
    motor.pi.set_servo_pulsewidth(motor.tilt_pin, 0)
