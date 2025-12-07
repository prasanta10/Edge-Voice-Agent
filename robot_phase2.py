import speech_recognition as sr
import pyttsx3
import whisper
import os
import pywhatkit
import datetime
import warnings
import ollama # Local LLM interface

warnings.filterwarnings("ignore")

# --- CONFIGURATION ---
def speak(text):
    print(f"ROBOT: {text}")
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    try:
        engine.setProperty('voice', voices[1].id) 
    except:
        engine.setProperty('voice', voices[0].id)
        
    engine.setProperty('rate', 160)
    engine.say(text)
    engine.runAndWait()

# --- INITIALIZATION ---
print("Loading Whisper Model...")
model = whisper.load_model("base") 
print("System Ready. Local Brain (Llama 3.2) is active.")

def listen_and_transcribe():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        recognizer.energy_threshold = 300 
        
        try:
            # Listening
            audio = recognizer.listen(source, timeout=5)
            
            # Saving temp file
            with open("temp.wav", "wb") as f:
                f.write(audio.get_wav_data())
            
            # Transcribing with Whisper
            result = model.transcribe("temp.wav", fp16=False)
            
            # Cleanup
            if os.path.exists("temp.wav"):
                os.remove("temp.wav")
                
            return result["text"].strip()
            
        except:
            return ""

# --- THE NEW INTELLIGENCE FUNCTION ---
def ask_brain(question):
    print(" Thinking...")
    try:
        response = ollama.chat(model='llama3.2', messages=[
            {
                'role': 'system', 
                'content': 'You are a helpful AI assistant. Keep your answers brief (max 2 sentences). Do not use markdown.'
            },
            {
                'role': 'user',
                'content': question
            },
        ])
        return response['message']['content']
    except Exception as e:
        return f"I had trouble thinking. Error: {str(e)}"

# --- MAIN CONTROLLER ---
def run_robot():
    speak("I am online and ready to think.")
    
    while True:
        command = listen_and_transcribe()
        
        if command:
            print(f"YOU: {command}")
            command_lower = command.lower()
            
            # 1. Exit Logic
            if "stop" in command_lower or "exit" in command_lower:
                speak("Shutting down.")
                break

            # 2. Automation Logic (The Hands)
            elif "play" in command_lower:
                song = command_lower.replace("play", "").strip()
                speak(f"Playing {song}")
                pywhatkit.playonyt(song)
                
            elif "time" in command_lower:
                now = datetime.datetime.now().strftime("%I:%M %p")
                speak(f"It is {now}")
                
            elif "open notepad" in command_lower:
                speak("Opening Notepad")
                os.system("notepad")

            else:
                # If no simple command matched, ask the LLM
                reply = ask_brain(command)
                speak(reply)

if __name__ == "__main__":
    run_robot()