from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

class DeviceCard(QFrame):
    # Signals to communicate with the main window
    edit_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    connect_requested = pyqtSignal(str)

    def __init__(self, device_data: dict, parent=None):
        super().__init__(parent)
        self.device_data = device_data
        self.device_id = device_data.get('id', '')
        self.setObjectName("deviceCard")
        self._setup_ui()

    def _setup_ui(self):
        # Allow the frame to style itself properly
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Header: Name and IP
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        
        lbl_name = QLabel(self.device_data.get("name", "Bilinmeyen Kamera"))
        lbl_name.setObjectName("deviceCardTitle")
        lbl_name.setWordWrap(True)
        
        lbl_ip = QLabel(f"IP: {self.device_data.get('ip', 'N/A')} | RTSP: {self.device_data.get('rtsp_port', '554')}")
        lbl_ip.setObjectName("deviceCardIP")

        header_layout.addWidget(lbl_name)
        header_layout.addWidget(lbl_ip)
        main_layout.addLayout(header_layout)

        main_layout.addStretch() # Push buttons to the bottom

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        # Connect button
        self.btn_connect = QPushButton("Bağlan")
        self.btn_connect.setObjectName("primaryButton")
        self.btn_connect.clicked.connect(self._on_connect_clicked)
        
        # Edit/Delete Layout
        action_layout = QHBoxLayout()
        action_layout.setSpacing(5)

        self.btn_edit = QPushButton("Düzenle")
        self.btn_edit.clicked.connect(self._on_edit_clicked)
        
        self.btn_delete = QPushButton("Sil")
        self.btn_delete.setObjectName("dangerButton")
        self.btn_delete.clicked.connect(self._on_delete_clicked)
        
        action_layout.addWidget(self.btn_edit)
        action_layout.addWidget(self.btn_delete)

        btn_layout.addWidget(self.btn_connect, stretch=2)
        btn_layout.addLayout(action_layout, stretch=1)
        
        main_layout.addLayout(btn_layout)

        self.setMinimumSize(250, 160)
        self.setMaximumSize(350, 200)

    def _on_connect_clicked(self):
        self.connect_requested.emit(self.device_id)

    def _on_edit_clicked(self):
        self.edit_requested.emit(self.device_id)

    def _on_delete_clicked(self):
        confirm = QMessageBox.question(
            self,
            "Cihazı Sil",
            f"'{self.device_data.get('name')}' cihazını silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(self.device_id)
