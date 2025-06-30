

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QMainWindow
from PySide6.QtCore import Qt, QObject, Slot, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebChannel import QWebChannel
import sys

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Maximized PySide6 Window")
        # self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        # Maximize the window
        self.showMaximized()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    sys.exit(app.exec())