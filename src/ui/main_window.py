from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QScrollArea, QLabel, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt
import sys
import os

from src.ui.device_card import DeviceCard
from src.ui.add_device_dialog import AddDeviceDialog
from src.utils.config_manager import ConfigManager
from src.ui.video_widget import VideoWidget

# Custom Flow Layout for grid-like alignment that wraps
# We could implement a real FlowLayout, but a grid or vertical list of grids is easier
class FlowLayout(QVBoxLayout):
    # A simple wrapper for now to just lay out cards in rows.
    # In a full app, extending a QLayout for Flow is ideal,
    # but for simplicity we will arrange them dynamically.
    pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Barn Monitor")
        self.resize(800, 600)
        self.setup_ui()
        self.load_devices()

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        self.layout_main = QVBoxLayout(main_widget)
        self.layout_main.setContentsMargins(20, 20, 20, 20)
        self.layout_main.setSpacing(20)

        # Header Bar
        header_layout = QHBoxLayout()
        title = QLabel("Smart Barn Monitor")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        
        self.btn_add = QPushButton("+ Yeni Cihaz Ekle")
        self.btn_add.setObjectName("primaryButton")
        self.btn_add.setFixedSize(180, 40)
        self.btn_add.clicked.connect(self.open_add_dialog)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_add)
        
        self.layout_main.addLayout(header_layout)

        # Splitter for Main Content
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.layout_main.addWidget(self.splitter)

        # Scroll Area for Device Cards (Left Side)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setMinimumWidth(320)
        
        self.scroll_widget = QWidget()
        # Instead of FlowLayout, let's use a VBox that holds HBoxes (Rows) for cards.
        self.cards_layout = QVBoxLayout(self.scroll_widget)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll.setWidget(self.scroll_widget)
        self.splitter.addWidget(self.scroll)

        # Video Player Area (Right Side)
        self.video_player = VideoWidget()
        self.video_player.setMinimumWidth(450)
        self.video_player.fullscreen_toggled.connect(self.toggle_fullscreen)
        self.splitter.addWidget(self.video_player)

        # Set stretch factors (Right side gets more space)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 3)

    def open_add_dialog(self, device_id=None):
        dialog = AddDeviceDialog(self, device_id=device_id)
        if dialog.exec():
            self.load_devices() # Refresh list if saved

    def toggle_fullscreen(self, is_fullscreen: bool):
        if is_fullscreen:
            self.scroll.hide()
            self.btn_add.hide()
            self.showFullScreen()
        else:
            self.scroll.show()
            self.btn_add.show()
            self.showNormal()

    def load_devices(self):
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # we have row layouts
                row_layout = item.layout()
                while row_layout.count():
                    child = row_layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                row_layout.deleteLater()

        devices = ConfigManager.load_config()
        
        if not devices:
            empty_lbl = QLabel("Henüz kayıtlı bir cihaz yok. Lütfen sağ üstten ekleyin.")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #888888; font-size: 16px;")
            self.cards_layout.addWidget(empty_lbl)
            return

        # Splitter is narrow, so display 1 card per row
        cards_per_row = 1
        
        row_container = None
        for i, device in enumerate(devices):
            if i % cards_per_row == 0:
                row_container = QHBoxLayout()
                self.cards_layout.addLayout(row_container)
            
            card = DeviceCard(device)
            card.edit_requested.connect(self.open_add_dialog)
            card.delete_requested.connect(self.delete_device)
            card.connect_requested.connect(self.connect_to_device)
            
            row_container.addWidget(card)

        # Fill remaining slots in the last row with stretch
        if row_container and row_container.count() > 0 and row_container.count() < cards_per_row:
            row_container.addStretch()

    def delete_device(self, device_id):
        if ConfigManager.delete_device(device_id):
            self.load_devices()
        else:
            QMessageBox.critical(self, "Hata", "Cihaz silinemedi.")

    def connect_to_device(self, device_id):
        device = ConfigManager.get_device(device_id)
        if device:
            user = device.get('username', '')
            pwd = device.get('password', '')
            ip = device.get('ip', '')
            port = device.get('rtsp_port', 554)
            # Remove leading slash if user typed it, to prevent rtsp://user:pass@ip:port//stream
            path = device.get('rtsp_path', '/stream').lstrip('/')
            
            if user and pwd:
                rtsp_url = f"rtsp://{user}:{pwd}@{ip}:{port}/{path}"
            elif user:
                rtsp_url = f"rtsp://{user}@{ip}:{port}/{path}"
            else:
                rtsp_url = f"rtsp://{ip}:{port}/{path}"
                
            self.video_player.start_stream(rtsp_url)
