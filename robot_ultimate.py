import speech_recognition as sr
import whisper
import os
import pywhatkit
import datetime
import warnings
import ollama
import threading
import tkinter as tk
from PIL import Image, ImageTk  # <--- NEW: For handling images
import time

# Filter warnings
warnings.filterwarnings("ignore")

# --- CONFIGURATION ---
WAKE_WORD = "jarvis"

# --- 1. THE ROBOT BACKEND (Logic) ---
class VoiceAssistant:
    def __init__(self, gui_callback):
        self.gui_callback = gui_callback
        self.model = whisper.load_model("base")
        self.gui_callback("Ready")

    def speak(self, text):
        self.gui_callback("Speaking")
        print(f"🤖 ROBOT: {text}")
        try:
            safe_text = text.replace('"', '').replace("'", "")
            cmd = f'powershell -Command "Add-Type –AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{safe_text}\');"'
            os.system(cmd)
        except:
            pass
        
    def listen_audio(self, timeout=5, phrase_limit=5):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
                return audio
            except sr.WaitTimeoutError:
                return None
            except:
                return None

    def transcribe_audio(self, audio):
        if not audio: return ""
        try:
            with open("temp.wav", "wb") as f:
                f.write(audio.get_wav_data())
            result = self.model.transcribe("temp.wav", fp16=False)
            if os.path.exists("temp.wav"): os.remove("temp.wav")
            return result["text"].strip()
        except:
            return ""

    def ask_llm(self, question):
        self.gui_callback("Thinking")
        try:
            response = ollama.chat(model='llama3.2', messages=[
                {'role': 'system', 'content': 'You are Jarvis. Answer in 1 sentence.'},
                {'role': 'user', 'content': question}
            ])
            return response['message']['content']
        except:
            return "I can't think right now."

    def execute_command(self, command):
        """Returns True to continue, False to stop"""
        command_lower = command.lower()
        
        if "stop" in command_lower or "exit" in command_lower or "go to sleep" in command_lower:
            self.speak("Going to sleep.")
            return False 

        elif "play" in command_lower:
            song = command_lower.replace("play", "").strip()
            self.speak(f"Playing {song}")
            pywhatkit.playonyt(song)
        elif "time" in command_lower:
            now = datetime.datetime.now().strftime("%I:%M %p")
            self.speak(f"It is {now}")
        elif "open notepad" in command_lower:
            self.speak("Opening Notepad")
            os.system("notepad")
        else:
            reply = self.ask_llm(command)
            self.speak(reply)
            
        return True

    def run(self):
        self.speak(f"System Online.")
        
        while True:
            # OUTER LOOP: SLEEP MODE
            self.gui_callback("Waiting") 
            print(f"\nWaiting for '{WAKE_WORD}'...")
            
            audio = self.listen_audio(timeout=None, phrase_limit=3)
            
            if audio:
                text = self.transcribe_audio(audio).lower()
                if WAKE_WORD in text:
                    print("✅ Wake Word Detected!")
                    self.speak("Yes?")
                    
                    # INNER LOOP: ACTIVE MODE
                    self.gui_callback("Listening")
                    
                    while True:
                        print("   (Active) Listening...")
                        audio_cmd = self.listen_audio(timeout=5, phrase_limit=5)
                        
                        if audio_cmd:
                            command = self.transcribe_audio(audio_cmd)
                            if command:
                                print(f"👤 YOU: {command}")
                                should_continue = self.execute_command(command)
                                if not should_continue: break
                                self.gui_callback("Listening")
                        else:
                            print("❌ Timeout - Sleeping")
                            break 
                            
                    self.gui_callback("Ready")

# --- 2. THE VISUAL GUI (Image Swapper) ---
class AssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis AI")
        self.root.geometry("400x500")
        self.root.configure(bg="#111111")
        self.root.resizable(False, False)

        tk.Label(root, text="JARVIS", font=("Arial", 20, "bold"), fg="#ffffff", bg="#111111").pack(pady=20)

        # 1. LOAD AND RESIZE IMAGES
        self.images = {}
        try:
            # We resize all images to 250x250 pixels to fit the window
            size = (250, 250)
            self.images["Waiting"] = ImageTk.PhotoImage(Image.open("sleep.png").resize(size))
            self.images["Listening"] = ImageTk.PhotoImage(Image.open("awake.png").resize(size))
            self.images["Thinking"] = ImageTk.PhotoImage(Image.open("thinking.png").resize(size))
            
            # Re-use 'awake' for speaking, or add a separate speaking image if you have one
            self.images["Speaking"] = self.images["Listening"] 
            self.images["Ready"] = self.images["Waiting"]

        except Exception as e:
            print(f"Error loading images: {e}")
            print("Make sure sleep.png, awake.png, and thinking.png are in the folder!")
            # Fallback if images fail
            self.images = None

        # 2. IMAGE LABEL (This holds the robot face)
        self.image_label = tk.Label(root, bg="#111111")
        self.image_label.pack(pady=10)
        
        # Set initial image
        if self.images:
            self.image_label.config(image=self.images["Waiting"])

        # Status Text
        self.status_label = tk.Label(root, text="Initializing...", font=("Consolas", 12), fg="#aaaaaa", bg="#111111")
        self.status_label.pack(pady=20)

        self.start_thread()

    def update_status(self, status):
        """Swaps the image based on the robot's state"""
        
        # 1. Update Text
        self.root.after(0, lambda: self.status_label.config(text=status))
        
        # 2. Update Image (if loaded successfully)
        if self.images and status in self.images:
            # We map status to our image dictionary keys
            # Note: "Ready" maps to Waiting/Sleep
            img = self.images.get(status, self.images["Waiting"])
            self.root.after(0, lambda: self.image_label.config(image=img))

    def start_thread(self):
        assistant = VoiceAssistant(self.update_status)
        thread = threading.Thread(target=assistant.run)
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = AssistantGUI(root)
    root.mainloop()