"""Offspring generator widget for GUI."""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QMessageBox, QDialog, QListWidget,
    QListWidgetItem, QDialogButtonBox, QLineEdit
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from pathlib import Path
import asyncio


class OffspringWidget(QWidget):
    """Offspring generator widget."""
    
    def __init__(self, config, main_window):
        super().__init__()
        self.config = config
        self.main_window = main_window
        self.parent1_path = None
        self.parent2_path = None
        self.parent1_assets = {}
        self.parent2_assets = {}
        self.parent1_name = ""
        self.parent2_name = ""
        self.generation_thread: Optional['OffspringThread'] = None
        self.templates = []
        
        self.setup_ui()
    
    def load_templates(self):
        """Load available templates into combo box."""
        from ..templates import TemplateManager
        
        self.template_combo.clear()
        
        try:
            manager = TemplateManager()
            self.templates = manager.list_templates()
            
            for template in self.templates:
                label = f"{template.name} ({len(template.assets)} assets)"
                if template.is_official:
                    label += " ★"
                self.template_combo.addItem(label, template.name)
            
            # Select official template by default
            for i, template in enumerate(self.templates):
                if template.is_official:
                    self.template_combo.setCurrentIndex(i)
                    break
        
        except Exception as e:
            self.template_combo.addItem(f"Error loading templates: {e}", None)
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("👶 Offspring Generator")
        title_font = QFont("Arial", 22, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(10)
        
        # Parent selection section
        parent_layout = QHBoxLayout()
        
        # Parent 1
        parent1_layout = QVBoxLayout()
        parent1_label = QLabel("👤 Parent 1")
        parent1_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        parent1_layout.addWidget(parent1_label)
        
        self.parent1_info = QLabel("[Press 'Select Parent 1' below]")
        self.parent1_info.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                border: 2px solid #444;
                border-radius: 5px;
                padding: 15px;
                min-height: 100px;
            }
        """)
        self.parent1_info.setWordWrap(True)
        parent1_layout.addWidget(self.parent1_info)
        
        self.parent1_btn = QPushButton("Select Parent 1")
        self.parent1_btn.setFixedHeight(40)
        self.parent1_btn.clicked.connect(self.select_parent1)
        parent1_layout.addWidget(self.parent1_btn)
        
        parent_layout.addLayout(parent1_layout, 1)
        
        # Parent 2
        parent2_layout = QVBoxLayout()
        parent2_label = QLabel("👤 Parent 2")
        parent2_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        parent2_layout.addWidget(parent2_label)
        
        self.parent2_info = QLabel("[Press 'Select Parent 2' below]")
        self.parent2_info.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                border: 2px solid #444;
                border-radius: 5px;
                padding: 15px;
                min-height: 100px;
            }
        """)
        self.parent2_info.setWordWrap(True)
        parent2_layout.addWidget(self.parent2_info)
        
        self.parent2_btn = QPushButton("Select Parent 2")
        self.parent2_btn.setFixedHeight(40)
        self.parent2_btn.clicked.connect(self.select_parent2)
        parent2_layout.addWidget(self.parent2_btn)
        
        parent_layout.addLayout(parent2_layout, 1)
        
        layout.addLayout(parent_layout)
        
        layout.addSpacing(10)
        
        # Content mode selection
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Content Mode:")
        mode_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        mode_layout.addWidget(mode_label)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Auto (inherit from parents)", "SFW", "NSFW", "Platform-Safe"])
        self.mode_combo.setFixedWidth(250)
        mode_layout.addWidget(self.mode_combo)
        
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        # Template selector
        template_layout = QHBoxLayout()
        template_label = QLabel("Template:")
        template_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        template_layout.addWidget(template_label)
        self.template_combo = QComboBox()
        self.template_combo.setFixedWidth(250)
        self.load_templates()
        template_layout.addWidget(self.template_combo)
        template_layout.addStretch()
        layout.addLayout(template_layout)
        
        layout.addSpacing(10)
        
        # Generate button
        self.generate_btn = QPushButton("▶️ Generate Offspring")
        self.generate_btn.setFixedHeight(50)
        self.generate_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.generate_btn.setEnabled(False)
        self.generate_btn.clicked.connect(self.start_generation)
        layout.addWidget(self.generate_btn)
        
        # Back button
        back_layout = QHBoxLayout()
        back_layout.addStretch()
        
        self.back_btn = QPushButton("⬅️ Back to Home")
        self.back_btn.setFixedWidth(150)
        self.back_btn.clicked.connect(self.main_window.show_home)
        back_layout.addWidget(self.back_btn)
        
        layout.addLayout(back_layout)
        
        # Output log
        output_label = QLabel("Output:")
        output_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(output_label)
        
        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        self.output_log.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                border: 2px solid #444;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.output_log, 1)
    
    def set_parent(self, parent_num, draft_path, assets):
        """Set parent character after selection."""
        from ..metadata import DraftMetadata
        
        metadata = DraftMetadata.load(draft_path)
        char_name = metadata.character_name if metadata else draft_path.name
        
        if parent_num == 1:
            self.parent1_path = draft_path
            self.parent1_assets = assets
            self.parent1_name = char_name
            
            # Update display
            self.parent1_info.setText(f"✓ Selected:\n\n{char_name}\n{draft_path.name}")
            self.parent1_info.setStyleSheet("""
                QLabel {
                    background-color: #1a3a1a;
                    border: 2px solid #4a8a4a;
                    border-radius: 5px;
                    padding: 15px;
                    min-height: 100px;
                }
            """)
        else:
            self.parent2_path = draft_path
            self.parent2_assets = assets
            self.parent2_name = char_name
            
            # Update display
            self.parent2_info.setText(f"✓ Selected:\n\n{char_name}\n{draft_path.name}")
            self.parent2_info.setStyleSheet("""
                QLabel {
                    background-color: #1a3a1a;
                    border: 2px solid #4a8a4a;
                    border-radius: 5px;
                    padding: 15px;
                    min-height: 100px;
                }
            """)
        
        # Enable generate button if both parents selected
        self.generate_btn.setEnabled(bool(self.parent1_path and self.parent2_path))
    
    def select_parent1(self):
        """Show parent 1 selection dialog."""
        dialog = ParentSelectDialog(1, self)
        if dialog.exec():
            parent_path, assets = dialog.get_selection()
            if parent_path and assets:
                self.set_parent(1, parent_path, assets)
    
    def select_parent2(self):
        """Show parent 2 selection dialog."""
        dialog = ParentSelectDialog(2, self)
        if dialog.exec():
            parent_path, assets = dialog.get_selection()
            if parent_path and assets:
                self.set_parent(2, parent_path, assets)
    
    def log(self, message):
        """Append message to output log."""
        self.output_log.append(message)
        self.output_log.verticalScrollBar().setValue(
            self.output_log.verticalScrollBar().maximum()
        )
        self.main_window.status_bar.showMessage(message[:50], 3000)
    
    def start_generation(self):
        """Start offspring generation in background thread."""
        if not self.parent1_path or not self.parent2_path:
            QMessageBox.warning(self, "Missing Parents", "Please select both parent characters")
            return
        
        # Get content mode
        mode_value = self.mode_combo.currentText()
        mode = None if mode_value == "Auto (inherit from parents)" else mode_value
        
        # Get template
        template_name = self.template_combo.currentData()
        if not template_name:
            QMessageBox.warning(self, "No Template", "Please select a template.")
            return
        template = next((t for t in self.templates if t.name == template_name), None)
        if not template:
            QMessageBox.warning(self, "Template Not Found", "Could not find the selected template.")
            return

        # Clear output log
        self.output_log.clear()
        self.generate_btn.setEnabled(False)
        self.parent1_btn.setEnabled(False)
        self.parent2_btn.setEnabled(False)
        
        # Start generation thread
        self.generation_thread = OffspringThread(
            self.parent1_path,
            self.parent2_path,
            self.parent1_assets,
            self.parent2_assets,
            self.parent1_name,
            self.parent2_name,
            mode,
            self.config,
            template
        )
        self.generation_thread.log_signal.connect(self.log)
        self.generation_thread.finished_signal.connect(self.generation_finished)
        self.generation_thread.error_signal.connect(self.generation_error)
        self.generation_thread.start()
    
    def generation_finished(self, draft_dir, assets):
        """Handle successful generation."""
        from .review import ReviewWidget
        
        # Navigate to review screen
        self.main_window.show_review(draft_dir, assets)
        
        # Re-enable buttons
        self.generate_btn.setEnabled(True)
        self.parent1_btn.setEnabled(True)
        self.parent2_btn.setEnabled(True)
    
    def generation_error(self, error_message):
        """Handle generation error."""
        QMessageBox.critical(self, "Generation Error", error_message)
        
        # Re-enable buttons
        self.generate_btn.setEnabled(True)
        self.parent1_btn.setEnabled(True)
        self.parent2_btn.setEnabled(True)


