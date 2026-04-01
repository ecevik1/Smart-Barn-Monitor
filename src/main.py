import sys
import os

# Ensure the root directory is accessible to imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from src.ui.main_window import MainWindow
from src.ui.theme import DARK_THEME_QSS
import traceback
import os

def global_exception_handler(exctype, value, tb):
    """
    Catches all unhandled exceptions globally to prevent silent crashes,
    logs the stack trace into 'crash_log.txt', and safely exits the application.
    """
    traceback_str = ''.join(traceback.format_exception(exctype, value, tb))
    print("Unhandled exception:\n", traceback_str)
    try:
        with open("crash_log.txt", "a", encoding="utf-8") as f:
            f.write("Kritik Hata (Crash):\n" + traceback_str + "\n")
    except:
        pass
    sys.__excepthook__(exctype, value, tb)
    sys.exit(1)

sys.excepthook = global_exception_handler

def main():
    """
    Main entry point for the Smart Barn Monitor application.
    Sets up the global exception handler, initializes the QApplication
    with basic styles, and starts the MainWindow event loop.
    """
    # Setup App Data path if we needed it, but using config.json locally
    if not os.path.exists("config.json"):
        with open("config.json", "w") as f:
            f.write("[]")

    app = QApplication(sys.argv)
    
    # Apply modern dark theme
    app.setStyleSheet(DARK_THEME_QSS)
    
    # Set application icon
    icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.png'))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
