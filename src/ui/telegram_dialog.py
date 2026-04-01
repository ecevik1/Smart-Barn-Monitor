import requests
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QWidget, QFormLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.utils.config_manager import ConfigManager

class TelegramTestWorker(QThread):
    result_signal = pyqtSignal(bool, str) # success, message

    def __init__(self, bot_token, chat_id):
        super().__init__()
        self.bot_token = bot_token
        self.chat_id = chat_id

    def run(self):
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": "🐄 Smart Barn Monitor - Bağlantı Testi Başarılı!"
            }
            # Set a timeout so UI doesn't hang infinitely
            response = requests.post(url, json=payload, timeout=5)
            
            if response.status_code == 200:
                self.result_signal.emit(True, "Başarılı!")
            elif response.status_code in [401, 404]:
                self.result_signal.emit(False, "Geçersiz Bot Token.")
            elif response.status_code == 400:
                self.result_signal.emit(False, "Geçersiz Chat ID.")
            else:
                self.result_signal.emit(False, f"Hata Kodu: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            self.result_signal.emit(False, "İnternet Bağlantısı Yok.")
        except requests.exceptions.Timeout:
            self.result_signal.emit(False, "Bağlantı Zaman Aşımına Uğradı.")
        except Exception as e:
            self.result_signal.emit(False, f"Sistem Hatası: {str(e)}")


class TelegramDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Telegram Ayarları")
        self.setMinimumWidth(450) # Remove setFixedSize to allow dynamic resizing
        self.worker = None
        
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Info Label
        info = QLabel("Telegram Bot @BotFather üzerinden alınan Token ve\\nbildirimin gideceği Chat ID bilgilerinizi giriniz.")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #aaaaaa; margin-bottom: 10px;")
        layout.addWidget(info)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Bot Token
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Örn: 123456789:ABCdefHTuN...")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setMinimumHeight(35)
        form_layout.addRow("Bot Token:", self.token_input)
        
        # Chat ID
        self.chat_id_input = QLineEdit()
        self.chat_id_input.setPlaceholderText("Örn: 987654321")
        self.chat_id_input.setMinimumHeight(35)
        form_layout.addRow("Chat ID:", self.chat_id_input)
        
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
        btn_layout.addStretch() # Push buttons to the right
        
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
        conf = ConfigManager.get_telegram_config()
        self.token_input.setText(conf.get("bot_token", ""))
        self.chat_id_input.setText(conf.get("chat_id", ""))

    def test_connection(self):
        token = self.token_input.text().strip()
        chat_id = self.chat_id_input.text().strip()
        
        if not token or not chat_id:
            self.show_status(False, "Lütfen Token ve Chat ID girin.")
            return
            
        self.btn_test.setEnabled(False)
        self.btn_test.setText("Test Ediliyor...")
        self.status_label.hide()
        
        self.worker = TelegramTestWorker(bot_token=token, chat_id=chat_id)
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
        self.adjustSize() # Automatically adjust window size if label forces expansion

    def save_and_close(self):
        token = self.token_input.text().strip()
        chat_id = self.chat_id_input.text().strip()
        
        if ConfigManager.save_telegram_config(token, chat_id):
            self.accept()
        else:
            QMessageBox.critical(self, "Hata", "Ayarlar kaydedilemedi.")
