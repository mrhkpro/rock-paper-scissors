import cv2
import mediapipe as mp
import random
import time
import threading
import tkinter as tk
from tkinter import messagebox

# تنظیمات پیشرفته MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


class HandGame:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_gui()
        self.camera_index = 0
        self.running = False
        self.countdown = 5
        self.last_gesture = ""
        
        # تنظیمات مدل دست
        self.hands = mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.8,
            min_tracking_confidence=0.8,
            static_image_mode=False
        )

    def setup_gui(self):
        self.root.title("بازی دستی")
        self.root.geometry("800x600")
        
        # بخش نمایش تصویر
        self.video_frame = tk.Label(self.root)
        self.video_frame.pack(pady=10)
        
        # بخش اطلاعات
        self.status_label = tk.Label(self.root, text="آماده", font=("Tahoma", 14))
        self.status_label.pack()
        
        # دکمه‌ها
        self.start_btn = tk.Button(self.root, text="شروع بازی", command=self.start_game)
        self.start_btn.pack(pady=5)
        
        self.exit_btn = tk.Button(self.root, text="خروج", command=self.exit_game)
        self.exit_btn.pack()

    def start_game(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.game_loop, daemon=True).start()

    def exit_game(self):
        self.running = False
        self.root.destroy()

    def process_gesture(self, hand_landmarks):
        # مختصات نرمالایز شده
        wrist = hand_landmarks.landmark[0]
        joints = {
            'thumb': hand_landmarks.landmark[4],
            'index': hand_landmarks.landmark[8],
            'middle': hand_landmarks.landmark[12],
            'ring': hand_landmarks.landmark[16],
            'pinky': hand_landmarks.landmark[20]
        }
        
        # محاسبه فواصل
        def is_finger_open(tip, pip):
            return tip.y < pip.y
        
        fingers = {
            'thumb': joints['thumb'].x < hand_landmarks.landmark[3].x,
            'index': is_finger_open(joints['index'], hand_landmarks.landmark[6]),
            'middle': is_finger_open(joints['middle'], hand_landmarks.landmark[10]),
            'ring': is_finger_open(joints['ring'], hand_landmarks.landmark[14]),
            'pinky': is_finger_open(joints['pinky'], hand_landmarks.landmark[18])
        }
        
        # تشخیص حرکت
        open_fingers = sum([fingers['index'], fingers['middle'], fingers['ring'], fingers['pinky']])
        
        if open_fingers == 0:
            return "Rock"
        elif open_fingers == 2 and fingers['index'] and fingers['middle']:
            return "Scissors"
        elif open_fingers == 4:
            return "Paper"
        return "Unknown"

    def update_gui(self, text, color="black"):
        self.status_label.config(text=text, fg=color)

    def game_loop(self):
        cap = cv2.VideoCapture(self.camera_index)
        start_time = time.time()
        
        while self.running:
            success, frame = cap.read()
            if not success:
                continue
            
            # پردازش فریم
            frame = cv2.flip(frame, 1)
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(image_rgb)
            
            # نمایش آناتومی دست
            if results.multi_hand_landmarks:
                for landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame, landmarks, mp_hands.HAND_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(0,255,0), thickness=2),
                        mp_drawing.DrawingSpec(color=(255,0,0), thickness=2),
                        mp_drawing.DrawingSpec(color=(0,0,255), thickness=2)
                    )
                    # تشخیص حرکت
                    gesture = self.process_gesture(landmarks)
                    self.last_gesture = gesture
            
            # نمایش تایمر
            elapsed = time.time() - start_time
            remaining = max(5 - int(elapsed), 0)
            cv2.putText(frame, f"زمان: {remaining}s", (10,30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            
            # تبدیل فریم برای GUI
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, (640, 480))
            photo = tk.PhotoImage(data=cv2.imencode('.png', img)[1].tobytes())
            self.video_frame.config(image=photo)
            self.video_frame.image = photo
            
            # بررسی پایان زمان
            if elapsed >= 5:
                if self.last_gesture != "Unknown":
                    bot_choice = random.choice(["Rock", "Paper", "Scissors"])
                    result = self.decide_winner(self.last_gesture, bot_choice)
                    self.update_gui(f"شما: {self.last_gesture} | کامپیوتر: {bot_choice}\nنتیجه: {result}", "green")
                else:
                    self.update_gui("حرکت نامعتبر! دوباره امتحان کنید", "red")
                
                start_time = time.time()
                self.last_gesture = ""
            
            # خروج با کلید Q
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()

    def decide_winner(self, user, bot):
        if user == bot:
            return "مساوی"
        elif (user == "Rock" and bot == "Scissors") or \
             (user == "Scissors" and bot == "Paper") or \
             (user == "Paper" and bot == "Rock"):
            return "شما برنده شدید!"
        return "کامپیوتر برنده شد!"

if __name__ == "__main__":
    game = HandGame()
    game.root.mainloop()
