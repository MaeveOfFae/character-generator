"""Template manager screen for Qt6 GUI."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QMessageBox, QInputDialog,
    QFileDialog, QDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from pathlib import Path

from .template_editor import TemplateEditor
from .template_wizard import TemplateWizard


class TemplateManagerScreen(QWidget):
    """Template manager screen."""
    
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.parent_window = parent
        self.templates = []
        self.selected_template = None
        
        self.setup_ui()
        self.load_templates()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Header with back button and title
        header_layout = QHBoxLayout()
        
        # Back button
        self.back_btn = QPushButton("← Back")
        self.back_btn.clicked.connect(self.go_back)
        header_layout.addWidget(self.back_btn)
        
        header_layout.addStretch()
        
        # Title
        title = QLabel("Template Manager")
        title_font = QFont("Arial", 20, QFont.Weight.Bold)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Instructions
        instructions = QLabel(
            "Manage custom blueprint templates. Templates define which assets to generate "
            "and their dependencies."
        )
        instructions.setWordWrap(True)
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
        self.templates_list.currentItemChanged.connect(self.on_template_selected)
        left_layout.addWidget(self.templates_list)
        
        # Template actions
        action_layout = QHBoxLayout()
        
        new_btn = QPushButton("New Template")
        new_btn.clicked.connect(self.new_template)
        action_layout.addWidget(new_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_templates)
        action_layout.addWidget(refresh_btn)

        import_btn = QPushButton("Import")
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
        right_layout.addWidget(self.details_text)
        
        # Detail actions
        detail_action_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton("Validate")
        self.validate_btn.setEnabled(False)
        self.validate_btn.clicked.connect(self.validate_template)
        detail_action_layout.addWidget(self.validate_btn)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self.edit_template)
        detail_action_layout.addWidget(self.edit_btn)

        self.duplicate_btn = QPushButton("Duplicate")
        self.duplicate_btn.setEnabled(False)
        self.duplicate_btn.clicked.connect(self.duplicate_template)
        detail_action_layout.addWidget(self.duplicate_btn)

        self.export_btn = QPushButton("Export")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_template)
        detail_action_layout.addWidget(self.export_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_template)
        detail_action_layout.addWidget(self.delete_btn)
        
        right_layout.addLayout(detail_action_layout)
        
        content_layout.addWidget(right_widget, 2)
        
        layout.addLayout(content_layout)
        
        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
    
    def go_back(self):
        """Return to home screen."""
        if self.parent_window:
            self.parent_window.show_home()
    
    def load_templates(self):
        """Load available templates."""
        from bpui.features.templates.templates import TemplateManager
        
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
            
            self.status_label.setText(f"Loaded {len(self.templates)} templates")

        except Exception as e:
            self.status_label.setText(f"Error loading templates: {e}")
    
    def on_template_selected(self, current, previous):
        """Handle template selection."""
        if not current:
            self.selected_template = None
            self.details_text.clear()
            self.validate_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.duplicate_btn.setEnabled(False)
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
        self.edit_btn.setEnabled(not self.selected_template.is_official)
        self.duplicate_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.delete_btn.setEnabled(not self.selected_template.is_official)
    
    def validate_template(self):
        """Validate selected template with enhanced error reporting."""
        if not self.selected_template:
            return

        from bpui.features.templates.templates import TemplateManager

        try:
            manager = TemplateManager()
            result = manager.validate_template(self.selected_template)

            if not result["errors"] and not result["warnings"]:
                QMessageBox.information(
                    self,
                    "Validation Passed",
                    f"Template '{self.selected_template.name}' is valid and ready to use."
                )
            else:
                message = []
                if result["errors"]:
                    message.append("ERRORS (must be fixed):")
                    for error in result["errors"]:
                        message.append(f"  • {error}")
                    message.append("")

                if result["warnings"]:
                    message.append("WARNINGS (recommended fixes):")
                    for warning in result["warnings"]:
                        message.append(f"  • {warning}")

                QMessageBox.warning(
                    self,
                    "Validation Issues",
                    "\n".join(message)
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Validation Error",
                f"Failed to validate template '{self.selected_template.name}'.\n\n"
                f"Error: {e}\n\n"
                f"Please check that the template files are not corrupted."
            )
    
    def export_template(self):
        """Export selected template with enhanced error reporting."""
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
            from bpui.features.templates.templates import TemplateManager

            manager = TemplateManager()
            output_path = Path(export_dir) / self.selected_template.name.lower().replace(" ", "_")

            # Check if export directory already exists
            if output_path.exists():
                reply = QMessageBox.question(
                    self,
                    "Directory Exists",
                    f"Directory '{output_path.name}' already exists.\n\n"
                    f"Do you want to overwrite it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            manager.export_template(self.selected_template, output_path)

            QMessageBox.information(
                self,
                "Export Complete",
                f"Template '{self.selected_template.name}' exported successfully.\n\n"
                f"Location: {output_path}\n\n"
                f"You can now share this directory or import it on another machine."
            )

        except PermissionError:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Permission denied writing to:\n{export_dir}\n\n"
                f"Please choose a different location or check your permissions."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export template '{self.selected_template.name}'.\n\n"
                f"Error: {e}\n\n"
                f"Please ensure you have write permissions and sufficient disk space."
            )
    
    def import_template(self):
        """Import a template with enhanced error reporting."""
        # Ask for template directory
        template_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Template Directory to Import",
            str(Path.home())
        )

        if not template_dir:
            return

        try:
            from bpui.features.templates.templates import TemplateManager

            template_path = Path(template_dir)

            # Validate template structure before importing
            if not (template_path / "template.toml").exists():
                QMessageBox.warning(
                    self,
                    "Invalid Template",
                    f"The selected directory does not contain a valid template.\n\n"
                    f"Missing: template.toml\n\n"
                    f"Please select a directory that was exported from the template manager."
                )
                return

            manager = TemplateManager()
            template = manager.import_template(template_path)

            if template:
                QMessageBox.information(
                    self,
                    "Import Complete",
                    f"Successfully imported template: {template.name}\n\n"
                    f"The template is now available for use in compilation."
                )
                self.load_templates()
            else:
                QMessageBox.warning(
                    self,
                    "Import Failed",
                    f"Failed to import template from:\n{template_dir}\n\n"
                    f"Possible causes:\n"
                    f"  • Missing or invalid template.toml\n"
                    f"  • Corrupted template files\n"
                    f"  • Template already exists with the same name\n\n"
                    f"Please verify the template directory structure."
                )

        except PermissionError:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Permission denied reading from:\n{template_dir}\n\n"
                f"Please check your read permissions."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to import template.\n\n"
                f"Error: {e}\n\n"
                f"Please check that the directory contains a valid template."
            )
    
    def delete_template(self):
        """Delete selected template with confirmation and enhanced error reporting."""
        if not self.selected_template or self.selected_template.is_official:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete template '{self.selected_template.name}'?\n\n"
            f"This will permanently remove:\n"
            f"  • Template configuration\n"
            f"  • All blueprint files\n"
            f"  • Asset definitions\n\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Default to No for safety
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            from bpui.features.templates.templates import TemplateManager

            manager = TemplateManager()
            if manager.delete_template(self.selected_template):
                QMessageBox.information(
                    self,
                    "Delete Complete",
                    f"Template '{self.selected_template.name}' has been deleted successfully."
                )
                self.load_templates()
            else:
                QMessageBox.warning(
                    self,
                    "Delete Failed",
                    f"Failed to delete template '{self.selected_template.name}'.\n\n"
                    f"The template may be in use or protected."
                )

        except PermissionError:
            QMessageBox.critical(
                self,
                "Delete Error",
                f"Permission denied deleting template '{self.selected_template.name}'.\n\n"
                f"Location: {self.selected_template.path}\n\n"
                f"Please check your write permissions."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Delete Error",
                f"Failed to delete template '{self.selected_template.name}'.\n\n"
                f"Error: {e}\n\n"
                f"The template files may be in use or locked by another process."
            )
    
    def new_template(self):
        """Create a new template using the wizard."""
        wizard = TemplateWizard(self)
        if wizard.exec() == QDialog.DialogCode.Accepted:
            self.load_templates()
    
    def edit_template(self):
        """Edit the selected template."""
        if not self.selected_template or self.selected_template.is_official:
            return
        
        editor = TemplateEditor(self, template=self.selected_template)
        if editor.exec() == QDialog.DialogCode.Accepted:
            self.load_templates()
    
    def duplicate_template(self):
        """Duplicate the selected template."""
        if not self.selected_template:
            return
        
        # Ask for new name
        from PySide6.QtWidgets import QInputDialog
        
        new_name, ok = QInputDialog.getText(
            self,
            "Duplicate Template",
            f"Enter name for duplicated template:",
            text=f"{self.selected_template.name} (Copy)"
        )
        
        if not ok or not new_name.strip():
            return
        
        try:
            from bpui.features.templates.templates import TemplateManager
            import shutil
            
            manager = TemplateManager()
            
            # Create new template directory
            new_dir_name = new_name.strip().lower().replace(" ", "_")
            new_dir = manager.custom_dir / new_dir_name
            
            if new_dir.exists():
                QMessageBox.warning(
                    self,
                    "Duplicate Failed",
                    f"A template named '{new_name}' already exists."
                )
                return
            
            # Copy template directory
            if self.selected_template.is_official:
                # For official template, create custom copy
                new_dir.mkdir(parents=True, exist_ok=True)
                
                # Generate template.toml
                import tomli_w
                template_data = {
                    "template": {
                        "name": new_name.strip(),
                        "version": "1.0.0",
                        "description": f"Copy of {self.selected_template.name}"
                    },
                    "assets": [
                        {
                            "name": asset.name,
                            "required": asset.required,
                            "depends_on": asset.depends_on,
                            "description": asset.description,
                            "blueprint_file": asset.blueprint_file or f"{asset.name}.md"
                        }
                        for asset in self.selected_template.assets
                    ]
                }
                
                with open(new_dir / "template.toml", "wb") as f:
                    tomli_w.dump(template_data, f)
            else:
                # For custom template, copy directory
                shutil.copytree(self.selected_template.path, new_dir)
                
                # Update name in template.toml
                import sys
                if sys.version_info >= (3, 11):
                    import tomllib
                else:
                    import tomli as tomllib
                import tomli_w
                
                toml_path = new_dir / "template.toml"
                with open(toml_path, "rb") as f:
                    data = tomllib.load(f)
                
                data["template"]["name"] = new_name.strip()
                
                with open(toml_path, "wb") as f:
                    tomli_w.dump(data, f)
            
            QMessageBox.information(
                self,
                "Duplicate Complete",
                f"Successfully created duplicate template: {new_name}\n\n"
                f"The new template is now available for editing and use."
            )
            self.load_templates()

        except PermissionError:
            QMessageBox.critical(
                self,
                "Duplicate Error",
                f"Permission denied creating template '{new_name}'.\n\n"
                f"Please check your write permissions."
            )
        except FileNotFoundError as e:
            QMessageBox.critical(
                self,
                "Duplicate Error",
                f"Failed to duplicate template '{self.selected_template.name}'.\n\n"
                f"Some template files are missing:\n{e}\n\n"
                f"The source template may be corrupted."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Duplicate Error",
                f"Failed to duplicate template '{self.selected_template.name}'.\n\n"
                f"Error: {e}\n\n"
                f"Please ensure you have sufficient disk space and write permissions."
            )
