from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, 
    QSlider, QHBoxLayout, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

class PTZButton(QPushButton):
    pressed_signal = pyqtSignal()
    released_signal = pyqtSignal()

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(50, 50)
        self.setStyleSheet("""
            QPushButton {
                background-color: #333;
                border: 1px solid #555;
                font-size: 18px;
                color: white;
            }
            QPushButton:pressed {
                background-color: #555;
            }
            QPushButton:disabled {
                background-color: #222;
                color: #555;
            }
        """)
        
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.pressed_signal.emit()
            
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.released_signal.emit()

class PTZPanel(QWidget):
    move_requested = pyqtSignal(float, float, float) # pan, tilt, zoom
    stop_requested = pyqtSignal()
    goto_preset_requested = pyqtSignal(int)
    set_preset_requested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self.setup_ui()
        self.set_active(False, "Bağlı Değil")

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # Status Label
        self.lbl_status = QLabel("ONVIF PTZ")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("font-weight: bold; color: #fff;")
        main_layout.addWidget(self.lbl_status)

        # D-Pad Group
        dpad_group = QGroupBox("Yön Kontrolü")
        dpad_group.setStyleSheet("QGroupBox { color: #ccc; }")
        dpad_layout = QGridLayout(dpad_group)
        dpad_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_up = PTZButton("↑")
        self.btn_left = PTZButton("←")
        self.btn_right = PTZButton("→")
        self.btn_down = PTZButton("↓")

        dpad_layout.addWidget(self.btn_up, 0, 1)
        dpad_layout.addWidget(self.btn_left, 1, 0)
        # Empty center (could be home)
        dpad_layout.addWidget(self.btn_right, 1, 2)
        dpad_layout.addWidget(self.btn_down, 2, 1)

        # Bind events
        self.bind_move(self.btn_up, 0.0, 1.0, 0.0)
        self.bind_move(self.btn_down, 0.0, -1.0, 0.0)
        self.bind_move(self.btn_left, -1.0, 0.0, 0.0)
        self.bind_move(self.btn_right, 1.0, 0.0, 0.0)

        main_layout.addWidget(dpad_group)

        # Zoom Group
        zoom_group = QGroupBox("Zoom")
        zoom_group.setStyleSheet("QGroupBox { color: #ccc; }")
        zoom_layout = QHBoxLayout(zoom_group)
        zoom_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_zoom_out = PTZButton("-")
        self.btn_zoom_in = PTZButton("+")
        
        self.bind_move(self.btn_zoom_out, 0.0, 0.0, -1.0)
        self.bind_move(self.btn_zoom_in, 0.0, 0.0, 1.0)

        zoom_layout.addWidget(self.btn_zoom_out)
        zoom_layout.addWidget(self.btn_zoom_in)
        main_layout.addWidget(zoom_group)

        # Presets Group
        preset_group = QGroupBox("Ön Ayarlar (Presets)")
        preset_group.setStyleSheet("QGroupBox { color: #ccc; }")
        preset_layout = QVBoxLayout(preset_group)

        self.btn_save_mode = QPushButton("Kaydetme Modu: KAPALI")
        self.btn_save_mode.setCheckable(True)
        self.btn_save_mode.setStyleSheet("""
            QPushButton { background-color: #444; color: white; padding: 5px; }
            QPushButton:checked { background-color: #f44336; font-weight: bold; }
        """)
        self.btn_save_mode.toggled.connect(self.toggle_save_mode)
        preset_layout.addWidget(self.btn_save_mode)

        btn_row = QHBoxLayout()
        for i in range(1, 4):
            btn = QPushButton(str(i))
            btn.setFixedSize(40, 40)
            btn.setStyleSheet("background-color: #555; color: white; font-weight: bold;")
            btn.clicked.connect(lambda checked, idx=i: self.preset_clicked(idx))
            btn_row.addWidget(btn)
        
        preset_layout.addLayout(btn_row)
        main_layout.addWidget(preset_group)

        main_layout.addStretch()

    def bind_move(self, button, p, t, z):
        button.pressed_signal.connect(lambda: self.move_requested.emit(p, t, z))
        button.released_signal.connect(self.stop_requested.emit)

    def toggle_save_mode(self, checked):
        if checked:
            self.btn_save_mode.setText("Kaydetme Modu: AÇIK")
        else:
            self.btn_save_mode.setText("Kaydetme Modu: KAPALI")

    def preset_clicked(self, idx):
        if self.btn_save_mode.isChecked():
            self.set_preset_requested.emit(idx)
            self.btn_save_mode.setChecked(False) # Turn off after saving
            print(f"Preset {idx} saved.")
            QMessageBox.information(self, "Bilgi", f"Pozisyon Ön Ayar {idx} olarak kaydedildi.")
        else:
            self.goto_preset_requested.emit(idx)
            print(f"Going to preset {idx}.")

    def set_active(self, active: bool, msg: str = ""):
        self.setEnabled(active)
        if active:
            self.lbl_status.setText("PTZ Aktif")
            self.lbl_status.setStyleSheet("color: #4caf50; font-weight: bold;")
        else:
            self.lbl_status.setText(msg or "PTZ Devre Dışı")
            self.lbl_status.setStyleSheet("color: #f44336; font-weight: bold;")
