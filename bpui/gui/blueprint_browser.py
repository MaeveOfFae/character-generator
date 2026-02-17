"""Blueprint browser dialog for browsing and selecting blueprints from organized structure."""

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QGroupBox, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class BlueprintBrowserDialog(QDialog):
    """Dialog for browsing and selecting blueprints from the organized directory structure."""
    
    def __init__(self, parent=None, official_dir: Optional[Path] = None):
        """Initialize blueprint browser dialog.
        
        Args:
            parent: Parent widget
            official_dir: Path to blueprints directory
        """
        super().__init__(parent)
        self.official_dir = official_dir or (Path(__file__).parent.parent.parent / "blueprints")
        self.selected_blueprint = None
        self.selected_path = None
        
        self.setWindowTitle("📋 Blueprint Browser")
        self.resize(900, 600)
        
        self.setup_ui()
        self.load_blueprints()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Browse Available Blueprints")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #9b59b6; margin: 10px;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Browse and select blueprints from the organized structure. "
            "Blueprints are categorized into system, templates, and examples."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #888; margin: 5px;")
        layout.addWidget(instructions)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Blueprint tree
        tree_group = QGroupBox("Blueprints")
        tree_layout = QVBoxLayout()
        
        self.blueprint_tree = QTreeWidget()
        self.blueprint_tree.setHeaderLabel("Blueprint Structure")
        self.blueprint_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #1a1a1a;
                border: 2px solid #444;
            }
            QTreeWidget::item {
                padding: 5px;
            }
            QTreeWidget::item:selected {
                background-color: #4a2d5f;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                border-image: none;
                image: url(:/icons/closed.png);
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                image: url(:/icons/open.png);
            }
        """)
        self.blueprint_tree.itemClicked.connect(self.on_blueprint_selected)
        self.blueprint_tree.itemDoubleClicked.connect(self.on_blueprint_double_clicked)
        tree_layout.addWidget(self.blueprint_tree)
        
        tree_group.setLayout(tree_layout)
        splitter.addWidget(tree_group)
        
        # Right: Preview
        preview_group = QGroupBox("Blueprint Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_label = QLabel("Select a blueprint to preview")
        self.preview_label.setStyleSheet("color: #888; font-style: italic; margin: 10px;")
        preview_layout.addWidget(self.preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Courier New", 9))
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #0f0f0f;
                border: 2px solid #444;
                color: #aaa;
            }
        """)
        preview_layout.addWidget(self.preview_text)
        
        preview_group.setLayout(preview_layout)
        splitter.addWidget(preview_group)
        
        # Set splitter proportions (1:2 ratio)
        splitter.setSizes([300, 600])
        
        layout.addWidget(splitter)
        
        # Path display
        self.path_label = QLabel("")
        self.path_label.setStyleSheet("color: #666; margin: 5px; font-size: 11px;")
        layout.addWidget(self.path_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.select_btn = QPushButton("✓ Select Blueprint")
        self.select_btn.setStyleSheet("background-color: #2d4a2d; font-weight: bold;")
        self.select_btn.setEnabled(False)
        self.select_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.select_btn)
        
        layout.addLayout(button_layout)
    
    def load_blueprints(self):
        """Load blueprints from the organized directory structure."""
        self.blueprint_tree.clear()
        
        if not self.official_dir.exists():
            self.preview_text.setPlainText("Blueprints directory not found.")
            return
        
        # System blueprints
        system_dir = self.official_dir / "system"
        if system_dir.exists():
            system_item = QTreeWidgetItem(self.blueprint_tree)
            system_item.setText(0, "🔧 System Blueprints")
            system_item.setData(0, Qt.ItemDataRole.UserRole, system_dir)
            
            for md_file in sorted(system_dir.glob("*.md")):
                self.add_blueprint_item(system_item, md_file, "system")
        
        # Template blueprints
        templates_dir = self.official_dir / "templates"
        if templates_dir.exists():
            templates_item = QTreeWidgetItem(self.blueprint_tree)
            templates_item.setText(0, "📦 Template Blueprints")
            templates_item.setData(0, Qt.ItemDataRole.UserRole, templates_dir)
            
            for template_dir in sorted(templates_dir.iterdir()):
                if template_dir.is_dir():
                    template_item = QTreeWidgetItem(templates_item)
                    template_item.setText(0, f"📁 {template_dir.name}")
                    
                    for md_file in sorted(template_dir.glob("*.md")):
                        self.add_blueprint_item(template_item, md_file, template_dir.name)
        
        # Example blueprints
        examples_dir = self.official_dir / "examples"
        if examples_dir.exists():
            examples_item = QTreeWidgetItem(self.blueprint_tree)
            examples_item.setText(0, "💡 Example Blueprints")
            examples_item.setData(0, Qt.ItemDataRole.UserRole, examples_dir)
            
            for md_file in sorted(examples_dir.glob("*.md")):
                self.add_blueprint_item(examples_item, md_file, "examples")
        
        # Expand all top-level items
        for i in range(self.blueprint_tree.topLevelItemCount()):
            item = self.blueprint_tree.topLevelItem(i)
            if item is not None:
                item.setExpanded(True)
    
    def add_blueprint_item(self, parent_item: QTreeWidgetItem, blueprint_path: Path, category: str):
        """Add a blueprint file item to the tree.
        
        Args:
            parent_item: Parent tree item
            blueprint_path: Path to blueprint file
            category: Category name for display
        """
        item = QTreeWidgetItem(parent_item)
        item.setText(0, f"📄 {blueprint_path.name}")
        item.setData(0, Qt.ItemDataRole.UserRole, blueprint_path)
        
        # Get description from frontmatter
        try:
            content = blueprint_path.read_text(encoding='utf-8')
            description = self.parse_blueprint_description(content)
            if description:
                item.setToolTip(0, description)
        except Exception:
            pass
    
    def parse_blueprint_description(self, content: str) -> str:
        """Parse description from blueprint frontmatter.
        
        Args:
            content: Blueprint file content
            
        Returns:
            Description string or empty string
        """
        lines = content.split('\n')
        in_frontmatter = False
        
        for line in lines:
            if line.strip() == '---':
                in_frontmatter = not in_frontmatter
                continue
            
            if in_frontmatter and line.startswith('description:'):
                return line.split(':', 1)[1].strip().strip('"')
        
        return ""
    
    def on_blueprint_selected(self, item: QTreeWidgetItem, column: int):
        """Handle blueprint selection.
        
        Args:
            item: Selected tree item
            column: Column index
        """
        blueprint_path = item.data(0, Qt.ItemDataRole.UserRole)
        
        if not blueprint_path or not isinstance(blueprint_path, Path):
            self.preview_label.setText("Select a blueprint to preview")
            self.preview_text.clear()
            self.path_label.clear()
            self.select_btn.setEnabled(False)
            self.selected_blueprint = None
            self.selected_path = None
            return
        
        # Only enable for actual blueprint files
        if blueprint_path.suffix != '.md':
            self.preview_label.setText("Select a blueprint file (.md)")
            self.preview_text.clear()
            self.path_label.clear()
            self.select_btn.setEnabled(False)
            self.selected_blueprint = None
            self.selected_path = None
            return
        
        try:
            content = blueprint_path.read_text(encoding='utf-8')
            self.preview_text.setPlainText(content)
            self.preview_label.setText(f"Preview: {blueprint_path.name}")
            
            # Calculate relative path for display
            rel_path = blueprint_path.relative_to(self.official_dir)
            self.path_label.setText(f"Path: blueprints/{rel_path}")
            self.path_label.setStyleSheet("color: #4a2; margin: 5px; font-size: 11px;")
            
            self.select_btn.setEnabled(True)
            self.selected_blueprint = blueprint_path.stem
            self.selected_path = blueprint_path
            
        except Exception as e:
            self.preview_label.setText(f"Error loading blueprint: {e}")
            self.preview_text.clear()
            self.path_label.clear()
            self.select_btn.setEnabled(False)
            self.selected_blueprint = None
            self.selected_path = None
    
    def on_blueprint_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle blueprint double-click - select and accept.
        
        Args:
            item: Double-clicked tree item
            column: Column index
        """
        if self.select_btn.isEnabled():
            self.accept()
    
    def get_selected_blueprint(self) -> tuple[Optional[str], Optional[Path]]:
        """Get the selected blueprint name and path.
        
        Returns:
            Tuple of (blueprint_name, blueprint_path) or (None, None)
        """
        return self.selected_blueprint, self.selected_path