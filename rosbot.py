import os
import sys
import time
import tempfile
import json
from controller import Robot

TIME_STEP = 32
MAX_VELOCITY = 26.0
BASE_SPEED = 6.0

class ROSbotController:
    def __init__(self):
        self.robot = Robot()
        
        self.front_left_motor = self.robot.getDevice("fl_wheel_joint")
        self.front_right_motor = self.robot.getDevice("fr_wheel_joint")
        self.rear_left_motor = self.robot.getDevice("rl_wheel_joint")
        self.rear_right_motor = self.robot.getDevice("rr_wheel_joint")
        
        self.front_left_motor.setPosition(float('inf'))
        self.front_right_motor.setPosition(float('inf'))
        self.rear_left_motor.setPosition(float('inf'))
        self.rear_right_motor.setPosition(float('inf'))
        
        self.front_left_position_sensor = self.robot.getDevice("front left wheel motor sensor")
        self.front_right_position_sensor = self.robot.getDevice("front right wheel motor sensor")
        self.rear_left_position_sensor = self.robot.getDevice("rear left wheel motor sensor")
        self.rear_right_position_sensor = self.robot.getDevice("rear right wheel motor sensor")
        
        self.front_left_position_sensor.enable(TIME_STEP)
        self.front_right_position_sensor.enable(TIME_STEP)
        self.rear_left_position_sensor.enable(TIME_STEP)
        self.rear_right_position_sensor.enable(TIME_STEP)
        
        self.camera_rgb = self.robot.getDevice("camera rgb")
        self.camera_rgb.enable(TIME_STEP)
        
        self.camera_depth = self.robot.getDevice("camera depth")
        self.camera_depth.enable(TIME_STEP)
        
        self.lidar = self.robot.getDevice("laser")
        self.lidar.enable(TIME_STEP)
        self.lidar.enablePointCloud()
        
        self.accelerometer = self.robot.getDevice("imu accelerometer")
        self.gyro = self.robot.getDevice("imu gyro")
        self.compass = self.robot.getDevice("imu compass")
        
        self.accelerometer.enable(TIME_STEP)
        self.gyro.enable(TIME_STEP)
        self.compass.enable(TIME_STEP)
        
        self.distance_sensors = []
        self.distance_sensors.append(self.robot.getDevice("fl_range"))
        self.distance_sensors.append(self.robot.getDevice("rl_range"))
        self.distance_sensors.append(self.robot.getDevice("fr_range"))
        self.distance_sensors.append(self.robot.getDevice("rr_range"))
        
        for sensor in self.distance_sensors:
            sensor.enable(TIME_STEP)
        
        self.speed = BASE_SPEED
        self.is_executing_commands = False
        self.command_queue = []
        
        self.image_dir = tempfile.gettempdir()
        
        self.command_file = os.path.join(self.image_dir, "rosbot_commands.json")
        self.last_command_check = 0
        
        print(f"ROSbot initialized. Image directory: {self.image_dir}")
        print(f"Command file: {self.command_file}")
        
    def set_motor_speeds(self, left_speed, right_speed):
        left_speed = min(max(left_speed, -MAX_VELOCITY), MAX_VELOCITY)
        right_speed = min(max(right_speed, -MAX_VELOCITY), MAX_VELOCITY)
        
        self.front_left_motor.setVelocity(left_speed)
        self.front_right_motor.setVelocity(right_speed)
        self.rear_left_motor.setVelocity(left_speed)
        self.rear_right_motor.setVelocity(right_speed)
    
    def stop(self):
        self.set_motor_speeds(0, 0)
    
    def capture_image(self):
        image = self.camera_rgb.getImage()
        width = self.camera_rgb.getWidth()
        height = self.camera_rgb.getHeight()
        
        image_path = os.path.join(self.image_dir, f"rosbot_image_{int(time.time())}.jpg")
        
        with open(f"{image_path}.bmp", "wb") as f:
            f.write(bytes([ord('B'), ord('M')]))
            size = 54 + 3 * width * height
            f.write(size.to_bytes(4, byteorder='little'))
            f.write(bytes([0, 0, 0, 0]))
            f.write((54).to_bytes(4, byteorder='little'))
            f.write((40).to_bytes(4, byteorder='little'))
            f.write(width.to_bytes(4, byteorder='little'))
            f.write(height.to_bytes(4, byteorder='little'))
            f.write((1).to_bytes(2, byteorder='little'))
            f.write((24).to_bytes(2, byteorder='little'))
            f.write(bytes([0, 0, 0, 0]))
            f.write(bytes([0, 0, 0, 0]))
            f.write(bytes([0, 0, 0, 0]))
            f.write(bytes([0, 0, 0, 0]))
            f.write(bytes([0, 0, 0, 0]))
            f.write(bytes([0, 0, 0, 0]))
            
            for y in range(height - 1, -1, -1):
                for x in range(width):
                    idx = (y * width + x) * 4
                    b = int(image[idx + 2])
                    g = int(image[idx + 1])
                    r = int(image[idx])
                    f.write(bytes([b, g, r]))
                
                padding_len = (4 - (width * 3) % 4) % 4
                f.write(bytes([0] * padding_len))
        
        try:
            from PIL import Image
            img = Image.open(f"{image_path}.bmp")
            img.save(image_path)
            os.remove(f"{image_path}.bmp")
        except ImportError:
            image_path = f"{image_path}.bmp"
        
        return image_path
    
    def execute_commands(self, commands_str):
        if commands_str.startswith("[") and commands_str.endswith("]"):
            commands = commands_str.strip("[]").split(",")
            commands = [cmd.strip().strip('"\'') for cmd in commands if cmd.strip()]
        else:
            commands = commands_str.strip().split("\n")
            commands = [cmd.strip().strip('"\'') for cmd in commands if cmd.strip()]
        
        self.command_queue = commands
        self.is_executing_commands = True
        print(f"Added commands to queue: {commands}")
    
    def process_command(self, command):
        print(f"Executing command: {command}")
        
        if command.startswith("go_ahead"):
            try:
                distance = float(command.split("(")[1].split(")")[0])
                self.move_forward(distance)
                return True
            except:
                print(f"Invalid go_ahead command: {command}")
                
        elif command.startswith("go_back"):
            try:
                distance = float(command.split("(")[1].split(")")[0])
                self.move_backward(distance)
                return True
            except:
                print(f"Invalid go_back command: {command}")
                
        elif command.startswith("turn_left"):
            try:
                angle = float(command.split("(")[1].split(")")[0])
                self.turn_left(angle)
                return True
            except:
                print(f"Invalid turn_left command: {command}")
                
        elif command.startswith("turn_right"):
            try:
                angle = float(command.split("(")[1].split(")")[0])
                self.turn_right(angle)
                return True
            except:
                print(f"Invalid turn_right command: {command}")
                
        elif command.startswith("change_speed"):
            try:
                speed = float(command.split("(")[1].split(")")[0])
                self.change_speed(speed)
                return False
            except:
                print(f"Invalid change_speed command: {command}")
        
        return False
    
    def move_forward(self, distance):
        duration = distance / (self.speed * 0.01)
        
        self.set_motor_speeds(self.speed, self.speed)
        start_time = self.robot.getTime()
        
        while self.robot.step(TIME_STEP) != -1:
            current_time = self.robot.getTime()
            if current_time - start_time >= duration:
                break
        
        self.stop()
    
    def move_backward(self, distance):
        duration = distance / (self.speed * 0.01)
        
        self.set_motor_speeds(-self.speed, -self.speed)
        start_time = self.robot.getTime()
        
        while self.robot.step(TIME_STEP) != -1:
            current_time = self.robot.getTime()
            if current_time - start_time >= duration:
                break
        
        self.stop()
    
    def turn_left(self, angle):
        duration = (angle / 180) * 3.14
        
        self.set_motor_speeds(-self.speed, self.speed)
        start_time = self.robot.getTime()
        
        while self.robot.step(TIME_STEP) != -1:
            current_time = self.robot.getTime()
            if current_time - start_time >= duration:
                break
        
        self.stop()
    
    def turn_right(self, angle):
        duration = (angle / 180) * 3.14
        
        self.set_motor_speeds(self.speed, -self.speed)
        start_time = self.robot.getTime()
        
        while self.robot.step(TIME_STEP) != -1:
            current_time = self.robot.getTime()
            if current_time - start_time >= duration:
                break
        
        self.stop()
    
    def change_speed(self, speed_percent):
        self.speed = MAX_VELOCITY * (speed_percent / 100.0)
        print(f"Speed changed to {self.speed}")
    
    def check_for_commands(self):
        if os.path.exists(self.command_file):
            mod_time = os.path.getmtime(self.command_file)
            if mod_time > self.last_command_check:
                self.last_command_check = mod_time
                try:
                    with open(self.command_file, 'r') as f:
                        data = json.load(f)
                        if "commands" in data:
                            self.execute_commands(data["commands"])
                except Exception as e:
                    print(f"Error reading command file: {e}")
    
    def run(self):
        while self.robot.step(TIME_STEP) != -1:
            image_path = self.capture_image()
            print(f"Captured image: {image_path}")
            
            self.check_for_commands()
            
            if self.is_executing_commands and self.command_queue:
                command = self.command_queue.pop(0)
                requires_wait = self.process_command(command)
                
                if requires_wait:
                    continue
            
            if not self.command_queue and self.is_executing_commands:
                self.is_executing_commands = False
                print("Command queue empty, waiting for new commands")

if __name__ == "__main__":
    controller = ROSbotController()
    controller.run()
