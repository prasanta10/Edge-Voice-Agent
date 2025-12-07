import speech_recognition as sr
import pyttsx3
import whisper
import os
import pywhatkit
import datetime
import warnings
import time

warnings.filterwarnings("ignore")

# --- CONFIGURATION ---
def speak(text):
    print(f"🤖 ROBOT: {text}")
    engine = pyttsx3.init()
    
    # VOICE SETTING: Try 0 for Male, 1 for Female
    voices = engine.getProperty('voices')
    # Use try/except in case specific voice doesn't exist
    try:
        engine.setProperty('voice', voices[1].id) 
    except:
        engine.setProperty('voice', voices[0].id)
        
    engine.setProperty('rate', 160) # Slower is more realistic
    engine.say(text)
    engine.runAndWait()

# --- INITIALIZATION ---
print("⏳ Loading Whisper Model...")
model = whisper.load_model("base") 
print("✅ System Ready.")

def listen_and_transcribe():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        # Higher threshold = less sensitive to background noise
        recognizer.energy_threshold = 300 
        
        try:
            audio = recognizer.listen(source, timeout=5)
            with open("temp.wav", "wb") as f:
                f.write(audio.get_wav_data())
            
            result = model.transcribe("temp.wav", fp16=False)
            os.remove("temp.wav")
            return result["text"].strip().lower()
            
        except:
            return ""

# --- THE AUTOMATION BRAIN ---
def execute_command(command):
    
    # 1. YOUTUBE COMMAND
    if "play" in command:
        song = command.replace("play", "").strip()
        speak(f"Playing {song} on YouTube.")
        pywhatkit.playonyt(song)
    
    # 2. TIME COMMAND
    elif "time" in command:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {current_time}")
        
    # 3. OPEN APPS (Windows)
    elif "open notepad" in command:
        speak("Opening Notepad.")
        os.system("notepad")
        
    elif "open calculator" in command:
        speak("Opening Calculator.")
        os.system("calc")

    # 4. CHAT (Fallback)
    else:
        speak("I heard you, but I don't know that command yet.")

# --- MAIN LOOP ---
if __name__ == "__main__":
    speak("I am online. What can I do for you?")
    
    while True:
        command = listen_and_transcribe()
        
        if command:
            print(f"👤 YOU: {command}")
            
            if "stop" in command or "exit" in command:
                speak("Goodbye.")
                break
                
            execute_command(command)