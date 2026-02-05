"""Template manager screen for Qt6 GUI."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QMessageBox, QInputDialog,
    QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from pathlib import Path


class TemplateManagerScreen(QWidget):
    """Template manager screen."""
    
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.templates = []
        self.selected_template = None
        
        self.setup_ui()
        self.load_templates()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🎨 Template Manager")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #9b59b6; margin: 10px;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Manage custom blueprint templates. Templates define which assets to generate "
            "and their dependencies."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #888; margin: 10px;")
        layout.addWidget(instructions)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Left: Template list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        list_label = QLabel("Available Templates:")
        list_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(list_label)
        
        self.templates_list = QListWidget()
        self.templates_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                border: 2px solid #444;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #4a2d5f;
            }
        """)
        self.templates_list.currentItemChanged.connect(self.on_template_selected)
        left_layout.addWidget(self.templates_list)
        
        # Template actions
        action_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_templates)
        action_layout.addWidget(refresh_btn)
        
        import_btn = QPushButton("📥 Import")
        import_btn.clicked.connect(self.import_template)
        action_layout.addWidget(import_btn)
        
        left_layout.addLayout(action_layout)
        
        content_layout.addWidget(left_widget, 1)
        
        # Right: Template details
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        details_label = QLabel("Template Details:")
        details_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(details_label)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setFont(QFont("Courier New", 10))
        self.details_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                border: 2px solid #444;
            }
        """)
        right_layout.addWidget(self.details_text)
        
        # Detail actions
        detail_action_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton("✓ Validate")
        self.validate_btn.setEnabled(False)
        self.validate_btn.clicked.connect(self.validate_template)
        detail_action_layout.addWidget(self.validate_btn)
        
        self.export_btn = QPushButton("📤 Export")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_template)
        detail_action_layout.addWidget(self.export_btn)
        
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("background-color: #5f2d2d;")
        self.delete_btn.clicked.connect(self.delete_template)
        detail_action_layout.addWidget(self.delete_btn)
        
        right_layout.addLayout(detail_action_layout)
        
        content_layout.addWidget(right_widget, 2)
        
        layout.addLayout(content_layout)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; margin: 5px;")
        layout.addWidget(self.status_label)
    
    def load_templates(self):
        """Load available templates."""
        from ..templates import TemplateManager
        
        self.templates_list.clear()
        self.details_text.clear()
        
        try:
            manager = TemplateManager()
            self.templates = manager.list_templates()
            
            for template in self.templates:
                label = f"{template.name} ({len(template.assets)} assets)"
                if template.is_official:
                    label += " ★"
                
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, template.name)
                self.templates_list.addItem(item)
            
            self.status_label.setText(f"✓ Loaded {len(self.templates)} templates")
            self.status_label.setStyleSheet("color: #4a4;")
        
        except Exception as e:
            self.status_label.setText(f"❌ Error loading templates: {e}")
            self.status_label.setStyleSheet("color: #f44;")
    
    def on_template_selected(self, current, previous):
        """Handle template selection."""
        if not current:
            self.selected_template = None
            self.details_text.clear()
            self.validate_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            return
        
        template_name = current.data(Qt.ItemDataRole.UserRole)
        
        # Find template
        self.selected_template = None
        for template in self.templates:
            if template.name == template_name:
                self.selected_template = template
                break
        
        if not self.selected_template:
            return
        
        # Show details
        details = []
        details.append(f"Name: {self.selected_template.name}")
        details.append(f"Version: {self.selected_template.version}")
        details.append(f"Description: {self.selected_template.description}")
        details.append(f"Location: {self.selected_template.path}")
        details.append(f"Official: {'Yes' if self.selected_template.is_official else 'No'}")
        details.append("")
        details.append(f"Assets ({len(self.selected_template.assets)}):")
        details.append("-" * 40)
        
        for i, asset in enumerate(self.selected_template.assets, 1):
            details.append(f"{i}. {asset.name}")
            details.append(f"   Required: {asset.required}")
            if asset.depends_on:
                details.append(f"   Depends on: {', '.join(asset.depends_on)}")
            if asset.description:
                details.append(f"   Description: {asset.description}")
            if asset.blueprint_file:
                details.append(f"   Blueprint: {asset.blueprint_file}")
            details.append("")
        
        self.details_text.setPlainText("\n".join(details))
        
        # Enable buttons
        self.validate_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.delete_btn.setEnabled(not self.selected_template.is_official)
    
    def validate_template(self):
        """Validate selected template."""
        if not self.selected_template:
            return
        
        from ..templates import TemplateManager
        
        try:
            manager = TemplateManager()
            result = manager.validate_template(self.selected_template)
            
            if not result["errors"] and not result["warnings"]:
                QMessageBox.information(
                    self,
                    "Validation Passed",
                    f"✓ Template '{self.selected_template.name}' is valid!"
                )
            else:
                message = []
                if result["errors"]:
                    message.append("Errors:")
                    for error in result["errors"]:
                        message.append(f"  • {error}")
                    message.append("")
                
                if result["warnings"]:
                    message.append("Warnings:")
                    for warning in result["warnings"]:
                        message.append(f"  • {warning}")
                
                QMessageBox.warning(
                    self,
                    "Validation Issues",
                    "\n".join(message)
                )
        
        except Exception as e:
            QMessageBox.critical(self, "Validation Error", f"Failed to validate: {e}")
    
    def export_template(self):
        """Export selected template."""
        if not self.selected_template:
            return
        
        # Ask for export location
        export_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            str(Path.home())
        )
        
        if not export_dir:
            return
        
        try:
            from ..templates import TemplateManager
            
            manager = TemplateManager()
            output_path = Path(export_dir) / self.selected_template.name.lower().replace(" ", "_")
            manager.export_template(self.selected_template, output_path)
            
            QMessageBox.information(
                self,
                "Export Complete",
                f"✓ Template exported to:\n{output_path}"
            )
        
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export: {e}")
    
    def import_template(self):
        """Import a template."""
        # Ask for template directory
        template_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Template Directory to Import",
            str(Path.home())
        )
        
        if not template_dir:
            return
        
        try:
            from ..templates import TemplateManager
            
            manager = TemplateManager()
            template = manager.import_template(Path(template_dir))
            
            if template:
                QMessageBox.information(
                    self,
                    "Import Complete",
                    f"✓ Imported template: {template.name}"
                )
                self.load_templates()
            else:
                QMessageBox.warning(
                    self,
                    "Import Failed",
                    "Failed to import template. Check that template.toml exists and is valid."
                )
        
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import: {e}")
    
    def delete_template(self):
        """Delete selected template."""
        if not self.selected_template or self.selected_template.is_official:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete template '{self.selected_template.name}'?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            from ..templates import TemplateManager
            
            manager = TemplateManager()
            if manager.delete_template(self.selected_template):
                QMessageBox.information(
                    self,
                    "Delete Complete",
                    f"✓ Deleted template: {self.selected_template.name}"
                )
                self.load_templates()
            else:
                QMessageBox.warning(self, "Delete Failed", "Failed to delete template")
        
        except Exception as e:
            QMessageBox.critical(self, "Delete Error", f"Failed to delete: {e}")
