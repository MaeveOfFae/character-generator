"""Template editor for creating/editing template.toml files and their assets."""

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit, QSplitter, QGroupBox,
    QFormLayout, QSpinBox, QCheckBox, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt

from bpui.features.templates.templates import Template, AssetDefinition, TemplateManager
from .blueprint_editor import BlueprintEditor


class TemplateEditor(QDialog):
    """Dialog for editing templates."""

    def __init__(self, parent=None, template: Template = None):
        """Initialize the template editor.
        
        Args:
            parent: Parent widget
            template: The template to edit.
        """
        super().__init__(parent)
        self.template = template
        self.modified = False
        self.template_manager = TemplateManager()
        self.blueprint_content_cache = {}

        self.setWindowTitle("Template Editor")
        self.resize(1200, 800)

        self.setup_ui()

        if self.template:
            self.load_template()

    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("🎨 Template Editor")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #9b59b6; margin: 10px;")
        layout.addWidget(title)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left side: template metadata and asset list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        splitter.addWidget(left_widget)

        # Template Metadata
        meta_group = QGroupBox("Template Metadata")
        meta_layout = QFormLayout(meta_group)
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.on_modified)
        self.description_edit = QLineEdit()
        self.description_edit.textChanged.connect(self.on_modified)
        self.version_major = QSpinBox()
        self.version_major.setMinimum(1)
        self.version_major.valueChanged.connect(self.on_modified)
        self.version_minor = QSpinBox()
        self.version_minor.setMinimum(0)
        self.version_minor.valueChanged.connect(self.on_modified)
        version_layout = QHBoxLayout()
        version_layout.addWidget(self.version_major)
        version_layout.addWidget(QLabel("."))
        version_layout.addWidget(self.version_minor)
        version_layout.addStretch()
        meta_layout.addRow("Name:", self.name_edit)
        meta_layout.addRow("Description:", self.description_edit)
        meta_layout.addRow("Version:", version_layout)
        left_layout.addWidget(meta_group)

        # Asset List
        asset_group = QGroupBox("Assets")
        asset_layout = QVBoxLayout(asset_group)
        self.asset_list = QListWidget()
        self.asset_list.currentItemChanged.connect(self.on_asset_selected)
        asset_layout.addWidget(self.asset_list)
        asset_button_layout = QHBoxLayout()
        add_asset_btn = QPushButton("➕ Add")
        add_asset_btn.clicked.connect(self.add_asset)
        remove_asset_btn = QPushButton("➖ Remove")
        remove_asset_btn.clicked.connect(self.remove_asset)
        asset_button_layout.addWidget(add_asset_btn)
        asset_button_layout.addWidget(remove_asset_btn)
        asset_layout.addLayout(asset_button_layout)
        left_layout.addWidget(asset_group)
        
        # Center: Asset editor
        self.asset_editor = QGroupBox("Asset Editor")
        self.asset_editor.setEnabled(False)
        asset_editor_layout = QFormLayout(self.asset_editor)
        
        self.asset_name_edit = QLineEdit()
        self.asset_name_edit.textChanged.connect(self.on_modified)
        self.asset_required_check = QCheckBox()
        self.asset_required_check.stateChanged.connect(self.on_modified)
        self.asset_depends_on_edit = QLineEdit()
        self.asset_depends_on_edit.textChanged.connect(self.on_modified)
        self.asset_description_edit = QLineEdit()
        self.asset_description_edit.textChanged.connect(self.on_modified)
        self.asset_blueprint_file_edit = QLineEdit()
        self.asset_blueprint_file_edit.textChanged.connect(self.on_modified)

        asset_editor_layout.addRow("Name:", self.asset_name_edit)
        asset_editor_layout.addRow("Required:", self.asset_required_check)
        asset_editor_layout.addRow("Depends On:", self.asset_depends_on_edit)
        asset_editor_layout.addRow("Description:", self.asset_description_edit)
        asset_editor_layout.addRow("Blueprint File:", self.asset_blueprint_file_edit)

        center_widget = self.asset_editor
        splitter.addWidget(center_widget)
        
        # Right side: blueprint content editor
        self.blueprint_editor = QGroupBox("Blueprint Content")
        self.blueprint_editor.setEnabled(False)
        blueprint_editor_layout = QVBoxLayout(self.blueprint_editor)

        self.blueprint_content_edit = QPlainTextEdit()
        self.blueprint_content_edit.textChanged.connect(self.on_modified)
        blueprint_editor_layout.addWidget(self.blueprint_content_edit)

        advanced_editor_btn = QPushButton("Advanced Editor")
        advanced_editor_btn.clicked.connect(self.open_advanced_editor)
        blueprint_editor_layout.addWidget(advanced_editor_btn)

        right_widget = self.blueprint_editor
        splitter.addWidget(right_widget)


        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Save Template")
        save_btn.setStyleSheet("background-color: #2d4a2d; font-weight: bold;")
        save_btn.clicked.connect(self.save_template)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def on_modified(self):
        self.modified = True

    def load_template(self):
        """Load the template data into the UI."""
        self.name_edit.setText(self.template.name)
        self.description_edit.setText(self.template.description)
        
        try:
            major, minor = self.template.version.split('.')
            self.version_major.setValue(int(major))
            self.version_minor.setValue(int(minor))
        except (ValueError, IndexError):
            self.version_major.setValue(1)
            self.version_minor.setValue(0)
            
        self.asset_list.clear()
        for asset in self.template.assets:
            item = QListWidgetItem(asset.name)
            item.setData(Qt.ItemDataRole.UserRole, asset)
            self.asset_list.addItem(item)
        
        self.blueprint_content_cache.clear()
        self.modified = False

    def on_asset_selected(self, current, previous):
        """Handle asset selection."""
        # First, save the previous asset's blueprint content to cache
        if previous:
            asset = previous.data(Qt.ItemDataRole.UserRole)
            if asset:
                self.update_asset_from_ui(asset)
                if self.blueprint_editor.isEnabled():
                    self.blueprint_content_cache[asset.name] = self.blueprint_content_edit.toPlainText()

        self.blueprint_content_edit.clear()
        if not current:
            self.asset_editor.setEnabled(False)
            self.blueprint_editor.setEnabled(False)
            return

        asset = current.data(Qt.ItemDataRole.UserRole)
        if not asset:
            return

        self.asset_editor.setEnabled(True)
        self.asset_name_edit.setText(asset.name)
        self.asset_required_check.setChecked(asset.required)
        self.asset_depends_on_edit.setText(", ".join(asset.depends_on))
        self.asset_description_edit.setText(asset.description)
        self.asset_blueprint_file_edit.setText(asset.blueprint_file or "")

        # Load content from cache or from file
        content = None
        if asset.name in self.blueprint_content_cache:
            content = self.blueprint_content_cache[asset.name]
        else:
            content = self.template_manager.get_blueprint_content(self.template, asset.name)

        if content is not None:
            self.blueprint_content_edit.setPlainText(content)
        else:
            self.blueprint_content_edit.setPlainText("") # Empty for new/missing blueprints
            
        self.blueprint_editor.setEnabled(True) # Always enable if an asset is selected

    def update_asset_from_ui(self, asset):
        """Update an asset object from the UI fields."""
        asset.name = self.asset_name_edit.text()
        asset.required = self.asset_required_check.isChecked()
        asset.depends_on = [s.strip() for s in self.asset_depends_on_edit.text().split(',') if s.strip()]
        asset.description = self.asset_description_edit.text()
        asset.blueprint_file = self.asset_blueprint_file_edit.text()

    def add_asset(self):
        """Add a new asset."""
        name, ok = QInputDialog.getText(self, "Add Asset", "Enter asset name:")
        if ok and name:
            new_asset = AssetDefinition(name=name, blueprint_file=f"{name}.md")
            self.template.assets.append(new_asset)
            item = QListWidgetItem(new_asset.name)
            item.setData(Qt.ItemDataRole.UserRole, new_asset)
            self.asset_list.addItem(item)
            self.asset_list.setCurrentItem(item)
            self.blueprint_content_cache[new_asset.name] = "" # Pre-cache empty content
            self.modified = True

    def remove_asset(self):
        """Remove the selected asset."""
        current_item = self.asset_list.currentItem()
        if not current_item:
            return

        asset = current_item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self,
            "Remove Asset",
            f"Are you sure you want to remove the asset '{asset.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.template.assets.remove(asset)
            if asset.name in self.blueprint_content_cache:
                del self.blueprint_content_cache[asset.name]
            self.asset_list.takeItem(self.asset_list.row(current_item))
            self.modified = True

    def open_advanced_editor(self):
        """Open the advanced blueprint editor."""
        current_item = self.asset_list.currentItem()
        if not current_item:
            return
            
        asset = current_item.data(Qt.ItemDataRole.UserRole)
        if not asset or not asset.blueprint_file:
            # Maybe ask to create one?
            return
            
        blueprint_path = self.template.path / "assets" / asset.blueprint_file
        
        editor = BlueprintEditor(self, blueprint_path=blueprint_path)
        if editor.exec() == QDialog.DialogCode.Accepted:
            self.modified = True
            # Reload content
            content = self.template_manager.get_blueprint_content(self.template, asset.name)
            if content:
                self.blueprint_content_edit.setPlainText(content)

    def save_template(self):
        """Save the template data."""
        if not self.template:
            return

        # Update current asset from UI before saving
        current_item = self.asset_list.currentItem()
        if current_item:
            asset = current_item.data(Qt.ItemDataRole.UserRole)
            if asset:
                self.update_asset_from_ui(asset)
                # also save current editor content to cache
                if self.blueprint_editor.isEnabled():
                    self.blueprint_content_cache[asset.name] = self.blueprint_content_edit.toPlainText()

        # Update template metadata
        self.template.name = self.name_edit.text()
        self.template.description = self.description_edit.text()
        self.template.version = f"{self.version_major.value()}.{self.version_minor.value()}"

        try:
            # Save the template.toml
            self.template_manager.save_template(self.template)

            # Save all blueprint files from cache
            assets_dir = self.template.path / "assets"
            assets_dir.mkdir(exist_ok=True)
            for asset_name, content in self.blueprint_content_cache.items():
                # Find the asset to get the blueprint_file name
                asset_to_save = next((a for a in self.template.assets if a.name == asset_name), None)
                if asset_to_save and asset_to_save.blueprint_file:
                    blueprint_path = assets_dir / asset_to_save.blueprint_file
                    blueprint_path.write_text(content)

            QMessageBox.information(self, "Save Complete", "Template saved successfully.")
            self.modified = False
            self.blueprint_content_cache.clear()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save template: {e}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Close anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        event.accept()
