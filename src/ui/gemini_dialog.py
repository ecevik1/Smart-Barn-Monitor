from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QWidget, QFormLayout, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.utils.config_manager import ConfigManager
from google import genai

class GeminiTestWorker(QThread):
    result_signal = pyqtSignal(bool, str) # success, message

    def __init__(self, api_key, model):
        super().__init__()
        self.api_key = api_key
        self.model = model

    def run(self):
        try:
            client = genai.Client(api_key=self.api_key)
            # Simple text-only prompt to test connectivity and API key
            response = client.models.generate_content(
                model=self.model,
                contents="TEST: Bağlantı başarılı mı? Lütfen sadece 'BAĞLANTI TAMAM' yaz."
            )
            
            if response.text:
                self.result_signal.emit(True, "Bağlantı Başarılı!")
            else:
                self.result_signal.emit(False, "Boş yanıt alındı.")
                
        except Exception as e:
            self.result_signal.emit(False, f"Bağlantı Hatası: {str(e)}")

class GeminiDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gemini AI Ayarları")
        self.setMinimumWidth(450)
        self.worker = None
        
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        info = QLabel("Hibrit AI için Google Gemini API Key ve Model seçimi.")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #aaaaaa; margin-bottom: 10px;")
        layout.addWidget(info)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("AIzaSy...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setMinimumHeight(35)
        form_layout.addRow("API Key:", self.api_key_input)
        
        # Model Selection
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
            "gemini-1.5-pro",
            "gemini-2.0-flash-exp"
        ])
        self.model_combo.setMinimumHeight(35)
        form_layout.addRow("Model:", self.model_combo)
        
        layout.addLayout(form_layout)
        
        # Status Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold;")
        self.status_label.hide()
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_test = QPushButton("Bağlantıyı Test Et")
        self.btn_test.setMinimumHeight(35)
        self.btn_test.clicked.connect(self.test_connection)
        
        self.btn_save = QPushButton("Kaydet")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setMinimumHeight(35)
        self.btn_save.setMinimumWidth(100)
        self.btn_save.clicked.connect(self.save_and_close)
        
        btn_layout.addWidget(self.btn_test)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)
        
        self.adjustSize()

    def load_config(self):
        conf = ConfigManager.get_gemini_config()
        self.api_key_input.setText(conf.get("api_key", ""))
        
        model = conf.get("model", "gemini-2.5-flash")
        idx = self.model_combo.findText(model)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)

    def test_connection(self):
        api_key = self.api_key_input.text().strip()
        model = self.model_combo.currentText()
        
        if not api_key:
            self.show_status(False, "Lütfen API Key girin.")
            return
            
        self.btn_test.setEnabled(False)
        self.btn_test.setText("Test Ediliyor...")
        self.status_label.hide()
        
        self.worker = GeminiTestWorker(api_key=api_key, model=model)
        self.worker.result_signal.connect(self.on_test_result)
        self.worker.start()

    def on_test_result(self, success: bool, message: str):
        self.show_status(success, message)
        self.btn_test.setEnabled(True)
        self.btn_test.setText("Bağlantıyı Test Et")

    def show_status(self, success: bool, message: str):
        self.status_label.show()
        if success:
            self.status_label.setStyleSheet("color: #4caf50; font-weight: bold;") # Green
            self.status_label.setText(message)
        else:
            self.status_label.setStyleSheet("color: #f44336; font-weight: bold;") # Red
            self.status_label.setText(message)
        self.adjustSize()

    def save_and_close(self):
        api_key = self.api_key_input.text().strip()
        model = self.model_combo.currentText()
        
        if ConfigManager.save_gemini_config(api_key, model):
            self.accept()
        else:
            QMessageBox.critical(self, "Hata", "Gemini ayarları kaydedilemedi.")
