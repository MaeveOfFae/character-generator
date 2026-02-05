"""Validate directory screen for Qt6 GUI."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from pathlib import Path


class ValidateScreen(QWidget):
    """Validate any directory screen."""
    
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("✓ Validate Directory")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #9b59b6; margin: 10px;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Validate any character pack directory for missing files, "
            "placeholders, content mode consistency, and user-authorship violations."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #888; margin: 10px;")
        layout.addWidget(instructions)
        
        # Directory input
        input_layout = QHBoxLayout()
        
        input_label = QLabel("Directory Path:")
        input_label.setFixedWidth(100)
        input_layout.addWidget(input_label)
        
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("e.g., output/character_name or drafts/20240101_120000_...")
        input_layout.addWidget(self.dir_input)
        
        browse_btn = QPushButton("📁 Browse")
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self.browse_directory)
        input_layout.addWidget(browse_btn)
        
        layout.addLayout(input_layout)
        
        # Button row
        btn_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Back")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(self.go_back)
        btn_layout.addWidget(back_btn)
        
        btn_layout.addStretch()
        
        self.validate_btn = QPushButton("✓ Validate")
        self.validate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a2d5f;
                padding: 10px 20px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #5a3d6f;
            }
        """)
        self.validate_btn.clicked.connect(self.run_validation)
        btn_layout.addWidget(self.validate_btn)
        
        layout.addLayout(btn_layout)
        
        # Results area
        results_label = QLabel("Validation Results:")
        results_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(results_label)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Courier New", 10))
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                border: 2px solid #444;
                padding: 10px;
            }
        """)
        layout.addWidget(self.results_text)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; margin: 5px;")
        layout.addWidget(self.status_label)
    
    def go_back(self):
        """Go back to home screen."""
        main_window = self.parent()  # type: ignore
        if main_window and hasattr(main_window, 'show_home'):
            main_window.show_home()  # type: ignore
    
    def browse_directory(self):
        """Browse for directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Validate",
            str(Path.cwd())
        )
        
        if dir_path:
            self.dir_input.setText(dir_path)
    
    def run_validation(self):
        """Run validation on the directory."""
        dir_path = self.dir_input.text().strip()
        
        if not dir_path:
            self.status_label.setText("❌ Please enter a directory path")
            self.status_label.setStyleSheet("color: #f44;")
            return
        
        path = Path(dir_path)
        
        if not path.exists():
            self.status_label.setText(f"❌ Directory not found: {dir_path}")
            self.status_label.setStyleSheet("color: #f44;")
            return
        
        if not path.is_dir():
            self.status_label.setText(f"❌ Not a directory: {dir_path}")
            self.status_label.setStyleSheet("color: #f44;")
            return
        
        self.status_label.setText("⏳ Validating...")
        self.status_label.setStyleSheet("color: #888;")
        self.results_text.clear()
        
        try:
            from ..validate import validate_pack
            
            result = validate_pack(path)
            
            # Format output
            output = []
            output.append(f"📁 Directory: {path}\\n")
            output.append("=" * 60)
            output.append("")
            
            if result["valid"]:
                output.append("✓ VALIDATION PASSED")
                output.append("")
                output.append("All checks passed:")
                for check in result.get("checks_passed", []):
                    output.append(f"  ✓ {check}")
            else:
                output.append("✗ VALIDATION FAILED")
                output.append("")
                
                if result.get("errors"):
                    output.append("Errors:")
                    for error in result["errors"]:
                        output.append(f"  ✗ {error}")
                    output.append("")
                
                if result.get("warnings"):
                    output.append("Warnings:")
                    for warning in result["warnings"]:
                        output.append(f"  ⚠ {warning}")
            
            output.append("")
            output.append("=" * 60)
            
            self.results_text.setPlainText("\\n".join(output))
            
            if result["valid"]:
                self.status_label.setText("✓ Validation passed")
                self.status_label.setStyleSheet("color: #4a4;")
            else:
                self.status_label.setText(f"✗ Validation failed with {len(result.get('errors', []))} errors")
                self.status_label.setStyleSheet("color: #f44;")
        
        except Exception as e:
            self.results_text.setPlainText(f"Error during validation:\\n{e}")
            self.status_label.setText(f"❌ Validation error: {e}")
            self.status_label.setStyleSheet("color: #f44;")
