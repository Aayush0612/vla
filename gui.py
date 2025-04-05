import tkinter as tk
from tkinter import ttk
import requests
import threading
import time
import os
import json
import tempfile
from PIL import Image, ImageTk

class ROSbotGUI:
    def __init__(self, root, vla_api_url="http://localhost:5000"):
        self.root = root
        self.root.title("ROSbot Controller")
        self.root.geometry("800x600")
        
        self.vla_api_url = vla_api_url
        self.latest_image_path = None
        self.latest_image = None
        
        self.temp_dir = tempfile.gettempdir()
        
        self.command_file = os.path.join(self.temp_dir, "rosbot_commands.json")
        
        print(f"ROSbot GUI initialized. Temp directory: {self.temp_dir}")
        print(f"Command file: {self.command_file}")
        
        self.create_widgets()
        
        self.running = True
        self.update_thread = threading.Thread(target=self.monitor_for_images)
        self.update_thread.daemon = True
        self.update_thread.start()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.image_frame = ttk.Frame(main_frame, borderwidth=2, relief="groove")
        self.image_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        prompt_frame = ttk.Frame(main_frame)
        prompt_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(prompt_frame, text="Prompt:").pack(side=tk.LEFT, padx=5)
        
        self.prompt_var = tk.StringVar()
        self.prompt_entry = ttk.Entry(prompt_frame, textvariable=self.prompt_var, width=50)
        self.prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.prompt_entry.bind("<Return>", self.send_prompt)
        
        self.send_button = ttk.Button(prompt_frame, text="Send", command=self.send_prompt)
        self.send_button.pack(side=tk.LEFT, padx=5)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_image(self, image_path):
        if not os.path.exists(image_path):
            self.status_var.set(f"Error: Image not found at {image_path}")
            return
        
        try:
            pil_image = Image.open(image_path)
            w, h = pil_image.size
            
            display_w = self.image_frame.winfo_width() - 10
            display_h = self.image_frame.winfo_height() - 10
            
            if display_w <= 1 or display_h <= 1:
                display_w, display_h = 700, 400
            
            ratio = min(display_w/w, display_h/h)
            new_size = (int(w * ratio), int(h * ratio))
            
            resized_image = pil_image.resize(new_size, Image.LANCZOS)
            
            tk_image = ImageTk.PhotoImage(resized_image)
            self.image_label.configure(image=tk_image)
            self.image_label.image = tk_image
            
            self.latest_image = tk_image
            self.latest_image_path = image_path
            self.status_var.set(f"Updated image: {os.path.basename(image_path)}")
        
        except Exception as e:
            self.status_var.set(f"Error updating image: {str(e)}")
    
    def monitor_for_images(self):
        last_image_time = 0
        
        while self.running:
            try:
                img_files = [f for f in os.listdir(self.temp_dir) if f.startswith("rosbot_image_") and f.endswith((".jpg", ".bmp"))]
                
                if img_files:
                    img_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.temp_dir, x)), reverse=True)
                    newest_img = img_files[0]
                    img_path = os.path.join(self.temp_dir, newest_img)
                    img_time = os.path.getmtime(img_path)
                    
                    if img_time > last_image_time:
                        last_image_time = img_time
                        self.root.after(100, lambda p=img_path: self.update_image(p))
            
            except Exception as e:
                print(f"Error in monitor thread: {e}")
            
            time.sleep(0.5)
    
    def send_prompt(self, event=None):
        prompt = self.prompt_var.get().strip()
        if not prompt:
            self.status_var.set("Please enter a prompt")
            return
        
        if not self.latest_image_path:
            self.status_var.set("No image available to process")
            return
        
        self.status_var.set(f"Processing prompt: {prompt}")
        
        thread = threading.Thread(target=self.process_prompt_thread, args=(prompt,))
        thread.daemon = True
        thread.start()
    
    def process_prompt_thread(self, prompt):
        try:
            response = requests.post(
                f"{self.vla_api_url}/process-image",
                json={"image_path": self.latest_image_path, "user_prompt": prompt}
            )
            
            if response.status_code == 200:
                result = response.json()
                if "commands" in result:
                    commands = result["commands"]
                    self.root.after(0, lambda: self.status_var.set(f"Commands received: {commands}"))
                    
                    with open(self.command_file, 'w') as f:
                        json.dump({"commands": commands}, f)
                else:
                    self.root.after(0, lambda: self.status_var.set(f"Error: Unexpected API response: {result}"))
            else:
                self.root.after(0, lambda: self.status_var.set(f"Error: API returned {response.status_code}: {response.text}"))
        
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
    
    def on_closing(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    import sys
    vla_api_url = "http://localhost:5000"
    if len(sys.argv) > 1:
        vla_api_url = sys.argv[1]
    
    root = tk.Tk()
    app = ROSbotGUI(root, vla_api_url)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
