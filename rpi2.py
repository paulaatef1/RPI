# ----------------------------------------------------------------
# ---------------------- Import Libraries ------------------------
# ----------------------------------------------------------------
import os
import cv2
import time
import pyttsx3
import threading
import json
import wikipedia
import requests
import pygame.mixer
from datetime import datetime
import speech_recognition as sr
from api_request import detect
from picamera2 import Picamera2, Preview

current_directory = os.path.dirname(__file__)

# ----------------------------------------------------------------
# ----------- Function To Convert The Text Into Speech -----------
# ----------------------------------------------------------------
def speak(text):
    engine = pyttsx3.init() 
    voices = engine.getProperty('voices') 
    engine.setProperty('voice', voices[1].id) 
    engine.say(text)
    engine.runAndWait()

class AiGlassesSystem:
    def __init__(self):
        self.video_loop_active = False
        
        # Initialize Picamera2
        self.picam2 = PiCamera2() 
        self.preview_config = self.picam2.create_preview_configuration()
        self.picam2.configure(self.preview_config)
        self.picam2.start()

        pygame.mixer.init()
        self.system_active = True
        self.object_names =  {'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush', '0.25', '0.50', '1',  '10', '100', '20', '200', '5', '50'}

    def start_system(self):
        voice_thread = threading.Thread(target=self.listen_for_commands)
        voice_thread.start()

    def listen_for_commands(self):
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
        self.speak_and_print("Hello, I am the smart glasses for blind people. I am Listening...", "AI Glasses")

        while self.system_active:
            with microphone as source:
                sound = self.mixer.Sound(os.path.join(current_directory, 'static', 'start.mp3'))
                sound.set_volume(0.3) 
                sound.play()
                recognizer.adjust_for_ambient_noise(source)
                print("AI Glasses: I am Listening...")
                audio = recognizer.listen(source)

            try:
                command = str(recognizer.recognize_google(audio).lower())
                print(f"You Said: {command}")
                
                if  "exit" in command :
                    self.exit()
                
                elif  "detect" in command :
                    self.capture_and_process("object")
                
                if  "money" in command :
                    self.capture_and_process("currency")
                
                if  "describe" in command :
                    self.capture_and_process("describe")
                
                if  "text" in command :
                    self.capture_and_process("text")
                
                elif command.startswith("find"):
                    self.handle_find(command[5:])
                
                elif  "video" in command :
                    self.start_video_loop()
                
                elif  "stop" in command :
                    self.stop_video_loop()
                
                # else:
                #     try:
                #         wiki_res = wikipedia.summary(command, sentences = 1)
                #         self.speak_and_print(wiki_res, "AI Glasses")
                #     except:
                #         print("AI Glasses: Something went wrong!")
                #         continue

            except sr.UnknownValueError:
                print("AI Glasses: Could not understand audio, try again.")
            except sr.RequestError as e:
                print(f"AI Glasses: Error with the speech recognition service; {0}".format(e))

    def handle_find(self, text):
        words = text.split()
        filtered_words = [word for word in words if word.lower() not in ['the', 'a', 'an']]
        object_to_be_found = ' '.join(filtered_words)

        if object_to_be_found in self.object_names:
            self.capture_and_process("find", object_to_be_found)
        else:
            self.speak_and_print(f"{object_to_be_found} Is Not An Object to be found!", "AI Glasses")


    def start_video_loop(self):
        self.video_loop_active = True
        video_loop = threading.Thread(target=self.open_video_capture)
        video_loop.start()

    def stop_video_loop(self):
        self.video_loop_active = False

    def open_video_capture(self, duration=15):
        # if not self.cap.isOpened():
        #     print("Error: Could not open camera.")
        #     return
        self.speak_and_print("Video mode is active for 15 seconds. Say stop to end it.", "AI Glasses")
        start_time = time.time()
        elapsed_time = 0
        while self.video_loop_active and elapsed_time < duration:
            self.capture_and_process("object")
            elapsed_time = time.time() - start_time

        self.speak_and_print("The Video Mode Is Off. i am Listening", "AI Glasses")
        self.stop_video_loop()
        cv2.destroyAllWindows()

    def capture_and_process(self, mode, object_to_be_found=None):
        """Captures an image using Picamera2, saves it, and sends it to the image recognition API.
        """

        self.mixer.Sound(os.path.join(current_directory, 'static', 'camera.mp3')).play()

        # Capture Image using Picamera2 
        image = np.empty((640, 480, 3), dtype=np.uint8)  # Assuming image dimensions are 640x480
        self.picam2.capture(image, format='rgb')
        # or:
        # image = self.picam2.capture_array()  # Capture as a numpy array 
        now = datetime.now()
        image_filename = f"static/uploads/captured_image_{now.strftime('%Y%m%d%H%M%S')}.jpg"
        cv2.imwrite(image_filename, image) 

        # Call the detect function to send the image to your API server
        result = self.detect(image_filename, mode, object_to_be_found)
        if result:
            self.speak_and_print(result, "AI Glasses")
        else:
            self.speak_and_print("Something went wrong with the server!", "AI Glasses")
    
    def speak_and_print(self, text, channel):
        print(f"{channel}: {text}")
        speak(text)

    def exit(self):
        self.speak_and_print("Goodbye, See you soon!", "AI Glasses")
        self.stop_video_loop()
        self.system_active = False

# Example usage
ai_glasses = AiGlassesSystem()
ai_glasses.start_system()
