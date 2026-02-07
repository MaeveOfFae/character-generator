"""Review screen widget."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QPlainTextEdit, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from pathlib import Path
from .theme import SyntaxHighlighter


class ReviewWidget(QWidget):
    """Review screen for editing and validating assets."""
    
    def __init__(self, config, main_window, draft_dir, assets):
        super().__init__()
        self.config = config
        self.main_window = main_window
        self.draft_dir = draft_dir
        self.assets = assets
        self.edit_mode = False
        self.text_editors = {}
        self.dirty = False  # Track if changes are unsaved
        self.highlighters = {}  # Store highlighters for each editor
        
        self.setup_ui()
        self.load_assets()
        self.setup_shortcuts()
        self.connect_change_tracking()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        self.create_header(layout)
        
        # Tab widget with text editors
        self.create_tabs(layout)
        
        # Action button bar
        self.create_action_bar(layout)
    
    def create_header(self, layout):
        """Create header with metadata."""
        header_frame = QFrame()
        header_frame.setFrameShape(QFrame.Shape.StyledPanel)
        header_frame.setLineWidth(2)
        header_layout = QHBoxLayout(header_frame)
        
        # Title
        title = QLabel(f"📝 Review: {self.draft_dir.name}")
        title_font = QFont("Arial", 14, QFont.Weight.Bold)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        # Load metadata
        from ..metadata import DraftMetadata
        metadata = DraftMetadata.load(self.draft_dir)
        
        if metadata:
            info_text = f"Seed: {metadata.seed[:50]}... | Mode: {metadata.mode} | Model: {metadata.model}"
        else:
            info_text = "No metadata available"
        
        metadata_label = QLabel(info_text)
        metadata_label.setStyleSheet("color: #888;")
        header_layout.addWidget(metadata_label, 1)
        
        # Quick action buttons
        fav_btn = QPushButton("⭐ Favorite")
        fav_btn.setFixedWidth(110)
        fav_btn.clicked.connect(self.toggle_favorite)
        header_layout.addWidget(fav_btn)
        
        genre_btn = QPushButton("🎭 Genre")
        genre_btn.setFixedWidth(100)
        genre_btn.clicked.connect(self.select_genre)
        header_layout.addWidget(genre_btn)
        
        tags_btn = QPushButton("🏷️ Tags")
        tags_btn.setFixedWidth(100)
        tags_btn.clicked.connect(self.edit_tags)
        header_layout.addWidget(tags_btn)
        
        notes_btn = QPushButton("📝 Notes")
        notes_btn.setFixedWidth(100)
        notes_btn.clicked.connect(self.edit_notes)
        header_layout.addWidget(notes_btn)
        
        layout.addWidget(header_frame)
    
    def create_tabs(self, layout):
        """Create tabbed text editors."""
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        
        tabs_data = [
            ("System Prompt", "system_prompt"),
            ("Post History", "post_history"),
            ("Character Sheet", "character_sheet"),
            ("Intro Scene", "intro_scene"),
            ("Intro Page", "intro_page"),
            ("A1111", "a1111"),
            ("Suno", "suno"),
        ]
        
        for tab_name, asset_key in tabs_data:
            editor = QPlainTextEdit()
            editor.setReadOnly(True)
            editor.setFont(QFont("Courier New", 11))
            editor.setStyleSheet("""
                QPlainTextEdit {
                    background-color: #2a2a2a;
                    border: 1px solid #444;
                }
            """)
            
            self.text_editors[asset_key] = editor
            self.tab_widget.addTab(editor, tab_name)
            
            # Create and attach syntax highlighter
            self.create_highlighter(editor)
        
        layout.addWidget(self.tab_widget, 1)
    
    def create_action_bar(self, layout):
        """Create action button bar."""
        action_frame = QFrame()
        action_frame.setFrameShape(QFrame.Shape.StyledPanel)
        action_layout = QHBoxLayout(action_frame)
        
        # Left side
        self.edit_btn = QPushButton("✏️ Edit Mode [E]")
        self.edit_btn.setFixedWidth(140)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        action_layout.addWidget(self.edit_btn)
        
        self.save_btn = QPushButton("💾 Save [Ctrl+S]")
        self.save_btn.setFixedWidth(140)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet("QPushButton:enabled { background-color: #2d5f2d; }")
        self.save_btn.clicked.connect(self.save_changes)
        action_layout.addWidget(self.save_btn)
        
        validate_btn = QPushButton("✓ Validate")
        validate_btn.setFixedWidth(110)
        validate_btn.clicked.connect(self.validate_pack)
        action_layout.addWidget(validate_btn)
        
        regen_btn = QPushButton("🔄 Regenerate")
        regen_btn.setFixedWidth(130)
        regen_btn.clicked.connect(self.regenerate_asset)
        action_layout.addWidget(regen_btn)
        
        history_btn = QPushButton("📜 History")
        history_btn.setFixedWidth(110)
        history_btn.clicked.connect(self.show_version_history)
        action_layout.addWidget(history_btn)
        
        action_layout.addStretch()
        
        # Center status
        self.status_label = QLabel("✓ Ready")
        self.status_label.setStyleSheet("color: #4a4;")
        action_layout.addWidget(self.status_label)
        
        action_layout.addStretch()
        
        # Right side
        export_btn = QPushButton("📦 Export")
        export_btn.setFixedWidth(110)
        export_btn.clicked.connect(self.export_pack)
        action_layout.addWidget(export_btn)
        
        back_btn = QPushButton("⬅️ Back [Q]")
        back_btn.setFixedWidth(120)
        back_btn.clicked.connect(self.main_window.show_home)
        action_layout.addWidget(back_btn)
        
        layout.addWidget(action_frame)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        QShortcut(QKeySequence("E"), self, self.toggle_edit_mode)
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_changes)
        QShortcut(QKeySequence("Q"), self, self.main_window.show_home)
        QShortcut(QKeySequence("Escape"), self, self.main_window.show_home)
        QShortcut(QKeySequence("Tab"), self, self.next_tab)    
    def connect_change_tracking(self):
        """Connect signals to track unsaved changes."""
        for editor in self.text_editors.values():
            editor.textChanged.connect(self.mark_dirty)
    
    def load_assets(self):
        """Load assets into editors."""
        for asset_key, editor in self.text_editors.items():
            content = self.assets.get(asset_key, "")
            editor.setPlainText(content)
            # Reapply highlighting after loading
            if asset_key in self.highlighters:
                highlighter = self.highlighters[asset_key]
                self.apply_highlighting(editor, highlighter)
    
    def mark_dirty(self):
        """Mark as having unsaved changes."""
        if self.edit_mode:
            self.dirty = True
            self.status_label.setText("⚠️ Unsaved changes")
            self.status_label.setStyleSheet("color: #fa4;")    
    def toggle_edit_mode(self):
        """Toggle edit mode."""
        self.edit_mode = not self.edit_mode
        
        # Get current editor
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, QPlainTextEdit):
            current_widget.setReadOnly(not self.edit_mode)
        
        # Update UI
        if self.edit_mode:
            self.edit_btn.setText("🔒 Read Mode [E]")
            self.save_btn.setEnabled(True)
            self.status_label.setText("⚠️ Edit mode active")
            self.status_label.setStyleSheet("color: #fa4;")
        else:
            self.edit_btn.setText("✏️ Edit Mode [E]")
            self.save_btn.setEnabled(False)
            self.status_label.setText("✓ Ready")
            self.status_label.setStyleSheet("color: #4a4;")
    
    def save_changes(self):
        """Save changes to current asset."""
        if not self.edit_mode:
            return
        
        # Get current tab
        current_index = self.tab_widget.currentIndex()
        asset_keys = list(self.text_editors.keys())
        asset_key = asset_keys[current_index]
        
        # Get content
        editor = self.text_editors[asset_key]
        content = editor.toPlainText()
        
        # Save to file
        from ..pack_io import save_asset
        try:
            save_asset(self.draft_dir, asset_key, content)
            self.assets[asset_key] = content
            self.dirty = False
            self.main_window.status_bar.showMessage(f"✓ Saved {asset_key}", 3000)
            self.status_label.setText("✓ Changes saved")
            self.status_label.setStyleSheet("color: #4a4;")
        except Exception as e:
            self.main_window.status_bar.showMessage(f"✗ Error saving: {e}", 5000)
    
    def create_highlighter(self, editor):
        """Create and store syntax highlighter for editor."""
        # Load theme colors from config
        theme_config = self.config.get("theme", {})
        from .theme import ThemeManager, SyntaxHighlighter, DEFAULT_THEME
        
        # Get theme colors
        theme_colors = {
            "tokenizer": theme_config.get("tokenizer", DEFAULT_THEME["tokenizer"]),
            "app": theme_config.get("app", DEFAULT_THEME["app"])
        }
        
        # Create highlighter instance (stores the colors)
        highlighter = SyntaxHighlighter(theme_colors)
        
        # Store reference to highlighter for each editor
        for asset_key, ed in self.text_editors.items():
            if ed == editor:
                self.highlighters[asset_key] = highlighter
                break
        
        # Apply highlighting to the editor
        self.apply_highlighting(editor, highlighter)
    
    def regenerate_asset(self):
        """Regenerate the current asset using LLM."""
        from .dialogs import RegenerateDialog
        current_index = self.tab_widget.currentIndex()
        asset_keys = list(self.text_editors.keys())
        asset_key = asset_keys[current_index]
        
        dialog = RegenerateDialog(self, self.draft_dir, self.assets, self.config, asset_key)
        if dialog.exec():
            # Reload from dialog result
            if hasattr(dialog, 'regenerated_content'):
                self.text_editors[asset_key].setPlainText(dialog.regenerated_content)
                self.assets[asset_key] = dialog.regenerated_content
                self.dirty = True
                self.main_window.status_bar.showMessage("✓ Asset regenerated", 3000)
    
    def validate_pack(self):
        """Validate the pack."""
        from ..validate import validate_pack
        
        self.main_window.status_bar.showMessage("Running validation...", 0)
        
        try:
            result = validate_pack(self.draft_dir)
            
            if result.get("success"):
                self.main_window.status_bar.showMessage("✓ Validation passed", 5000)
                self.status_label.setText("✓ Validation passed")
                self.status_label.setStyleSheet("color: #4a4;")
            else:
                errors = result.get("errors", "Unknown error")
                self.main_window.status_bar.showMessage(f"✗ Validation failed: {errors}", 10000)
                self.status_label.setText("✗ Validation failed")
                self.status_label.setStyleSheet("color: #f44;")
        except Exception as e:
            self.main_window.status_bar.showMessage(f"✗ Validation error: {e}", 5000)
    
    def export_pack(self):
        """Export the pack."""
        from .dialogs import ExportDialog
        dialog = ExportDialog(self, self.draft_dir, self.assets, self.config)
        dialog.exec()
    
    def toggle_favorite(self):
        """Toggle favorite status."""
        from ..metadata import DraftMetadata
        
        metadata = DraftMetadata.load(self.draft_dir)
        if metadata:
            metadata.favorite = not metadata.favorite
            metadata.save(self.draft_dir)
            status = "favorited" if metadata.favorite else "unfavorited"
            self.main_window.status_bar.showMessage(f"✓ Draft {status}", 3000)
    
    def select_genre(self):
        """Select genre."""
        from .dialogs import GenreDialog
        from ..metadata import DraftMetadata
        
        metadata = DraftMetadata.load(self.draft_dir)
        current_genre = metadata.genre if metadata else None
        
        dialog = GenreDialog(self, self.draft_dir, current_genre)
        if dialog.exec():
            self.main_window.status_bar.showMessage("✓ Genre updated", 3000)
    
    def edit_tags(self):
        """Edit tags."""
        from .dialogs import TagsDialog
        dialog = TagsDialog(self, self.draft_dir)
        if dialog.exec():
            self.main_window.status_bar.showMessage("✓ Tags updated", 3000)
    
    def edit_notes(self):
        """Edit notes."""
        from .dialogs import NotesDialog
        dialog = NotesDialog(self, self.draft_dir)
        if dialog.exec():
            self.main_window.status_bar.showMessage("✓ Notes updated", 3000)
    
    def show_version_history(self):
        """Show version history for current tab."""
        current_tab = self.tab_widget.currentWidget()
        asset_name = None
        
        for name, editor in self.text_editors.items():
            if editor == current_tab:
                asset_name = name
                break
        
        if not asset_name:
            self.main_window.status_bar.showMessage("✗ No asset selected", 3000)
            return
        
        from .dialogs import VersionHistoryDialog
        dialog = VersionHistoryDialog(self, self.draft_dir, asset_name)
        if dialog.exec():
            # Reload asset if it was rolled back
            self.load_assets()
            self.main_window.status_bar.showMessage("✓ Version history updated", 3000)
    
    def next_tab(self):
        """Go to next tab."""
        current = self.tab_widget.currentIndex()
        next_index = (current + 1) % self.tab_widget.count()
        self.tab_widget.setCurrentIndex(next_index)
    
    def refresh_highlighters(self):
        """Refresh all syntax highlighters with updated theme colors."""
        from .theme import ThemeManager, SyntaxHighlighter, DEFAULT_THEME
        
        # Reload theme colors
        theme_config = self.config.get("theme", {})
        theme_colors = {
            "tokenizer": theme_config.get("tokenizer", DEFAULT_THEME["tokenizer"]),
            "app": theme_config.get("app", DEFAULT_THEME["app"])
        }
        
        # Update all highlighters
        for asset_key, highlighter in self.highlighters.items():
            highlighter.theme_colors = theme_colors
            highlighter.formats = highlighter._create_formats()
            
            # Reapply highlighting to the editor
            editor = self.text_editors.get(asset_key)
            if editor:
                self.apply_highlighting(editor, highlighter)
    
    def apply_highlighting(self, editor, highlighter):
        """Apply syntax highlighting to an editor."""
        from PySide6.QtGui import QTextCursor
        
        text = editor.toPlainText()
        
        # Get highlights
        highlights = highlighter.get_highlight_data(text)
        
        # Apply highlights in reverse order (to maintain positions)
        cursor = QTextCursor(editor.document())
        for start, end, fmt in reversed(highlights):
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            cursor.mergeCharFormat(fmt)
