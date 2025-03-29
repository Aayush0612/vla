import ollama
import re
import os
from pathlib import Path

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
    """Pass image and prompt directly to the LLM without modification"""
    # Clean the path string
    image_path = image_path.strip()
    if (image_path.startswith('"') and image_path.endswith('"')) or \
       (image_path.startswith("'") and image_path.endswith("'")):
        image_path = image_path[1:-1]
    
    # Ensure path exists
    if not os.path.exists(image_path):
        return f"Error: Image path does not exist: {image_path}"
    
    # If no user prompt is provided, use a default prompt
    if not user_prompt:
        user_prompt = "Based on this image, generate robot commands for the most logical task."
    
    # Create prompt for the vision model
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
        # Send request with image and prompt
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
        
        # Handle different response structures
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

def parse_action_plan(plan_text):
    """Extract commands from the model's response without modifying them"""
    # Try to find Python list in the response
    list_pattern = r'\[(.*?)\]'
    list_match = re.search(list_pattern, plan_text, re.DOTALL)
    
    if list_match:
        actions_text = list_match.group(1).strip()
        if '\n' in actions_text:
            actions = [action.strip().strip(',').strip('"\'') for action in actions_text.split('\n') if action.strip()]
        else:
            actions = [action.strip().strip(',').strip('"\'') for action in actions_text.split(',')]
        return actions
    
    # Try to find individual function calls if no list is found
    function_pattern = r'([a-zA-Z_]+\([^)]*\))'
    function_calls = re.findall(function_pattern, plan_text)
    
    if function_calls:
        return function_calls
    
    # If no structured commands found, return empty list
    return []

def validate_command(cmd):
    """Minimal validation to ensure command is executable without replacing it"""
    try:
        func_match = re.match(r'([a-zA-Z_]+)\((.*)\)', cmd)
        if not func_match:
            return False
            
        func_name, params_str = func_match.groups()
        
        # Check if function exists
        if func_name not in globals():
            return False
        
        # Allow parameterless functions
        if func_name in ["release", "detect_objects"] and not params_str.strip():
            return True
            
        # For functions with parameters, validate they are numbers
        if params_str:
            params = [p.strip() for p in params_str.split(',')]
            for p in params:
                try:
                    # Skip validation for empty parameters (like optional ones)
                    if p.strip():
                        float(p)
                except ValueError:
                    return False
            
        return True
    except Exception:
        return False

def process_image_and_act(image_path, user_prompt=""):
    """Process image and return commands exactly as the LLM generated them (if valid)"""
    # Get raw response from vision model
    plan_text = get_action_plan(image_path, user_prompt)
    
    # Parse the commands from the response
    commands = parse_action_plan(plan_text)
    
    # Filter out invalid commands but don't replace them
    valid_commands = [cmd for cmd in commands if validate_command(cmd)]
    
    # If no valid commands were found, return the raw response for debugging
    if not valid_commands and commands:
        return ["Error: No valid commands found in model output.", f"Raw output: {plan_text}"]
    elif not valid_commands:
        return ["Error: Model did not generate any commands.", f"Raw output: {plan_text}"]
    
    return valid_commands

if __name__ == "__main__":
    try:
        image_path = input("Enter the path to the image: ")
        user_prompt = input("Enter your instruction (or press Enter for default): ")
        
        commands = process_image_and_act(image_path, user_prompt)
        print("\n".join(commands))
        
    except Exception as e:
        print(f"Error: {str(e)}")
