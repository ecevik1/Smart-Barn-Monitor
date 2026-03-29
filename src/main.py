import sys
import os

# Ensure the root directory is accessible to imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.ui.theme import DARK_THEME_QSS
import os

def main():
    # Setup App Data path if we needed it, but using config.json locally
    if not os.path.exists("config.json"):
        with open("config.json", "w") as f:
            f.write("[]")

    app = QApplication(sys.argv)
    
    # Apply modern dark theme
    app.setStyleSheet(DARK_THEME_QSS)
    
    # Show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
