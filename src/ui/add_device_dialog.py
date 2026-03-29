from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox, 
    QPushButton, QHBoxLayout, QMessageBox, QLabel
)
from PyQt6.QtCore import Qt
import sys
import os

# To ensure the utility modules can be accessed regardless of run location
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.utils.network import test_connection
from src.utils.config_manager import ConfigManager

class AddDeviceDialog(QDialog):
    def __init__(self, parent=None, device_id=None):
        super().__init__(parent)
        self.device_id = device_id  # If not None, we are editing
        self.setup_ui()
        self.load_data_if_editing()

    def setup_ui(self):
        self.setWindowTitle("Cihaz Düzenle" if self.device_id else "Yeni Cihaz Ekle")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)

        # Form Layout
        form_layout = QFormLayout()
        
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Örn: Ahır-1")
        
        self.inp_ip = QLineEdit()
        self.inp_ip.setPlaceholderText("Örn: 192.168.1.50")
        
        self.inp_user = QLineEdit()
        self.inp_user.setPlaceholderText("Kamera Giriş Kullanıcı Adı")
        
        self.inp_pass = QLineEdit()
        self.inp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_pass.setPlaceholderText("Kamera Şifresi")

        self.spin_rtsp = QSpinBox()
        self.spin_rtsp.setRange(1, 65535)
        self.spin_rtsp.setValue(554)
        
        self.spin_onvif = QSpinBox()
        self.spin_onvif.setRange(1, 65535)
        self.spin_onvif.setValue(80)

        self.inp_rtsp_path = QLineEdit()
        self.inp_rtsp_path.setText("/stream")
        self.inp_rtsp_path.setPlaceholderText("Örn: /stream, /h264 vs.")

        form_layout.addRow("Kamera Adı:", self.inp_name)
        form_layout.addRow("IP Adresi:", self.inp_ip)
        form_layout.addRow("Kullanıcı Adı:", self.inp_user)
        form_layout.addRow("Şifre:", self.inp_pass)
        form_layout.addRow("RTSP Port:", self.spin_rtsp)
        form_layout.addRow("ONVIF Port:", self.spin_onvif)
        form_layout.addRow("RTSP Yolu:", self.inp_rtsp_path)

        layout.addLayout(form_layout)

        # Status Label
        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status)

        # Action Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_test = QPushButton("Test Et (Handshake)")
        self.btn_test.clicked.connect(self.test_connection)
        
        self.btn_save = QPushButton("Kaydet")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.clicked.connect(self.save_device)
        
        btn_layout.addWidget(self.btn_test)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

    def load_data_if_editing(self):
        if not self.device_id:
            return
            
        device = ConfigManager.get_device(self.device_id)
        if device:
            self.inp_name.setText(device.get('name', ''))
            self.inp_ip.setText(device.get('ip', ''))
            self.inp_user.setText(device.get('username', ''))
            self.inp_pass.setText(device.get('password', ''))
            self.spin_rtsp.setValue(int(device.get('rtsp_port', 554)))
            self.spin_onvif.setValue(int(device.get('onvif_port', 80)))
            self.inp_rtsp_path.setText(device.get('rtsp_path', '/stream'))

    def validate_inputs(self) -> dict:
        name = self.inp_name.text().strip()
        ip = self.inp_ip.text().strip()
        user = self.inp_user.text().strip()
        pwd = self.inp_pass.text()
        
        if not name or not ip:
            QMessageBox.warning(self, "Eksik Bilgi", "Kamera Adı ve IP Adresi zorunludur.")
            return None
        
        return {
            "name": name,
            "ip": ip,
            "username": user,
            "password": pwd,
            "rtsp_port": self.spin_rtsp.value(),
            "onvif_port": self.spin_onvif.value(),
            "rtsp_path": self.inp_rtsp_path.text()
        }

    def test_connection(self):
        data = self.validate_inputs()
        if not data:
            return
            
        ip = data['ip']
        # We test the RTSP port primarily
        port = data['rtsp_port']
        
        self.lbl_status.setText("Test yapılıyor... Lütfen bekleyin.")
        self.lbl_status.setStyleSheet("color: yellow")
        # In a generic app, connection test is async. For simplicity, we block for 3 seconds max.
        import time
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        success = test_connection(ip, port)
        
        if success:
            self.lbl_status.setText(f"Bağlantı Başarılı! ({ip}:{port})")
            self.lbl_status.setStyleSheet("color: lightgreen")
        else:
            self.lbl_status.setText(f"Bağlantı Başarısız! Cihaza erişilemedi.")
            self.lbl_status.setStyleSheet("color: red")

    def save_device(self):
        data = self.validate_inputs()
        if not data:
            return
        
        if self.device_id:
            success = ConfigManager.update_device(self.device_id, data)
        else:
            success = ConfigManager.add_device(data)
            
        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Hata", "Cihaz kaydedilirken bir hata oluştu.")

