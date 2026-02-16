"""Qt6 GUI application entry point."""

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor
import sys

from .main_window import MainWindow
from bpui.core.config import Config


def setup_dark_theme(app: QApplication):
    """Apply dark theme to the application."""
    app.setStyle("Fusion")
    
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Base, QColor(40, 40, 40))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(50, 50, 50))
    palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Button, QColor(50, 50, 50))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(100, 150, 255))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(70, 100, 150))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    
    app.setPalette(palette)


def run_gui_app():
    """Run the Qt6 GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Blueprint UI")
    
    setup_dark_theme(app)
    
    config = Config()
    window = MainWindow(config)
    window.show()
    
    sys.exit(app.exec())
