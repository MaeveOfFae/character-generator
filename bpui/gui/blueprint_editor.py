"""Blueprint editor for creating/editing blueprint markdown files with YAML frontmatter."""

import re
from pathlib import Path
try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QPlainTextEdit, QSplitter, QGroupBox,
    QFormLayout, QMessageBox, QSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class BlueprintEditor(QDialog):
    """Dialog for editing blueprint markdown files with YAML frontmatter."""
    
    def __init__(self, parent=None, blueprint_path: Optional[Path] = None):
        """Initialize the blueprint editor.
        
        Args:
            parent: Parent widget
            blueprint_path: Path to existing blueprint file (None for new blueprint)
        """
        super().__init__(parent)
        self.blueprint_path = blueprint_path
        self.modified = False
        
        self.setWindowTitle("Blueprint Editor")
        self.resize(1000, 700)
        
        self.setup_ui()
        
        if blueprint_path and blueprint_path.exists():
            self.load_blueprint(blueprint_path)
        else:
            self.set_defaults()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📝 Blueprint Editor")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #9b59b6; margin: 10px;")
        layout.addWidget(title)
        
        # Main splitter (frontmatter left, content right)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Frontmatter editor
        frontmatter_group = QGroupBox("YAML Frontmatter")
        frontmatter_layout = QFormLayout()
        
        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Character Sheet")
        self.name_edit.textChanged.connect(self.on_modified)
        frontmatter_layout.addRow("Name:", self.name_edit)
        
        # Description field
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Brief description of this blueprint")
        self.description_edit.textChanged.connect(self.on_modified)
        frontmatter_layout.addRow("Description:", self.description_edit)
        
        # Invokable checkbox
        self.invokable_check = QCheckBox()
        self.invokable_check.setChecked(True)
        self.invokable_check.stateChanged.connect(self.on_modified)
        frontmatter_layout.addRow("Invokable:", self.invokable_check)
        
        # Version field
        version_layout = QHBoxLayout()
        self.version_major = QSpinBox()
        self.version_major.setMinimum(1)
        self.version_major.setMaximum(99)
        self.version_major.setValue(1)
        self.version_major.valueChanged.connect(self.on_modified)
        version_layout.addWidget(self.version_major)
        
        version_layout.addWidget(QLabel("."))
        
        self.version_minor = QSpinBox()
        self.version_minor.setMinimum(0)
        self.version_minor.setMaximum(99)
        self.version_minor.setValue(0)
        self.version_minor.valueChanged.connect(self.on_modified)
        version_layout.addWidget(self.version_minor)
        
        version_layout.addStretch()
        frontmatter_layout.addRow("Version:", version_layout)
        
        # Frontmatter preview
        frontmatter_preview_label = QLabel("Frontmatter Preview:")
        frontmatter_preview_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        frontmatter_layout.addRow(frontmatter_preview_label)
        
        self.frontmatter_preview = QPlainTextEdit()
        self.frontmatter_preview.setReadOnly(True)
        self.frontmatter_preview.setMaximumHeight(150)
        self.frontmatter_preview.setFont(QFont("Courier New", 9))
        self.frontmatter_preview.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0f0f0f;
                border: 1px solid #444;
                color: #888;
            }
        """)
        frontmatter_layout.addRow(self.frontmatter_preview)
        
        frontmatter_group.setLayout(frontmatter_layout)
        splitter.addWidget(frontmatter_group)
        
        # Right: Markdown content editor
        content_group = QGroupBox("Markdown Content")
        content_layout = QVBoxLayout()
        
        content_help = QLabel(
            "Write the blueprint instructions in Markdown. "
            "The frontmatter will be automatically added."
        )
        content_help.setWordWrap(True)
        content_help.setStyleSheet("color: #888; margin-bottom: 5px; font-size: 11px;")
        content_layout.addWidget(content_help)
        
        self.content_edit = QPlainTextEdit()
        self.content_edit.setFont(QFont("Courier New", 10))
        self.content_edit.setPlaceholderText(
            "Enter blueprint instructions here...\n\n"
            "Example:\n"
            "# Blueprint Agent\n\n"
            "You are the Blueprint Agent.\n\n"
            "When invoked with a SEED, generate...\n"
        )
        self.content_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1a1a1a;
                border: 2px solid #444;
            }
        """)
        self.content_edit.textChanged.connect(self.on_modified)
        self.content_edit.textChanged.connect(self.update_frontmatter_preview)
        content_layout.addWidget(self.content_edit)
        
        content_group.setLayout(content_layout)
        splitter.addWidget(content_group)
        
        # Set splitter proportions (1:2 ratio)
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter)
        
        # Status bar
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; margin: 5px;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.save_btn = QPushButton("💾 Save Blueprint")
        self.save_btn.setStyleSheet("background-color: #2d4a2d; font-weight: bold;")
        self.save_btn.clicked.connect(self.save_blueprint)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
        # Initialize frontmatter preview
        self.update_frontmatter_preview()
    
    def set_defaults(self):
        """Set default values for new blueprint."""
        self.name_edit.setText("New Blueprint")
        self.description_edit.setText("A custom blueprint")
        self.invokable_check.setChecked(True)
        self.version_major.setValue(1)
        self.version_minor.setValue(0)
        self.content_edit.setPlainText(
            "# Blueprint Agent\\n\\n"
            "You are the Blueprint Agent.\\n\\n"
            "When invoked with a SEED, generate..."
        )
        self.modified = False
    
    def load_blueprint(self, path: Path):
        """Load an existing blueprint file.
        
        Args:
            path: Path to blueprint markdown file
        """
        try:
            content = path.read_text()
            frontmatter, body = self.parse_blueprint(content)
            
            # Populate frontmatter fields
            self.name_edit.setText(frontmatter.get("name", ""))
            self.description_edit.setText(frontmatter.get("description", ""))
            self.invokable_check.setChecked(frontmatter.get("invokable", True))
            
            # Parse version
            version_str = str(frontmatter.get("version", "1.0"))
            try:
                if "." in version_str:
                    major, minor = version_str.split(".", 1)
                    self.version_major.setValue(int(major))
                    self.version_minor.setValue(int(minor))
                else:
                    self.version_major.setValue(int(version_str))
                    self.version_minor.setValue(0)
            except ValueError:
                pass
            
            # Set content
            self.content_edit.setPlainText(body)
            
            self.status_label.setText(f"✓ Loaded: {path.name}")
            self.status_label.setStyleSheet("color: #4a4;")
            self.modified = False
            
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load blueprint:\\n{e}")
    
    def parse_blueprint(self, content: str) -> tuple[Dict[str, Any], str]:
        """Parse blueprint markdown file into frontmatter and body.
        
        Args:
            content: Full markdown content with YAML frontmatter
            
        Returns:
            Tuple of (frontmatter dict, body string)
        """
        # Match YAML frontmatter between --- delimiters
        pattern = r'^---\\s*\\n(.*?)\\n---\\s*\\n(.*)$'
        match = re.match(pattern, content, re.DOTALL)
        
        if not match:
            return {}, content
        
        frontmatter_text = match.group(1)
        body = match.group(2)
        
        try:
            # Convert YAML-like to TOML-like by quoting string values
            toml_text = ""
            for line in frontmatter_text.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    if value.lower() not in ("true", "false") and not value.replace(".", "", 1).isdigit():
                        value = f'"{value}"'
                    toml_text += f"{key} = {value}\n"
            
            frontmatter = tomllib.loads(toml_text)
        except (tomllib.TOMLDecodeError, ValueError):
            frontmatter = {}

        return frontmatter, body
    
    def generate_frontmatter(self) -> str:
        """Generate YAML frontmatter from current field values.
        
        Returns:
            YAML frontmatter string with delimiters
        """
        version = f"{self.version_major.value()}.{self.version_minor.value()}"
        invokable = "true" if self.invokable_check.isChecked() else "false"
        
        frontmatter = f"""---
name = "{self.name_edit.text()}"
description = "{self.description_edit.text()}"
invokable = {invokable}
version = {version}
---"""
        return frontmatter
    
    def update_frontmatter_preview(self):
        """Update the frontmatter preview."""
        frontmatter = self.generate_frontmatter()
        self.frontmatter_preview.setPlainText(frontmatter)
    
    def on_modified(self):
        """Handle content modification."""
        self.modified = True
        self.update_frontmatter_preview()
    
    def get_full_content(self) -> str:
        """Get the complete blueprint content (frontmatter + body).
        
        Returns:
            Complete markdown string
        """
        frontmatter = self.generate_frontmatter()
        body = self.content_edit.toPlainText()
        return f"{frontmatter}\\n\\n{body}"
    
    def save_blueprint(self):
        """Save the blueprint to file."""
        if not self.blueprint_path:
            QMessageBox.warning(
                self,
                "No Save Path",
                "Blueprint path not set. Use 'Save to Template' instead."
            )
            return
        
        # Validate before saving
        validation = self.validate_blueprint()
        if not validation["valid"]:
            error_msg = "\\n".join(validation["errors"])
            reply = QMessageBox.question(
                self,
                "Blueprint Validation Failed",
                f"The blueprint has errors:\\n\\n{error_msg}\\n\\nSave anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        try:
            content = self.get_full_content()
            self.blueprint_path.write_text(content)
            
            self.status_label.setText(f"✓ Saved: {self.blueprint_path.name}")
            self.status_label.setStyleSheet("color: #4a4;")
            self.modified = False
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save blueprint:\\n{e}")
    
    def validate_blueprint(self) -> dict:
        """Validate blueprint structure and content.
        
        Returns:
            Dict with 'valid' (bool) and 'errors' (list of strings)
        """
        errors = []
        
        # Validate name
        name = self.name_edit.text().strip()
        if not name:
            errors.append("Blueprint name is required")
        
        # Validate description
        description = self.description_edit.text().strip()
        if not description:
            errors.append("Blueprint description is required")
        
        # Validate version
        version = f"{self.version_major.value()}.{self.version_minor.value()}"
        if not self.version_major.value() > 0:
            errors.append("Version major must be at least 1")
        
        # Validate content
        content = self.content_edit.toPlainText().strip()
        if not content:
            errors.append("Blueprint content is required")
        else:
            # Check for common blueprint sections
            content_lower = content.lower()
            
            # Should have some kind of agent/role definition
            if "agent" not in content_lower and "you are" not in content_lower:
                errors.append("Blueprint should define an agent role (e.g., 'You are the Blueprint Agent')")
            
            # Should have instructions
            if len(content.split('\\n')) < 3:
                errors.append("Blueprint content seems too short - add more instructions")
        
        # Check for template placeholders that should be replaced
        if "{PLACEHOLDER}" in content or "[PLACEHOLDER]" in content:
            errors.append("Blueprint contains placeholder text that should be replaced")
        
        # Check for proper formatting
        if not any(header in content for header in ["#", "##", "###"]):
            errors.append("Blueprint should include section headers (#, ##, ###) for better organization")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def save_to_template(self, template_dir: Path, filename: str) -> bool:
        """Save blueprint to a template directory.
        
        Args:
            template_dir: Template directory path
            filename: Blueprint filename (e.g., 'system_prompt.md')
            
        Returns:
            True if saved successfully
        """
        try:
            assets_dir = template_dir / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)
            
            blueprint_path = assets_dir / filename
            content = self.get_full_content()
            blueprint_path.write_text(content)
            
            self.blueprint_path = blueprint_path
            self.modified = False
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save to template:\\n{e}")
            return False
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Close anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        event.accept()
