from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QSlider, QHBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage, QFont
from src.utils.video_thread import VideoThread
from src.utils.audio_processor import AudioProcessor 
from src.utils.hybrid_ai_worker import HybridAIWorker
from src.utils.logger import Logger
import winsound 
import os

class VideoWidget(QWidget):
    fullscreen_toggled = pyqtSignal(bool) # Signal for main window
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread = None
        self.audio_thread = None
        self.old_threads = []
        self.is_fullscreen = False
        self.alarm_active = False
        
        # Flasher timer
        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(self.toggle_warning_visibility)
        self.flash_state = False
        
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Image Label (Background black)
        self.image_label = QLabel("Kamera seçmek için lütfen sol taraftaki listeden 'Bağlan'a tıklayın")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.image_label.setStyleSheet("background-color: #000000; color: #aaaaaa; font-size: 18px; font-weight: bold;")
        
        # Create overlay warning label inside image_label
        self.warning_label = QLabel("UYARI: DOĞUM BELİRTİSİ!", self.image_label)
        self.warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.warning_label.setStyleSheet("color: white; background-color: rgba(255, 0, 0, 150); font-weight: bold;")
        font = QFont("Arial", 24, QFont.Weight.Bold)
        self.warning_label.setFont(font)
        self.warning_label.hide()
        
        self.layout.addWidget(self.image_label, stretch=1)
        
        # Audio Panel
        self.audio_panel = QWidget()
        audio_layout = QHBoxLayout(self.audio_panel)
        audio_layout.setContentsMargins(10, 5, 10, 5)
        
        lbl_audio = QLabel("Canlı Ses:")
        self.audio_bar = QProgressBar()
        self.audio_bar.setRange(0, 100)
        self.audio_bar.setValue(0)
        self.audio_bar.setTextVisible(False)
        self.audio_bar.setStyleSheet("QProgressBar::chunk { background-color: #4caf50; }")
        
        lbl_sens = QLabel("Hassasiyet Eşiği:")
        self.sens_slider = QSlider(Qt.Orientation.Horizontal)
        self.sens_slider.setRange(0, 100)
        self.sens_slider.setValue(60) # Default
        self.sens_slider.valueChanged.connect(self.on_sensitivity_changed)
        
        self.btn_mute = QPushButton("Sessizde")
        self.btn_mute.setCheckable(True)
        self.btn_mute.setChecked(True) # Default to muted
        self.btn_mute.toggled.connect(self.on_mute_toggled)
        
        audio_layout.addWidget(lbl_audio)
        audio_layout.addWidget(self.audio_bar)
        audio_layout.addWidget(lbl_sens)
        audio_layout.addWidget(self.sens_slider)
        audio_layout.addWidget(self.btn_mute)
        
        self.audio_panel.hide() # Show only when streaming
        self.layout.addWidget(self.audio_panel)

    def start_stream(self, rtsp_url):
        self.stop_stream()
        
        self.image_label.setText("Bağlanılıyor...")
        self.audio_panel.show()
        
        # Start Video
        self.thread = VideoThread(rtsp_url)
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.status_signal.connect(self.update_status)
        self.thread.anomaly_signal.connect(lambda img: self.trigger_ai_analysis(img, "Görsel Anomali (İnsan/Köpek)"))
        self.thread.start()
        
        # Start Audio Processor
        sensitivity = self.sens_slider.value()
        self.audio_thread = AudioProcessor(rtsp_url, sensitivity)
        self.audio_thread.set_muted(self.btn_mute.isChecked())
        self.audio_thread.rms_level_signal.connect(self.update_audio_bar)
        self.audio_thread.alarm_signal.connect(self.trigger_alarm)
        self.audio_thread.start()

    def stop_stream(self):
        if self.thread is not None:
            self.thread.change_pixmap_signal.disconnect()
            self.thread.status_signal.disconnect()
            self.thread.stop()
            self.old_threads.append(self.thread)
            self.thread = None
            
        if self.audio_thread is not None:
            self.audio_thread.rms_level_signal.disconnect()
            self.audio_thread.alarm_signal.disconnect()
            self.audio_thread.stop()
            self.old_threads.append(self.audio_thread)
            self.audio_thread = None
            
        # Stop any active AI workers
        if hasattr(self, 'ai_worker') and self.ai_worker and self.ai_worker.isRunning():
            self.ai_worker.terminate()
            self.ai_worker = None
            
        # Clean up finished old threads gracefully
        self.old_threads = [t for t in self.old_threads if t.isRunning()]
            
        self.image_label.clear()
        self.image_label.setText("Yayın Durduruldu")
        self.audio_panel.hide()
        self.audio_bar.setValue(0)
        self.stop_alarm()

    def update_image(self, qt_image: QImage):
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(), 
            Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)

    def update_status(self, status: str):
        if "Canlı" not in status:
            self.image_label.clear()
            self.image_label.setText(status)
            
    def update_audio_bar(self, level: int):
        self.audio_bar.setValue(level)
        # Change bar color if exceeding threshold
        if level >= self.sens_slider.value():
            self.audio_bar.setStyleSheet("QProgressBar::chunk { background-color: #f44336; }")
        else:
            self.audio_bar.setStyleSheet("QProgressBar::chunk { background-color: #4caf50; }")

    def on_sensitivity_changed(self, value):
        if self.audio_thread:
            self.audio_thread.set_sensitivity(value)

    def on_mute_toggled(self, checked):
        if checked:
            self.btn_mute.setText("Sessizde")
        else:
            self.btn_mute.setText("Ses Açık")
            
        if self.audio_thread:
            self.audio_thread.set_muted(checked)

    def trigger_alarm(self):
        if not self.alarm_active:
            self.alarm_active = True
            self.flash_timer.start(500) # Flash every 500ms
            
            # Play sound async
            wav_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'alarm.wav')
            if os.path.exists(wav_path):
                # SND_ASYNC plays without blocking UI. 
                winsound.PlaySound(wav_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                
            # Stop alarm visual after 10 seconds
            QTimer.singleShot(10000, self.stop_alarm)
            
            # TRIGGER AI ANALYSIS FOR SOUND
            if self.thread and self.thread.latest_frame is not None:
                self.trigger_ai_analysis(self.thread.latest_frame, "Ses Anomalisi (Moo Sesi)")
            else:
                Logger.log("Ses alarmı tetiklendi ancak görüntü alınamadığı için AI analizi atlandı.", "app_events.log")

    def trigger_ai_analysis(self, cv_img, reason):
        """Starts a modular AI worker for Gemini analysis and Telegram notification."""
        if hasattr(self, 'ai_worker') and self.ai_worker and self.ai_worker.isRunning():
            Logger.log(f"AI Analizi zaten çalışıyor. Yeni talep ({reason}) atlandı.", "app_events.log")
            return
            
        Logger.log(f"AI Analizi başlatılıyor: {reason}", "app_events.log")
        
        self.ai_worker = HybridAIWorker(cv_img, trigger_reason=reason)
        # Connect signals for status feedback if needed
        self.ai_worker.status_signal.connect(lambda msg: print(f"[AI] {msg}"))
        self.ai_worker.error_signal.connect(lambda err: Logger.log(f"AI Hatası: {err}", "app_events.log"))
        self.ai_worker.success_signal.connect(lambda msg: Logger.log(f"AI Başarılı: {msg}", "app_events.log"))
        self.ai_worker.start()

    def stop_alarm(self):
        self.alarm_active = False
        self.flash_timer.stop()
        self.warning_label.hide()
        # SND_PURGE stops all current playback (or None to stop)
        winsound.PlaySound(None, winsound.SND_PURGE)

    def toggle_warning_visibility(self):
        self.flash_state = not self.flash_state
        if self.flash_state:
            self.warning_label.show()
        else:
            self.warning_label.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep warning label centered in the video
        w, h = 400, 60
        x = (self.image_label.width() - w) // 2
        y = (self.image_label.height() - h) // 2
        self.warning_label.setGeometry(x, y, w, h)

    def mouseDoubleClickEvent(self, event):
        self.is_fullscreen = not self.is_fullscreen
        
        if self.is_fullscreen:
            self.audio_panel.hide()
        else:
            if self.thread is not None:
                self.audio_panel.show()
                
        self.fullscreen_toggled.emit(self.is_fullscreen)

    def closeEvent(self, event):
        self.stop_stream()
        super().closeEvent(event)
