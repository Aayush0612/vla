from flask import Flask, request, jsonify
import ollama
import re
import os

app = Flask(__name__)

# Define robot action functions without predefined behaviors
def go_ahead(distance_meters):
    return f"go_ahead({distance_meters})"

def go_back(distance_meters):
    return f"go_back({distance_meters})"

def turn_left(angle_degrees):
    return f"turn_left({angle_degrees})"

def turn_right(angle_degrees):
    return f"turn_right({angle_degrees})"

def grab(width_meters):
    return f"grab({width_meters})"

def release():
    return f"release()"

def lift_arm(height_meters):
    return f"lift_arm({height_meters})"

def lower_arm(height_meters):
    return f"lower_arm({height_meters})"

def detect_objects():
    return f"detect_objects()"

def navigate_to(x_meters, y_meters):
    return f"navigate_to({x_meters}, {y_meters})"

def pick(x_meters, y_meters, z_meters):
    return f"pick({x_meters}, {y_meters}, {z_meters})"

def place(x_meters, y_meters, z_meters):
    return f"place({x_meters}, {y_meters}, {z_meters})"

def open_gripper(width_meters):
    return f"open_gripper({width_meters})"

def close_gripper(force_percent):
    return f"close_gripper({force_percent})"

def rotate_wrist(angle_degrees):
    return f"rotate_wrist({angle_degrees})"

def move_to_position(x_meters, y_meters, z_meters):
    return f"move_to_position({x_meters}, {y_meters}, {z_meters})"

def change_speed(speed_percent):
    return f"change_speed({speed_percent})"

def jump(height_meters, distance_meters=0):
    return f"jump({height_meters}, {distance_meters})"

def swim(speed_percent, direction_degrees):
    return f"swim({speed_percent}, {direction_degrees})"

def get_action_plan(image_path, user_prompt=""):
    image_path = image_path.strip()
    if (image_path.startswith('"') and image_path.endswith('"')) or \
       (image_path.startswith("'") and image_path.endswith("'")):
        image_path = image_path[1:-1]
    
    if not os.path.exists(image_path):
        return f"Error: Image path does not exist: {image_path}"
    
    if not user_prompt:
        user_prompt = "Based on this image, generate robot commands for the most logical task."
    
    prompt = f"""You are a Vision-Language-Action (VLA) model controlling a robot. Based on the image and the user's instruction: "{user_prompt}", generate a sequence of robot commands.

Available functions:
- go_ahead(distance_meters): Move forward by the specified distance
- go_back(distance_meters): Move backward by the specified distance
- turn_left(angle_degrees): Turn left by the specified angle in degrees
- turn_right(angle_degrees): Turn right by the specified angle in degrees
- grab(width_meters): Grab with the specified width
- release(): Release the currently held object
- lift_arm(height_meters): Lift the robot arm to the specified height
- lower_arm(height_meters): Lower the robot arm to the specified height
- detect_objects(): Detect objects in the current view
- navigate_to(x_meters, y_meters): Navigate to coordinates
- pick(x_meters, y_meters, z_meters): Pick at coordinates
- place(x_meters, y_meters, z_meters): Place at coordinates
- open_gripper(width_meters): Open the gripper to the specified width
- close_gripper(force_percent): Close the gripper with the specified force
- rotate_wrist(angle_degrees): Rotate the wrist by the specified angle
- move_to_position(x_meters, y_meters, z_meters): Move to coordinates
- change_speed(speed_percent): Change the robot's movement speed
- jump(height_meters, distance_meters): Jump up and optionally forward
- swim(speed_percent, direction_degrees): Swim at specified speed and direction

Provide your response as a Python list of function calls with appropriate parameters. For example:
[
    "go_ahead(1.5)",
    "turn_left(45)",
    "move_to_position(0.5, 0.3, 0.2)"
]

Return ONLY the command list with NO explanations or additional text."""
    
    try:
        response = ollama.chat(
            model='llama3.2-vision',
            messages=[
                {
                    'role': 'user',
                    'content': prompt,
                    'images': [image_path]
                }
            ]
        )
        
        if isinstance(response, dict):
            if 'message' in response and 'content' in response['message']:
                return response['message']['content']
            elif 'content' in response:
                return response['content']
            else:
                return str(response)
        else:
            return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        return f"Error processing image: {str(e)}"

@app.route('/process-image', methods=['POST'])
def process_image_api():
    data = request.json
    
    if 'image_path' not in data or not data['image_path']:
        return jsonify({"error": "Image path is required"}), 400
    
    image_path = data['image_path']
    user_prompt = data.get('user_prompt', "")
    
    commands = get_action_plan(image_path, user_prompt)
    
    if isinstance(commands, str) and commands.startswith("Error"):
        return jsonify({"error": commands}), 400
    
    return jsonify({"commands": commands})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
