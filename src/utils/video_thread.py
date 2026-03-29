import cv2
import time
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    status_signal = pyqtSignal(str)

    def __init__(self, rtsp_url):
        super().__init__()
        self._run_flag = True
        self.rtsp_url = rtsp_url

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
                    # Görüntüyü BGR'dan RGB'ye çevir
                    qt_img = self.convert_cv_qt(cv_img)
                    self.change_pixmap_signal.emit(qt_img)
                    # 25 FPS = saniyede 1/25 = 0.04 ms
                    time.sleep(0.04)
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
        return converted_format

    def stop(self):
        self._run_flag = False

