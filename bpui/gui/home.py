"""Home screen widget."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QFrame, QListWidgetItem, QLineEdit, QComboBox,
    QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from pathlib import Path


class HomeWidget(QWidget):
    """Home screen with recent drafts."""
    
    def __init__(self, config, main_window):
        super().__init__()
        self.config = config
        self.main_window = main_window
        self.all_drafts = []  # Store all drafts for filtering
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🌟 Blueprint UI")
        title_font = QFont("Arial", 24, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Character Asset Generator")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        seedgen_btn = QPushButton("🎲 Seed Generator")
        seedgen_btn.setFixedSize(200, 50)
        seedgen_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        seedgen_btn.clicked.connect(lambda: self.main_window.show_seed_generator())
        btn_layout.addWidget(seedgen_btn)
        
        compile_btn = QPushButton("🌱 New Compilation")
        compile_btn.setFixedSize(200, 50)
        compile_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        compile_btn.clicked.connect(lambda: self.main_window.show_compile())
        btn_layout.addWidget(compile_btn)
        
        batch_btn = QPushButton("📦 Batch Compilation")
        batch_btn.setFixedSize(200, 50)
        batch_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        batch_btn.clicked.connect(lambda: self.main_window.show_batch())
        btn_layout.addWidget(batch_btn)
        
        offspring_btn = QPushButton("👶 Offspring Generator")
        offspring_btn.setFixedSize(200, 50)
        offspring_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        offspring_btn.clicked.connect(lambda: self.main_window.show_offspring())
        btn_layout.addWidget(offspring_btn)
        
        validate_btn = QPushButton("✓ Validate Directory")
        validate_btn.setFixedSize(200, 50)
        validate_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        validate_btn.clicked.connect(lambda: self.main_window.show_validate())
        btn_layout.addWidget(validate_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        layout.addSpacing(20)
        
        # Recent drafts section
        drafts_label = QLabel("📁 Drafts")
        drafts_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(drafts_label)
        
        # Search and filter controls
        filter_layout = QHBoxLayout()
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search drafts...")
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_input, 2)
        
        # Genre filter
        self.genre_combo = QComboBox()
        self.genre_combo.addItem("All Genres")
        self.genre_combo.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.genre_combo, 1)
        
        # Tag filter
        self.tag_combo = QComboBox()
        self.tag_combo.addItem("All Tags")
        self.tag_combo.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.tag_combo, 1)
        
        # Sort
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Newest First", "Oldest First", "Name A-Z", "Name Z-A"])
        self.sort_combo.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.sort_combo, 1)
        
        # Favorites only
        self.favorites_check = QCheckBox("⭐ Favorites Only")
        self.favorites_check.stateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.favorites_check)
        
        layout.addLayout(filter_layout)
        
        self.drafts_list = QListWidget()
        self.drafts_list.setStyleSheet("""
            QListWidget {
                background-color: #2a2a2a;
                border: 2px solid #444;
                border-radius: 5px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
            QListWidget::item:selected {
                background-color: #4a6a8a;
            }
        """)
        self.drafts_list.itemDoubleClicked.connect(self.open_draft)
        layout.addWidget(self.drafts_list, 1)
        
        # Bottom button bar
        bottom_layout = QHBoxLayout()
        
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setFixedWidth(120)
        settings_btn.clicked.connect(self.show_settings)
        bottom_layout.addWidget(settings_btn)
        
        templates_btn = QPushButton("🎨 Templates")
        templates_btn.setFixedWidth(120)
        templates_btn.clicked.connect(lambda: self.main_window.show_template_manager())
        bottom_layout.addWidget(templates_btn)
        
        bottom_layout.addStretch()
        
        delete_btn = QPushButton("🗑️ Delete Draft")
        delete_btn.setFixedWidth(130)
        delete_btn.clicked.connect(self.delete_draft)
        bottom_layout.addWidget(delete_btn)
        
        rename_btn = QPushButton("✏️ Rename Draft")
        rename_btn.setFixedWidth(130)
        rename_btn.clicked.connect(self.rename_draft)
        bottom_layout.addWidget(rename_btn)
        
        quit_btn = QPushButton("❌ Quit")
        quit_btn.setFixedWidth(100)
        quit_btn.clicked.connect(self.main_window.close)
        bottom_layout.addWidget(quit_btn)
        
        layout.addLayout(bottom_layout)
    
    def refresh(self):
        """Refresh the drafts list."""
        from ..metadata import DraftMetadata
        from ..draft_index import DraftIndex
        
        drafts_dir = Path("drafts")
        if not drafts_dir.exists():
            self.all_drafts = []
            self.drafts_list.clear()
            return
        
        try:
            # Use index for fast retrieval
            index = DraftIndex()
            
            # Get all drafts from index
            indexed_drafts = index.search(sort_by="created", sort_desc=True)
            
            # Convert to old format for compatibility
            self.all_drafts = []
            for draft_data in indexed_drafts:
                draft_path = Path(draft_data["path"])
                if draft_path.exists():
                    metadata = DraftMetadata(
                        seed=draft_data["seed"],
                        mode=draft_data["mode"],
                        model=draft_data["model"],
                        genre=draft_data["genre"],
                        created=draft_data["created"],
                        modified=draft_data["modified"],
                        tags=draft_data["tags"],
                        notes=draft_data["notes"],
                        favorite=draft_data["favorite"],
                        character_name=draft_data["character_name"]
                    )
                    self.all_drafts.append({
                        'path': draft_path,
                        'metadata': metadata,
                        'mtime': draft_path.stat().st_mtime
                    })
            
            # Update filter dropdowns
            all_genres = set()
            all_tags = set()
            for draft_info in self.all_drafts:
                metadata = draft_info['metadata']
                if metadata:
                    if metadata.genre:
                        all_genres.add(metadata.genre)
                    if metadata.tags:
                        all_tags.update(metadata.tags)
            
            current_genre = self.genre_combo.currentText()
            current_tag = self.tag_combo.currentText()
            
            self.genre_combo.clear()
            self.genre_combo.addItem("All Genres")
            self.genre_combo.addItems(sorted(all_genres))
            if current_genre in all_genres or current_genre == "All Genres":
                self.genre_combo.setCurrentText(current_genre)
            
            self.tag_combo.clear()
            self.tag_combo.addItem("All Tags")
            self.tag_combo.addItems(sorted(all_tags))
            if current_tag in all_tags or current_tag == "All Tags":
                self.tag_combo.setCurrentText(current_tag)
        
        except Exception:
            # Fallback to filesystem scan if index fails
            self.all_drafts = []
            drafts = [d for d in drafts_dir.iterdir() if d.is_dir()]
            
            for draft in drafts:
                metadata = DraftMetadata.load(draft)
                self.all_drafts.append({
                    'path': draft,
                    'metadata': metadata,
                    'mtime': draft.stat().st_mtime
                })
        
        # Apply filters to display
        self.apply_filters()
    
    def apply_filters(self):
        """Apply search and filters to drafts list."""
        self.drafts_list.clear()
        
        if not self.all_drafts:
            item = QListWidgetItem("No drafts yet. Create one with 'New Compilation'")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.drafts_list.addItem(item)
            return
        
        # Get filter values
        search_text = self.search_input.text().lower()
        selected_genre = self.genre_combo.currentText()
        selected_tag = self.tag_combo.currentText()
        favorites_only = self.favorites_check.isChecked()
        sort_mode = self.sort_combo.currentText()
        
        # Filter drafts
        filtered = []
        for draft_info in self.all_drafts:
            draft_path = draft_info['path']
            metadata = draft_info['metadata']
            
            # Search filter
            if search_text:
                draft_name = draft_path.name.lower()
                seed = metadata.seed.lower() if metadata else ""
                if search_text not in draft_name and search_text not in seed:
                    continue
            
            # Genre filter
            if selected_genre != "All Genres":
                if not metadata or metadata.genre != selected_genre:
                    continue
            
            # Tag filter
            if selected_tag != "All Tags":
                if not metadata or selected_tag not in (metadata.tags or []):
                    continue
            
            # Favorites filter
            if favorites_only:
                if not metadata or not metadata.favorite:
                    continue
            
            filtered.append(draft_info)
        
        # Sort
        if sort_mode == "Newest First":
            filtered.sort(key=lambda d: d['mtime'], reverse=True)
        elif sort_mode == "Oldest First":
            filtered.sort(key=lambda d: d['mtime'])
        elif sort_mode == "Name A-Z":
            filtered.sort(key=lambda d: d['path'].name)
        elif sort_mode == "Name Z-A":
            filtered.sort(key=lambda d: d['path'].name, reverse=True)
        
        # Display filtered results
        for draft_info in filtered[:100]:  # Limit to 100 for performance
            draft_path = draft_info['path']
            metadata = draft_info['metadata']
            
            # Build display name
            display_name = f"📝 {draft_path.name}"
            if metadata:
                if metadata.favorite:
                    display_name = f"⭐ {draft_path.name}"
                if metadata.genre:
                    display_name += f" [{metadata.genre}]"
            
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, draft_path)
            self.drafts_list.addItem(item)
        
        if not filtered:
            item = QListWidgetItem("No drafts match your filters")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.drafts_list.addItem(item)
    
    def open_draft(self, item):
        """Open selected draft in review screen."""
        draft_dir = item.data(Qt.ItemDataRole.UserRole)
        if not draft_dir:
            return
        
        # Load assets
        from ..pack_io import load_draft
        try:
            assets = load_draft(draft_dir)
            self.main_window.show_review(draft_dir, assets)
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Load Error", f"Failed to load draft: {e}")
    
    def delete_draft(self):
        """Delete selected draft."""
        from PySide6.QtWidgets import QMessageBox
        import shutil
        
        current = self.drafts_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", "Please select a draft to delete")
            return
        
        draft_dir = current.data(Qt.ItemDataRole.UserRole)
        if not draft_dir:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete draft '{draft_dir.name}'?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            shutil.rmtree(draft_dir)
            self.refresh()
            self.main_window.status_bar.showMessage(f"✓ Deleted {draft_dir.name}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Delete Error", f"Failed to delete draft: {e}")
    
    def rename_draft(self):
        """Rename selected draft."""
        from PySide6.QtWidgets import QMessageBox, QInputDialog
        
        current = self.drafts_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", "Please select a draft to rename")
            return
        
        draft_dir = current.data(Qt.ItemDataRole.UserRole)
        if not draft_dir:
            return
        
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Draft",
            f"Enter new name for '{draft_dir.name}':",
            text=draft_dir.name
        )
        
        if not ok or not new_name:
            return
        
        # Sanitize new name
        import re
        new_name = re.sub(r'[^\w\s\-]', '_', new_name)
        new_name = re.sub(r'[\s]+', '_', new_name)
        
        new_dir = draft_dir.parent / new_name
        
        if new_dir.exists():
            QMessageBox.warning(self, "Name Conflict", f"A draft named '{new_name}' already exists")
            return
        
        try:
            draft_dir.rename(new_dir)
            self.refresh()
            self.main_window.status_bar.showMessage(f"✓ Renamed to {new_name}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Rename Error", f"Failed to rename draft: {e}")
            self.main_window.status_bar.showMessage(f"Error loading draft: {e}", 5000)
    
    def show_settings(self):
        """Show settings dialog."""
        from .dialogs import SettingsDialog
        dialog = SettingsDialog(self, self.config)
        if dialog.exec():
            self.config.save()
            self.main_window.status_bar.showMessage("✓ Settings saved", 3000)
