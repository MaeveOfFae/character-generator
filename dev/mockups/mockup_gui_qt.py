"""PySide6/Qt6 GUI mockup for review screen."""

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTabWidget, QPlainTextEdit, QPushButton, QLabel, QFrame, QStatusBar
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont, QColor, QPalette
except ImportError:
    print("Installing PySide6...")
    import subprocess
    subprocess.check_call(["pip", "install", "PySide6"])
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTabWidget, QPlainTextEdit, QPushButton, QLabel, QFrame, QStatusBar
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont, QColor, QPalette

import sys


class ReviewWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Sample data
        self.assets = {
            "system_prompt": "You are Elara Vance, a cyber-noir detective...\n\n[Sample content would go here]\n" * 10,
            "post_history": "Elara leaned back in her chair, neon signs bleeding...\n\n[Sample content]\n" * 8,
            "character_sheet": "Name: Elara Vance\nAge: 34\nGender: Female\nOccupation: Private Detective\n...\n" * 5,
            "intro_scene": "Rain hammered the streets of Neo-Tokyo...\n\n[Sample scene content]\n" * 6,
            "intro_page": "# Elara Vance\n\nCyber-noir detective with augmented reality implants...\n" * 4,
            "a1111": "[Control]\nModel: SDXL\nSteps: 30\n\n[Positive Prompt]\n1girl, detective...\n" * 3,
            "suno": "[Control]\nStyle: Cyberpunk Jazz\nTempo: 95 BPM\n\n[Verse]\nNeon lights...\n" * 3,
        }
        
        self.edit_mode = False
        
        self.setup_ui()
        self.apply_dark_theme()
    
    def setup_ui(self):
        """Setup the main UI."""
        self.setWindowTitle("Blueprint UI - Review: elara_vance")
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create sections
        self.create_header(main_layout)
        self.create_tabs(main_layout)
        self.create_action_bar(main_layout)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("✓ Ready - All assets loaded successfully")
    
    def create_header(self, parent_layout):
        """Create the header with metadata."""
        header_frame = QFrame()
        header_frame.setFrameShape(QFrame.Shape.StyledPanel)
        header_frame.setLineWidth(2)
        header_layout = QHBoxLayout(header_frame)
        
        # Title
        title = QLabel("📝 Review: elara_vance")
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        # Metadata
        metadata = QLabel("Seed: Cyber-noir detective | Genre: Sci-fi/Noir | Mode: NSFW | Model: deepseek/deepseek-chat")
        metadata_font = QFont("Arial", 10)
        metadata.setFont(metadata_font)
        metadata.setStyleSheet("color: #888;")
        header_layout.addWidget(metadata, stretch=1)
        
        # Quick action buttons
        self.fav_btn = QPushButton("⭐ Favorite")
        self.fav_btn.setFixedWidth(110)
        self.fav_btn.clicked.connect(lambda: self.status_bar.showMessage("Toggled favorite", 2000))
        header_layout.addWidget(self.fav_btn)
        
        tags_btn = QPushButton("🏷️ Tags")
        tags_btn.setFixedWidth(100)
        tags_btn.clicked.connect(lambda: self.status_bar.showMessage("Opening tags editor...", 2000))
        header_layout.addWidget(tags_btn)
        
        genre_btn = QPushButton("🎭 Genre")
        genre_btn.setFixedWidth(100)
        genre_btn.clicked.connect(lambda: self.status_bar.showMessage("Opening genre selector...", 2000))
        header_layout.addWidget(genre_btn)
        
        notes_btn = QPushButton("📝 Notes")
        notes_btn.setFixedWidth(100)
        notes_btn.clicked.connect(lambda: self.status_bar.showMessage("Opening notes editor...", 2000))
        header_layout.addWidget(notes_btn)
        
        parent_layout.addWidget(header_frame)
    
    def create_tabs(self, parent_layout):
        """Create the tabbed text editor area."""
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        
        # Asset tabs
        tabs_data = [
            ("System Prompt", "system_prompt"),
            ("Post History", "post_history"),
            ("Character Sheet", "character_sheet"),
            ("Intro Scene", "intro_scene"),
            ("Intro Page", "intro_page"),
            ("A1111", "a1111"),
            ("Suno", "suno"),
        ]
        
        self.text_editors = {}
        
        for tab_name, asset_key in tabs_data:
            # Create text editor
            editor = QPlainTextEdit()
            editor.setPlainText(self.assets[asset_key])
            editor.setReadOnly(True)
            
            # Set monospace font
            font = QFont("Courier New", 11)
            editor.setFont(font)
            
            # Store reference
            self.text_editors[asset_key] = editor
            
            # Add tab
            self.tab_widget.addTab(editor, tab_name)
        
        parent_layout.addWidget(self.tab_widget, stretch=1)
    
    def create_action_bar(self, parent_layout):
        """Create the action button bar."""
        action_frame = QFrame()
        action_frame.setFrameShape(QFrame.Shape.StyledPanel)
        action_layout = QHBoxLayout(action_frame)
        
        # Left side buttons
        self.edit_btn = QPushButton("✏️ Edit Mode")
        self.edit_btn.setFixedWidth(130)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        action_layout.addWidget(self.edit_btn)
        
        self.save_btn = QPushButton("💾 Save Changes")
        self.save_btn.setFixedWidth(140)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_changes)
        self.save_btn.setStyleSheet("QPushButton:enabled { background-color: #2d5f2d; }")
        action_layout.addWidget(self.save_btn)
        
        regen_btn = QPushButton("🔄 Regenerate Asset")
        regen_btn.setFixedWidth(160)
        regen_btn.clicked.connect(lambda: self.status_bar.showMessage("Regenerating current asset...", 2000))
        action_layout.addWidget(regen_btn)
        
        # Spacer
        action_layout.addStretch()
        
        # Center info
        self.info_label = QLabel("✓ No unsaved changes")
        info_font = QFont("Arial", 10)
        self.info_label.setFont(info_font)
        self.info_label.setStyleSheet("color: #4a4;")
        action_layout.addWidget(self.info_label)
        
        # Spacer
        action_layout.addStretch()
        
        # Right side buttons
        validate_btn = QPushButton("✓ Validate Pack")
        validate_btn.setFixedWidth(130)
        validate_btn.clicked.connect(lambda: self.status_bar.showMessage("Running validation...", 2000))
        action_layout.addWidget(validate_btn)
        
        export_btn = QPushButton("📦 Export")
        export_btn.setFixedWidth(110)
        export_btn.clicked.connect(lambda: self.status_bar.showMessage("Opening export dialog...", 2000))
        export_btn.setStyleSheet("background-color: #4a2d5f;")
        action_layout.addWidget(export_btn)
        
        chat_btn = QPushButton("💬 Chat Assistant")
        chat_btn.setFixedWidth(150)
        chat_btn.clicked.connect(lambda: self.status_bar.showMessage("Opening chat panel...", 2000))
        action_layout.addWidget(chat_btn)
        
        back_btn = QPushButton("⬅️ Back to Home")
        back_btn.setFixedWidth(140)
        back_btn.clicked.connect(self.close)
        action_layout.addWidget(back_btn)
        
        parent_layout.addWidget(action_frame)
    
    def toggle_edit_mode(self):
        """Toggle edit mode for current tab."""
        self.edit_mode = not self.edit_mode
        
        # Get current editor
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, QPlainTextEdit):
            current_widget.setReadOnly(not self.edit_mode)
        
        # Update UI
        if self.edit_mode:
            self.edit_btn.setText("🔒 Read Mode")
            self.save_btn.setEnabled(True)
            self.info_label.setText("⚠️ Edit mode active")
            self.info_label.setStyleSheet("color: #fa4;")
            self.status_bar.showMessage("Edit mode enabled - press Ctrl+S to save")
        else:
            self.edit_btn.setText("✏️ Edit Mode")
            self.save_btn.setEnabled(False)
            self.info_label.setText("✓ No unsaved changes")
            self.info_label.setStyleSheet("color: #4a4;")
            self.status_bar.showMessage("Edit mode disabled")
    
    def save_changes(self):
        """Save changes to current asset."""
        current_index = self.tab_widget.currentIndex()
        tab_name = self.tab_widget.tabText(current_index)
        self.status_bar.showMessage(f"Saved changes to {tab_name}", 3000)
        self.info_label.setText("✓ Changes saved")
        self.info_label.setStyleSheet("color: #4a4;")
    
    def apply_dark_theme(self):
        """Apply dark theme to the application."""
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
        
        self.setPalette(palette)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Modern cross-platform style
    
    window = ReviewWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
