import os

# Reduce stream connection and analysis timeout (stimeout in microseconds/5 seconds)
# This prevents the UI from waiting ~30s for a dead stream to fail.
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;5000|stimeout;5000000|analyzeduration;1000000|probesize;1000000"

import cv2
import time
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    status_signal = pyqtSignal(str)
    anomaly_signal = pyqtSignal(np.ndarray) # Emits the raw cv_img when anomaly occurs

    def __init__(self, rtsp_url):
        super().__init__()
        self._run_flag = True
        self.rtsp_url = rtsp_url
        
        # YOLOv8n initialization
        self.yolo_model = None
        if YOLO:
            try:
                self.yolo_model = YOLO("yolov8n.pt") # Automatically uses CUDA if available
            except Exception as e:
                print(f"[VideoThread] YOLO yüklenemedi: {e}")
                
        self.last_yolo_time = 0.0
        self.latest_frame = None

    def run(self):
        while self._run_flag:
            self.status_signal.emit("Bağlanılıyor...")
            cap = cv2.VideoCapture(self.rtsp_url)
            
            # Gecikmeyi azaltmak için buffer size = 1
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not cap.isOpened():
                if self._run_flag:
                    self.status_signal.emit("Bağlantı Kurulamadı, Yeniden Deneniyor...")
                    time.sleep(3)
                continue

            self.status_signal.emit("Canlı Yayın")
            
            while self._run_flag and cap.isOpened():
                ret, cv_img = cap.read()
                if ret:
                    self.latest_frame = cv_img.copy()
                    now = time.time()
                    
                    # 5 FPS YOLO Inference (every 0.2 seconds)
                    if self.yolo_model and (now - self.last_yolo_time >= 0.2):
                        self.last_yolo_time = now
                        results = self.yolo_model(cv_img, verbose=False)
                        
                        # Anomaly logic: User said Person (0) or Dog (16)
                        # We will trigger if any person is found in the barn stream
                        anomaly_found = False
                        for r in results:
                            for c in r.boxes.cls:
                                class_id = int(c)
                                if class_id == 0 or class_id == 16: # 0: person, 16: dog
                                    anomaly_found = True
                                    break
                                    
                        if anomaly_found:
                            self.anomaly_signal.emit(self.latest_frame)
                    
                        # Optionally explicitly draw boxes for the UI
                        cv_img = results[0].plot()

                    # Görüntüyü BGR'dan RGB'ye çevir
                    qt_img = self.convert_cv_qt(cv_img)
                    self.change_pixmap_signal.emit(qt_img)
                else:
                    self.status_signal.emit("Sinyal Yok, Yeniden Bağlanılıyor...")
                    break # Döngüden çık, yukarıdan tekrar VideoCapture başlatsın
            
            cap.release()
            
            if self._run_flag:
                time.sleep(2) # Kopma durumunda 2 saniye bekle

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap."""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        # Keep aspect ratio dynamically later on UI, convert to generic QImage here
        converted_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        # return .copy() is extremely important, otherwise rgb_image memory is freed and accessing QImage later causes crash
        return converted_format.copy()

    def stop(self):
        self._run_flag = False