class ParentSelectDialog(QDialog):
    """Dialog for selecting a parent draft."""
    
    def __init__(self, parent_num, parent_widget):
        super().__init__(parent_widget)
        self.parent_num = parent_num
        self.parent_widget = parent_widget
        self.drafts = []
        self.selected_path = None
        self.selected_assets = None
        
        self.setWindowTitle(f"Select Parent {parent_num}")
        self.setGeometry(200, 200, 600, 500)
        
        self.setup_ui()
        self.load_drafts()
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        title = QLabel(f"👤 Select Parent {self.parent_num}")
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search drafts...")
        self.search_input.textChanged.connect(self.apply_filter)
        layout.addWidget(self.search_input)
        
        # Drafts list
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
        self.drafts_list.itemDoubleClicked.connect(self.accept_selection)
        layout.addWidget(self.drafts_list)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_selection)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_drafts(self):
        """Load all drafts."""
        from ..metadata import search_metadata
        from pathlib import Path
        
        drafts_dir = Path.cwd() / "drafts"
        self.drafts = search_metadata(drafts_dir)
        self.apply_filter("")
    
    def apply_filter(self, query):
        """Apply search filter."""
        from ..metadata import search_metadata
        from pathlib import Path
        
        drafts_dir = Path.cwd() / "drafts"
        filtered = search_metadata(drafts_dir, query=query)
        self.drafts = filtered
        
        self.drafts_list.clear()
        
        for draft_path, metadata in filtered:
            char_name = metadata.character_name or draft_path.name
            mode_text = metadata.mode or "Auto"
            display = f"{char_name} ({mode_text})"
            
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, (draft_path, metadata))
            self.drafts_list.addItem(item)
    
    def accept_selection(self):
        """Accept selected draft."""
        current = self.drafts_list.currentItem()
        if not current:
            return
        
        draft_path, metadata = current.data(Qt.ItemDataRole.UserRole)
        
        try:
            from ..pack_io import load_draft
            assets = load_draft(draft_path)
            self.selected_path = draft_path
            self.selected_assets = assets
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load draft: {e}")
    
    def get_selection(self):
        """Get selected draft."""
        return self.selected_path, self.selected_assets


