"""Dependency configuration dialog for selecting asset dependencies."""

from typing import List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QCheckBox
)
from PySide6.QtCore import Qt


class DependencyDialog(QDialog):
    """Dialog for configuring asset dependencies."""
    
    def __init__(self, parent, asset_name: str, available_deps: List[str], current_deps: List[str]):
        """Initialize the dependency dialog.
        
        Args:
            parent: Parent widget
            asset_name: Name of the asset being configured
            available_deps: List of assets that can be dependencies
            current_deps: List of currently selected dependencies
        """
        super().__init__(parent)
        self.asset_name = asset_name
        self.available_deps = available_deps
        self.current_deps = current_deps
        
        self.setWindowTitle(f"Configure Dependencies: {asset_name}")
        self.resize(400, 300)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel(f"🔗 Dependencies for '{self.asset_name}'")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #9b59b6; margin: 10px;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Select which assets this asset depends on. "
            "Dependencies must be generated before this asset. "
            "Only assets that appear earlier in the list are available."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #888; margin: 10px;")
        layout.addWidget(instructions)
        
        # Dependency list
        list_label = QLabel("Available Dependencies:")
        list_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(list_label)
        
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
        
        # Populate list with checkboxes
        for dep_name in self.available_deps:
            item = QListWidgetItem()
            self.dep_list.addItem(item)
            
            checkbox = QCheckBox(dep_name)
            checkbox.setChecked(dep_name in self.current_deps)
            self.dep_list.setItemWidget(item, checkbox)
        
        layout.addWidget(self.dep_list)
        
        if not self.available_deps:
            no_deps = QLabel("ℹ️ No dependencies available (this asset is first in the list)")
            no_deps.setStyleSheet("color: #888; font-style: italic; margin: 10px;")
            layout.addWidget(no_deps)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("✓ Save Dependencies")
        save_btn.setStyleSheet("background-color: #2d4a2d; font-weight: bold;")
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def get_selected_dependencies(self) -> List[str]:
        """Get the list of selected dependencies.
        
        Returns:
            List of dependency asset names
        """
        selected = []
        for i in range(self.dep_list.count()):
            item = self.dep_list.item(i)
            widget = self.dep_list.itemWidget(item)
            if widget and isinstance(widget, QCheckBox):
                if widget.isChecked():
                    selected.append(widget.text())
        return selected
