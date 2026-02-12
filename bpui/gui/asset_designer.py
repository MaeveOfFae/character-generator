"""Asset designer dialog for configuring individual assets in a template."""

from pathlib import Path
from typing import List, Optional, Dict
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QRadioButton, QButtonGroup, QGroupBox,
    QFormLayout, QCheckBox, QMessageBox, QListWidget, QListWidgetItem,
    QSplitter, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt


class AssetDesignerDialog(QDialog):
    """Dialog for designing/editing a single asset."""
    
    def __init__(self, parent=None, asset=None, existing_assets: Optional[List[str]] = None):
        """Initialize the asset designer dialog.
        
        Args:
            parent: Parent widget
            asset: Existing AssetDef to edit (None for new asset)
            existing_assets: List of existing asset names (to prevent duplicates)
        """
        super().__init__(parent)
        self.existing_assets = existing_assets or []
        self.editing = asset is not None
        
        asset_name = asset.name if asset else "New Asset"
        self.setWindowTitle("Asset Designer" if not self.editing else f"Edit Asset: {asset_name}")
        self.resize(500, 400)
        
        self.setup_ui()
        
        if asset:
            self.load_asset(asset)
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("✨ Configure Asset")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #9b59b6; margin: 10px;")
        layout.addWidget(title)
        
        # Basic info
        info_group = QGroupBox("Asset Information")
        info_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., character_sheet")
        info_layout.addRow("Asset Name*:", self.name_input)
        
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Brief description of this asset...")
        self.description_input.setMaximumHeight(60)
        info_layout.addRow("Description:", self.description_input)
        
        self.required_check = QCheckBox("Required (must be generated)")
        self.required_check.setChecked(True)
        info_layout.addRow("", self.required_check)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Blueprint source
        source_group = QGroupBox("Blueprint Source")
        source_layout = QVBoxLayout()
        
        self.source_group = QButtonGroup()
        
        self.official_radio = QRadioButton("📋 Browse Blueprints")
        self.official_radio.setToolTip("Browse and select from available blueprints")
        self.source_group.addButton(self.official_radio, 0)
        source_layout.addWidget(self.official_radio)
        
        official_hint = QLabel(
            "   Browse and select from organized blueprint structure (system, templates, examples)"
        )
        official_hint.setStyleSheet("color: #888; font-size: 11px; margin-left: 20px;")
        source_layout.addWidget(official_hint)
        
        browse_btn_layout = QHBoxLayout()
        browse_btn_layout.addSpacing(30)
        self.browse_btn = QPushButton("🔍 Browse Blueprints")
        self.browse_btn.clicked.connect(self.browse_blueprints)
        browse_btn_layout.addWidget(self.browse_btn)
        browse_btn_layout.addStretch()
        source_layout.addLayout(browse_btn_layout)
        
        self.selected_blueprint_label = QLabel("   No blueprint selected")
        self.selected_blueprint_label.setStyleSheet("color: #666; font-size: 11px; margin-left: 20px;")
        source_layout.addWidget(self.selected_blueprint_label)
        
        self.custom_radio = QRadioButton("🔷 Use Custom Blueprint")
        self.custom_radio.setToolTip("Specify a custom blueprint file in this template")
        self.source_group.addButton(self.custom_radio, 1)
        source_layout.addWidget(self.custom_radio)
        
        custom_layout = QHBoxLayout()
        custom_layout.addSpacing(30)
        custom_layout.addWidget(QLabel("Filename:"))
        self.custom_filename_input = QLineEdit()
        self.custom_filename_input.setPlaceholderText("e.g., my_custom_sheet.md")
        self.custom_filename_input.setEnabled(False)
        custom_layout.addWidget(self.custom_filename_input)
        source_layout.addLayout(custom_layout)
        
        self.new_radio = QRadioButton("✨ Create New Blueprint")
        self.new_radio.setToolTip("Create a new blueprint using blueprint editor")
        self.source_group.addButton(self.new_radio, 2)
        source_layout.addWidget(self.new_radio)
        
        new_hint = QLabel(
            "   You'll be able to design the blueprint in the editor after creating the template."
        )
        new_hint.setStyleSheet("color: #888; font-size: 11px; margin-left: 20px;")
        source_layout.addWidget(new_hint)
        
        self.official_radio.setChecked(True)
        self.custom_radio.toggled.connect(
            lambda checked: self.custom_filename_input.setEnabled(checked)
        )
        
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("✓ Save Asset")
        save_btn.setStyleSheet("background-color: #2d4a2d; font-weight: bold;")
        save_btn.clicked.connect(self.save_asset)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def load_asset(self, asset):
        """Load asset data into form."""
        self.name_input.setText(asset.name)
        self.description_input.setPlainText(asset.description)
        self.required_check.setChecked(asset.required)
        
        if asset.blueprint_source == "official":
            self.official_radio.setChecked(True)
        elif asset.blueprint_source == "custom":
            self.custom_radio.setChecked(True)
            if asset.blueprint_file:
                self.custom_filename_input.setText(asset.blueprint_file)
        elif asset.blueprint_source == "new":
            self.new_radio.setChecked(True)
    
    def browse_blueprints(self):
        """Open blueprint browser dialog to select a blueprint."""
        from .blueprint_browser import BlueprintBrowserDialog
        from ..templates import TemplateManager
        
        manager = TemplateManager()
        dialog = BlueprintBrowserDialog(self, manager.official_dir)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            blueprint_name, blueprint_path = dialog.get_selected_blueprint()
            
            if blueprint_name and blueprint_path:
                # Store selected blueprint info
                self.browse_blueprint_name = blueprint_name
                self.browse_blueprint_path = blueprint_path
                
                # Update label
                rel_path = blueprint_path.relative_to(manager.official_dir)
                self.selected_blueprint_label.setText(f"   ✓ {blueprint_name}.md (blueprints/{rel_path})")
                self.selected_blueprint_label.setStyleSheet("color: #4a2; font-size: 11px; margin-left: 20px;")
    
    def save_asset(self):
        """Save asset configuration."""
        # Validate
        asset_name = self.name_input.text().strip()
        
        if not asset_name:
            QMessageBox.warning(self, "Missing Name", "Please enter an asset name.")
            return
        
        # Check for duplicates (except when editing current asset)
        if asset_name in self.existing_assets:
            QMessageBox.warning(
                self,
                "Duplicate Name",
                f"An asset named '{asset_name}' already exists. Please choose a different name."
            )
            return
        
        # Validate custom filename
        if self.custom_radio.isChecked():
            filename = self.custom_filename_input.text().strip()
            if not filename:
                QMessageBox.warning(
                    self,
                    "Missing Filename",
                    "Please enter a filename for custom blueprint."
                )
                return
            if not filename.endswith(".md"):
                QMessageBox.warning(
                    self,
                    "Invalid Filename",
                    "Blueprint filename must end with .md"
                )
                return
        
        # Store data
        self.asset_name = asset_name
        self.description = self.description_input.toPlainText().strip()
        self.is_required = self.required_check.isChecked()
        
        if self.official_radio.isChecked():
            # Check if a blueprint was browsed and selected
            if hasattr(self, 'browse_blueprint_path') and self.browse_blueprint_path:
                # Calculate relative path from blueprints directory
                from ..templates import TemplateManager
                manager = TemplateManager()
                try:
                    rel_path = self.browse_blueprint_path.relative_to(manager.official_dir)
                    self.blueprint_file = str(rel_path)
                    self.blueprint_source = "custom"  # Use relative path
                except ValueError:
                    # Blueprint not under official_dir, use full path
                    self.blueprint_file = str(self.browse_blueprint_path)
                    self.blueprint_source = "custom"
            else:
                # No blueprint browsed, use default naming
                self.blueprint_source = "official"
                self.blueprint_file = f"{asset_name}.md"
        elif self.custom_radio.isChecked():
            self.blueprint_source = "custom"
            self.blueprint_file = self.custom_filename_input.text().strip()
        else:  # new
            self.blueprint_source = "new"
            self.blueprint_file = f"{asset_name}.md"
        
        self.accept()
