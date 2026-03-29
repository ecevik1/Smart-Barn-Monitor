from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QScrollArea, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
import sys
import os

from src.ui.device_card import DeviceCard
from src.ui.add_device_dialog import AddDeviceDialog
from src.utils.config_manager import ConfigManager

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

        # Scroll Area for Device Cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        
        self.scroll_widget = QWidget()
        # Instead of FlowLayout, let's use a VBox that holds HBoxes (Rows) for cards.
        self.cards_layout = QVBoxLayout(self.scroll_widget)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll.setWidget(self.scroll_widget)
        self.layout_main.addWidget(self.scroll)

    def open_add_dialog(self, device_id=None):
        dialog = AddDeviceDialog(self, device_id=device_id)
        if dialog.exec():
            self.load_devices() # Refresh list if saved

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

        # Simple grid system (e.g. 2 cards per row)
        cards_per_row = 2
        
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
        # In this phase, we just show a message.
        # Future phases will launch the stream.
        device = ConfigManager.get_device(device_id)
        if device:
            rtsp_url = f"rtsp://{device.get('username')}:***@{device.get('ip')}:{device.get('rtsp_port')}/stream"
            QMessageBox.information(
                self, 
                "Bağlantı Merkezi", 
                f"Canlı İzleme modülü gelecekte eklenecek.\n(RTSP Bağlantısı Hazırlanıyor...)\n{rtsp_url}"
            )

