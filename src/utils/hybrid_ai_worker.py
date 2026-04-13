import time
import requests
import io
import cv2
from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal
from google import genai
from src.utils.config_manager import ConfigManager

class HybridAIWorker(QThread):
    status_signal = pyqtSignal(str)     # For general UI updates
    error_signal = pyqtSignal(str)      # Submitting errors
    success_signal = pyqtSignal(str)    # Sent to Telegram

    last_trigger_time = 0.0

    def __init__(self, cv_image, trigger_reason="Görsel Anomali Tespiti"):
        super().__init__()
        self.cv_image = cv_image
        self.trigger_reason = trigger_reason
        self.cooldown_duration = 300 # 5 minutes

    def run(self):
        current_time = time.time()
        # Cooldown Check
        if current_time - HybridAIWorker.last_trigger_time < self.cooldown_duration:
            self.status_signal.emit("Cooldown devrede. Yeni analiz talebi atlandı.")
            return
            
        HybridAIWorker.last_trigger_time = current_time
        
        self.status_signal.emit("Gemini AI'ye fotoğraf gönderiliyor...")
        
        # 1. Convert OpenCV image to PIL Image for Gemini
        try:
            rgb_img = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_img)
            
            # Save to snapshot.jpg as requested to keep a physical copy on disk
            cv2.imwrite("snapshot.jpg", self.cv_image)
        except Exception as e:
            self.error_signal.emit(f"Görüntü işleme hatası: {e}")
            return
            
        # 2. Get API Keys
        g_conf = ConfigManager.get_gemini_config()
        t_conf = ConfigManager.get_telegram_config()
        
        api_key = g_conf.get("api_key")
        model = g_conf.get("model", "gemini-1.5-flash")
        
        bot_token = t_conf.get("bot_token")
        chat_id = t_conf.get("chat_id")
        
        if not api_key:
            self.error_signal.emit("Gemini API Key bulunamadı.")
            return
        if not bot_token or not chat_id:
            self.error_signal.emit("Telegram ayarları eksik.")
            return

        # 3. Call Gemini with Exponential Backoff (Retry on 503)
        analysis_text = ""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                client = genai.Client(api_key=api_key)
                prompt = "Veteriner gözüyle durumu analiz et ve çok kısa bir rapor çıkar."
                
                response = client.models.generate_content(
                    model=model,
                    contents=[prompt, pil_image]
                )
                analysis_text = response.text
                break # Success!
            except Exception as e:
                err_msg = str(e)
                if "503" in err_msg and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) # 1, 2, 4, 8, 16 seconds
                    self.status_signal.emit(f"Gemini yoğun (503). {attempt+1}. deneme {wait_time}s sonra yapılacak...")
                    time.sleep(wait_time)
                else:
                    self.error_signal.emit(f"Gemini API Hatası: {e}")
                    return
            
        self.status_signal.emit("Analiz tamamlandı, Telegram'a gönderiliyor...")
        
        # 4. Telegram'a Gönder
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            
            # Send the saved snapshot
            with open("snapshot.jpg", "rb") as photo:
                payload = {"chat_id": chat_id, "caption": f"🚨 **{self.trigger_reason.upper()}**\n\n{analysis_text}"}
                files = {"photo": photo}
                res = requests.post(url, data=payload, files=files, timeout=15)
                
            if res.status_code == 200:
                self.success_signal.emit("Analiz Telegram'a başarıyla iletildi.")
            else:
                self.error_signal.emit(f"Telegram Hatası: {res.text}")
        except Exception as e:
            self.error_signal.emit(f"Telegram Gönderim Hatası: {e}")