class OffspringThread(QThread):
    """Background thread for offspring generation."""
    
    log_signal = Signal(str)
    finished_signal = Signal(object, object)
    error_signal = Signal(str)
    
    def __init__(self, parent1_path, parent2_path, parent1_assets, parent2_assets,
                 parent1_name, parent2_name, mode, config, template):
        super().__init__()
        self.parent1_path = parent1_path
        self.parent2_path = parent2_path
        self.parent1_assets = parent1_assets
        self.parent2_assets = parent2_assets
        self.parent1_name = parent1_name
        self.parent2_name = parent2_name
        self.mode = mode
        self.config = config
        self.template = template
    
    def run(self):
        """Run offspring generation."""
        # Run async code in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(self._run_async())
        finally:
            loop.close()
    
    async def _run_async(self):
        """Async implementation of offspring generation."""
        try:
            from ..llm.factory import create_engine
            from ..prompting import build_offspring_prompt, build_asset_prompt
            from ..parse_blocks import extract_single_asset, extract_character_name
            from ..pack_io import create_draft_dir
            from ..metadata import DraftMetadata
            from ..topological_sort import topological_sort

            self.log_signal.emit("Initializing offspring generation...")

            # Check API key
            if not self.config.api_key:
                raise Exception("No API key configured. Configure in Settings.")

            self.log_signal.emit(f"Parents: {self.parent1_name} + {self.parent2_name}")
            self.log_signal.emit(f"Mode: {self.mode or 'Auto'}")
            self.log_signal.emit(f"Model: {self.config.model}")

            # Create engine using factory
            try:
                engine = create_engine(
                    self.config,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
            except (ImportError, ValueError, RuntimeError) as e:
                raise Exception(f"Failed to create engine: {e}")

            # Step 1: Generate offspring seed
            self.log_signal.emit("\nStep 1: Generating offspring seed...")
            
            system_prompt, user_prompt = build_offspring_prompt(
                parent1_assets=self.parent1_assets,
                parent2_assets=self.parent2_assets,
                parent1_name=self.parent1_name,
                parent2_name=self.parent2_name,
                mode=self.mode
            )
            
            output_text = await engine.generate(system_prompt, user_prompt)
            offspring_seed = output_text.strip()
            
            if not offspring_seed:
                raise Exception("No seed generated")
            
            self.log_signal.emit(f"✓ Offspring seed generated ({len(offspring_seed)} chars)")
            self.log_signal.emit(f"  Preview: {offspring_seed[:100]}...")
            
            # Step 2: Generate full character suite
            self.log_signal.emit("\nStep 2: Generating full character suite...")

            if not self.template:
                raise Exception("No template provided for offspring generation.")
            
            try:
                asset_order = topological_sort(self.template.assets)
            except ValueError as e:
                raise Exception(f"Template error: {e}")
            
            assets = {}
            character_name = None
            
            for asset_name in asset_order:
                self.log_signal.emit(f"\n→ Generating {asset_name}...")
                
                system_prompt, user_prompt = build_asset_prompt(
                    asset_name, offspring_seed, self.mode, assets
                )
                
                output = await engine.generate(system_prompt, user_prompt)
                asset_content = extract_single_asset(output, asset_name)
                assets[asset_name] = asset_content
                
                self.log_signal.emit(f"✓ {asset_name} complete ({len(asset_content)} chars)")
                
                if asset_name == "character_sheet" and not character_name:
                    character_name = extract_character_name(asset_content)
                    if character_name:
                        self.log_signal.emit(f"Character: {character_name}")
            
            if not character_name:
                character_name = "offspring_character"
            
            self.log_signal.emit("\n✓ All assets generated!")
            self.log_signal.emit(f"✓ Generated {len(assets)} assets")
            
            # Save draft with lineage metadata
            self.log_signal.emit("\nSaving draft...")
            
            drafts_root = Path.cwd() / "drafts"
            drafts_root_abs = drafts_root.resolve()
            parent1_rel = str(self.parent1_path.relative_to(drafts_root_abs))
            parent2_rel = str(self.parent2_path.relative_to(drafts_root_abs))
            
            draft_dir = create_draft_dir(
                assets,
                character_name,
                seed=offspring_seed,
                mode=self.mode,
                model=self.config.model
            )
            
            # Update metadata with lineage
            metadata = DraftMetadata.load(draft_dir)
            if metadata:
                metadata.parent_drafts = [parent1_rel, parent2_rel]
                metadata.offspring_type = "generated"
                metadata.save(draft_dir)
            
            self.log_signal.emit(f"✓ Saved to: {draft_dir}")
            self.log_signal.emit(f"✓ Lineage: {parent1_rel} + {parent2_rel}")
            
            self.finished_signal.emit(draft_dir, assets)
            
        except Exception as e:
            self.log_signal.emit(f"\n✗ Error: {e}")
            self.error_signal.emit(str(e))
