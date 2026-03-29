from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage
from src.utils.video_thread import VideoThread

class VideoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread = None
        self.old_threads = []
        
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel("Kamera seçmek için lütfen sol taraftaki listeden 'Bağlan'a tıklayın")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #000000; color: #aaaaaa; font-size: 18px; font-weight: bold;")
        
        self.layout.addWidget(self.image_label)

    def start_stream(self, rtsp_url):
        # Stop existing thread
        if self.thread is not None:
            self.thread.change_pixmap_signal.disconnect()
            self.thread.status_signal.disconnect()
            self.thread.stop()
            self.old_threads.append(self.thread)
            
        # Clean up finished old threads gracefully
        self.old_threads = [t for t in self.old_threads if t.isRunning()]
            
        self.image_label.setText("Bağlanılıyor...")
        
        self.thread = VideoThread(rtsp_url)
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.status_signal.connect(self.update_status)
        self.thread.start()

    def stop_stream(self):
        if self.thread is not None:
            self.thread.change_pixmap_signal.disconnect()
            self.thread.status_signal.disconnect()
            self.thread.stop()
            self.old_threads.append(self.thread)
            self.thread = None
            self.image_label.clear()
            self.image_label.setText("Yayın Durduruldu")

    def update_image(self, qt_image: QImage):
        pixmap = QPixmap.fromImage(qt_image)
        # Scale to match label size holding aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)

    def update_status(self, status: str):
        if "Canlı" not in status:
            self.image_label.clear()
            self.image_label.setText(status)

    def closeEvent(self, event):
        self.stop_stream()
        super().closeEvent(event)
