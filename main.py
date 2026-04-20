import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from src.ui.main_window import MainWindow
from src.ui.theme import DARK_THEME_QSS

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

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

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
    icon_path = resource_path(os.path.join('assets', 'icons', 'icon.png'))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        dev_icon_path = os.path.join(os.getcwd(), 'assets', 'icons', 'icon.png')
        if os.path.exists(dev_icon_path):
            app.setWindowIcon(QIcon(dev_icon_path))
    
    # Show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
