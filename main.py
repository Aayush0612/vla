# vla_server.py
from flask import Flask, request, jsonify
import ollama
import os

app = Flask(__name__)

def go_ahead(distance_meters):
    return f"go_ahead({distance_meters})"

def go_back(distance_meters):
    return f"go_back({distance_meters})"

def turn_left(angle_degrees):
    return f"turn_left({angle_degrees})"

def turn_right(angle_degrees):
    return f"turn_right({angle_degrees})"

def change_speed(speed_percent):
    return f"change_speed({speed_percent})"

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
- change_speed(speed_percent): Change the robot's movement speed

Provide your response as a list of function calls with appropriate parameters. For example:
[
    "go_ahead(1.5)",
    "turn_left(45)",
]

Return ONLY the command list with NO explanations or additional text.
This will be interpreted as a custom language model for robot control.
"""
    
    try:
        response = ollama.chat(
            model='gemma3:4b',
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

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "up", "service": "VLA Robot Command Service"})

@app.route('/process-image', methods=['POST'])
def process_image_api():
    if not request.json:
        return jsonify({"error": "Invalid JSON payload"}), 400
        
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
    print("Starting VLA Robot Command Server on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000)
