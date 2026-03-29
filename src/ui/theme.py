DARK_THEME_QSS = """
QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
}

QPushButton {
    background-color: #2b2b2b;
    border: 1px solid #3c3c3c;
    border-radius: 6px;
    padding: 8px 16px;
    color: #ffffff;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #383838;
    border-color: #505050;
}

QPushButton:pressed {
    background-color: #007acc;
    border-color: #007acc;
}

/* Primary Action Button (Add/Save) */
QPushButton#primaryButton {
    background-color: #0e639c;
    border-color: #0e639c;
}
QPushButton#primaryButton:hover {
    background-color: #1177bb;
}

/* Danger Button */
QPushButton#dangerButton {
    background-color: #c94f4f;
    border-color: #c94f4f;
}
QPushButton#dangerButton:hover {
    background-color: #dd5a5a;
}
QPushButton#dangerButton:pressed {
    background-color: #a33b3b;
}

QLineEdit, QSpinBox {
    background-color: #252526;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 6px;
    color: #cccccc;
    selection-background-color: #007acc;
}

QLineEdit:focus, QSpinBox:focus {
    border: 1px solid #007acc;
}

QLabel {
    color: #cccccc;
}

/* QDialog/QMessageBox specific styling */
QDialog {
    background-color: #1e1e1e;
}

QGroupBox {
    border: 1px solid #3c3c3c;
    border-radius: 8px;
    margin-top: 1ex;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #007acc;
}

/* Device Card Styling */
QFrame#deviceCard {
    background-color: #252526;
    border: 1px solid #3c3c3c;
    border-radius: 10px;
}
QFrame#deviceCard:hover {
    border-color: #505050;
}
QLabel#deviceCardTitle {
    font-size: 18px;
    font-weight: bold;
    color: #007acc;
}
QLabel#deviceCardIP {
    font-size: 13px;
    color: #9cdcfe;
}

QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollArea > QWidget > QWidget {
    background-color: transparent;
}
"""
