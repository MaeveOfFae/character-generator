"""Template creation wizard for building custom templates step-by-step."""

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QListWidget, QListWidgetItem, QStackedWidget,
    QWidget, QMessageBox, QGroupBox, QFormLayout, QComboBox,
    QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


@dataclass
class AssetDef:
    """Temporary asset definition for wizard."""
    name: str
    required: bool = True
    depends_on: List[str] = field(default_factory=list)
    description: str = ""
    blueprint_source: str = "official"  # "official", "custom", "new"
    blueprint_file: Optional[str] = None


class TemplateWizard(QDialog):
    """Multi-step wizard for creating custom templates."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Template Creation Wizard")
        self.resize(800, 600)
        
        # Template data
        self.template_name = ""
        self.template_version = "1.0.0"
        self.template_description = ""
        self.assets: List[AssetDef] = []
        
        self.current_step = 0
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Title
        self.title_label = QLabel("🎨 Create New Template - Step 1: Basic Info")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #9b59b6; margin: 10px;"
        )
        layout.addWidget(self.title_label)
        
        # Progress indicator
        self.progress_label = QLabel("Step 1 of 4")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("color: #888; margin-bottom: 10px;")
        layout.addWidget(self.progress_label)
        
        # Stacked widget for different steps
        self.stack = QStackedWidget()
        self.stack.addWidget(self.create_basic_info_step())
        self.stack.addWidget(self.create_asset_selection_step())
        self.stack.addWidget(self.create_dependencies_step())
        self.stack.addWidget(self.create_review_step())
        layout.addWidget(self.stack)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        self.back_btn = QPushButton("← Back")
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setEnabled(False)
        nav_layout.addWidget(self.back_btn)
        
        nav_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        nav_layout.addWidget(self.cancel_btn)
        
        self.next_btn = QPushButton("Next →")
        self.next_btn.clicked.connect(self.go_next)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
    
    def create_basic_info_step(self) -> QWidget:
        """Create Step 1: Basic Info."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        instructions = QLabel(
            "Enter basic information about your template. "
            "This identifies the template and its purpose."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #888; margin: 10px;")
        layout.addWidget(instructions)
        
        form_group = QGroupBox("Template Information")
        form_layout = QFormLayout()
        
        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Minimal Character")
        form_layout.addRow("Template Name*:",self.name_input)
        
        # Version
        self.version_input = QLineEdit()
        self.version_input.setText("1.0.0")
        self.version_input.setPlaceholderText("e.g., 1.0.0")
        form_layout.addRow("Version:", self.version_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText(
            "Brief description of what this template generates..."
        )
        self.description_input.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description_input)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        layout.addStretch()
        return widget
    
    def create_asset_selection_step(self) -> QWidget:
        """Create Step 2: Asset Selection."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        instructions = QLabel(
            "Select which assets your template will generate. "
            "You can reorder assets by dragging them. Assets at the top are generated first."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #888; margin: 10px;")
        layout.addWidget(instructions)
        
        # Asset list
        self.asset_list = QListWidget()
        self.asset_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.asset_list.setStyleSheet("""
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
        layout.addWidget(self.asset_list)
        
        # Asset controls
        control_layout = QHBoxLayout()
        
        self.add_asset_btn = QPushButton("➕ Add Asset")
        self.add_asset_btn.clicked.connect(self.add_asset)
        control_layout.addWidget(self.add_asset_btn)
        
        self.edit_asset_btn = QPushButton("✏️ Edit Asset")
        self.edit_asset_btn.clicked.connect(self.edit_asset)
        self.edit_asset_btn.setEnabled(False)
        control_layout.addWidget(self.edit_asset_btn)
        
        self.remove_asset_btn = QPushButton("🗑️ Remove")
        self.remove_asset_btn.clicked.connect(self.remove_asset)
        self.remove_asset_btn.setEnabled(False)
        control_layout.addWidget(self.remove_asset_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        self.asset_list.itemSelectionChanged.connect(self.on_asset_selection_changed)
        
        return widget
    
    def create_dependencies_step(self) -> QWidget:
        """Create Step 3: Dependencies."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        instructions = QLabel(
            "Define dependencies between assets. Each asset can depend on assets "
            "that appear earlier in the list. This ensures the orchestrator generates "
            "them in the correct order."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #888; margin: 10px;")
        layout.addWidget(instructions)
        
        # Dependency configuration
        self.dep_list = QListWidget()
        self.dep_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                border: 2px solid #444;
            }
            QListWidget::item {
                padding: 8px;
            }
        """)
        self.dep_list.itemClicked.connect(self.edit_dependencies)
        layout.addWidget(self.dep_list)
        
        hint = QLabel("💡 Click on an asset to configure its dependencies")
        hint.setStyleSheet("color: #888; font-style: italic; margin: 5px;")
        layout.addWidget(hint)
        
        return widget
    
    def create_review_step(self) -> QWidget:
        """Create Step 4: Review & Create."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        instructions = QLabel(
            "Review your template configuration. Click 'Create Template' to save it."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #888; margin: 10px;")
        layout.addWidget(instructions)
        
        # Preview area
        preview_label = QLabel("Template Preview (template.toml):")
        preview_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(preview_label)
        
        self.review_text = QTextEdit()
        self.review_text.setReadOnly(True)
        self.review_text.setFont(QFont("Courier New", 10))
        self.review_text.setStyleSheet("""
            QTextEdit {
                background-color: #0f0f0f;
                border: 2px solid #444;
                color: #aaa;
            }
        """)
        layout.addWidget(self.review_text)
        
        return widget
    
    def go_next(self):
        """Navigate to next step."""
        # Validate current step
        if self.current_step == 0:
            if not self.validate_basic_info():
                return
            self.save_basic_info()
        elif self.current_step == 1:
            if not self.validate_assets():
                return
            self.prepare_dependencies_step()
        elif self.current_step == 2:
            self.prepare_review_step()
        elif self.current_step == 3:
            # Final step - create template
            self.create_template()
            return
        
        # Move to next step
        self.current_step += 1
        self.stack.setCurrentIndex(self.current_step)
        self.update_navigation()
    
    def go_back(self):
        """Navigate to previous step."""
        if self.current_step > 0:
            self.current_step -= 1
            self.stack.setCurrentIndex(self.current_step)
            self.update_navigation()
    
    def update_navigation(self):
        """Update navigation buttons and title based on current step."""
        steps = [
            "Step 1: Basic Info",
            "Step 2: Asset Selection",
            "Step 3: Dependencies",
            "Step 4: Review & Create"
        ]
        
        self.title_label.setText(f"🎨 Create New Template - {steps[self.current_step]}")
        self.progress_label.setText(f"Step {self.current_step + 1} of 4")
        
        self.back_btn.setEnabled(self.current_step > 0)
        
        if self.current_step == 3:
            self.next_btn.setText("✓ Create Template")
            self.next_btn.setStyleSheet("background-color: #2d4a2d; font-weight: bold;")
        else:
            self.next_btn.setText("Next →")
            self.next_btn.setStyleSheet("")
    
    def validate_basic_info(self) -> bool:
        """Validate Step 1."""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Missing Name", "Please enter a template name.")
            return False
        return True
    
    def save_basic_info(self):
        """Save Step 1 data."""
        self.template_name = self.name_input.text().strip()
        self.template_version = self.version_input.text().strip() or "1.0.0"
        self.template_description = self.description_input.toPlainText().strip()
    
    def validate_assets(self) -> bool:
        """Validate Step 2."""
        if len(self.assets) == 0:
            QMessageBox.warning(
                self,
                "No Assets",
                "Please add at least one asset to your template."
            )
            return False
        return True
    
    def add_asset(self):
        """Add a new asset."""
        from .asset_designer import AssetDesignerDialog
        
        dialog = AssetDesignerDialog(self, existing_assets=[a.name for a in self.assets])
        if dialog.exec() == QDialog.DialogCode.Accepted:
            asset = AssetDef(
                name=dialog.asset_name,
                required=dialog.is_required,
                description=dialog.description,
                blueprint_source=dialog.blueprint_source,
                blueprint_file=dialog.blueprint_file
            )
            self.assets.append(asset)
            self.refresh_asset_list()
    
    def edit_asset(self):
        """Edit selected asset."""
        current = self.asset_list.currentRow()
        if current < 0:
            return
        
        from .asset_designer import AssetDesignerDialog
        
        asset = self.assets[current]
        existing = [a.name for a in self.assets if a.name != asset.name]
        
        dialog = AssetDesignerDialog(self, asset=asset, existing_assets=existing)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            asset.name = dialog.asset_name
            asset.required = dialog.is_required
            asset.description = dialog.description
            asset.blueprint_source = dialog.blueprint_source
            asset.blueprint_file = dialog.blueprint_file
            self.refresh_asset_list()
    
    def remove_asset(self):
        """Remove selected asset."""
        current = self.asset_list.currentRow()
        if current < 0:
            return
        
        asset = self.assets[current]
        reply = QMessageBox.question(
            self,
            "Remove Asset",
            f"Remove asset '{asset.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.assets[current]
            self.refresh_asset_list()
    
    def refresh_asset_list(self):
        """Refresh the asset list widget."""
        # Save current order
        for i in range(self.asset_list.count()):
            item = self.asset_list.item(i)
            asset_name = item.data(Qt.ItemDataRole.UserRole)
            # Find asset and update order
            for j, asset in enumerate(self.assets):
                if asset.name == asset_name:
                    # Move to position i
                    self.assets.insert(i, self.assets.pop(j))
                    break
        
        # Rebuild list
        self.asset_list.clear()
        for asset in self.assets:
            source_icon = {"official": "📋", "custom": "🔷", "new": "✨"}
            label = f"{source_icon.get(asset.blueprint_source, '📄')} {asset.name}"
            if not asset.required:
                label += " (optional)"
            
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, asset.name)
            self.asset_list.addItem(item)
    
    def on_asset_selection_changed(self):
        """Handle asset selection change."""
        has_selection = self.asset_list.currentRow() >= 0
        self.edit_asset_btn.setEnabled(has_selection)
        self.remove_asset_btn.setEnabled(has_selection)
    
    def prepare_dependencies_step(self):
        """Prepare Step 3: Dependencies."""
        self.dep_list.clear()
        for asset in self.assets:
            label = f"{asset.name}"
            if asset.depends_on:
                label += f" → depends on: {', '.join(asset.depends_on)}"
            else:
                label += " (no dependencies)"
            
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, asset.name)
            self.dep_list.addItem(item)
    
    def edit_dependencies(self, item):
        """Edit dependencies for an asset."""
        asset_name = item.data(Qt.ItemDataRole.UserRole)
        asset = next((a for a in self.assets if a.name == asset_name), None)
        if not asset:
            return
        
        # Find available dependencies (assets that come before this one)
        asset_index = self.assets.index(asset)
        available = [a.name for a in self.assets[:asset_index]]
        
        if not available:
            QMessageBox.information(
                self,
                "No Dependencies Available",
                f"'{asset.name}' is first in the list, so it cannot depend on other assets."
            )
            return
        
        from .dependency_dialog import DependencyDialog
        dialog = DependencyDialog(self, asset.name, available, asset.depends_on[:])
        if dialog.exec() == QDialog.DialogCode.Accepted:
            asset.depends_on = dialog.get_selected_dependencies()
            self.prepare_dependencies_step()
    
    def prepare_review_step(self):
        """Prepare Step 4: Review."""
        toml_content = self.generate_toml()
        self.review_text.setPlainText(toml_content)
    
    def generate_toml(self) -> str:
        """Generate template.toml content."""
        lines = []
        lines.append("[template]")
        lines.append(f'name = "{self.template_name}"')
        lines.append(f'version = "{self.template_version}"')
        lines.append(f'description = "{self.template_description}"')
        lines.append("")
        
        for asset in self.assets:
            lines.append("[[assets]]")
            lines.append(f'name = "{asset.name}"')
            lines.append(f"required = {'true' if asset.required else 'false'}")
            # Format dependencies list
            deps_list = ', '.join(f'"{d}"' for d in asset.depends_on)
            lines.append(f"depends_on = [{deps_list}]")
            lines.append(f'description = "{asset.description}"')
            if asset.blueprint_file:
                lines.append(f'blueprint_file = "{asset.blueprint_file}"')
            lines.append("")
        
        return "\\n".join(lines)
    
    def create_template(self):
        """Create the template."""
        try:
            from bpui.features.templates.templates import TemplateManager
            
            manager = TemplateManager()
            
            # Create template directory
            template_dir_name = self.template_name.lower().replace(" ", "_")
            template_dir = manager.custom_dir / template_dir_name
            
            if template_dir.exists():
                reply = QMessageBox.question(
                    self,
                    "Template Exists",
                    f"Template '{self.template_name}' already exists. Overwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            template_dir.mkdir(parents=True, exist_ok=True)
            
            # Write template.toml
            toml_path = template_dir / "template.toml"
            toml_path.write_text(self.generate_toml(), encoding='utf-8')
            
            # Create assets directory
            assets_dir = template_dir / "assets"
            assets_dir.mkdir(exist_ok=True)
            
            QMessageBox.information(
                self,
                "Template Created",
                f"✓ Template '{self.template_name}' created successfully!\\n\\n"
                f"Location: {template_dir}"
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Creation Error", f"Failed to create template:\\n{e}")
