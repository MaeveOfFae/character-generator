"""Dialogs for Qt6 GUI."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QListWidget, QListWidgetItem,
    QCheckBox, QFormLayout, QPlainTextEdit, QSplitter, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from pathlib import Path
import asyncio


class TagsDialog(QDialog):
    """Dialog for editing tags."""
    
    def __init__(self, parent, draft_dir):
        super().__init__(parent)
        self.draft_dir = draft_dir
        
        self.setWindowTitle("Edit Tags")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Info
        info = QLabel("Add tags to organize your drafts:")
        layout.addWidget(info)
        
        # Tag input
        input_layout = QHBoxLayout()
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Enter tag...")
        self.tag_input.returnPressed.connect(self.add_tag)
        input_layout.addWidget(self.tag_input)
        
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_tag)
        input_layout.addWidget(add_btn)
        layout.addLayout(input_layout)
        
        # Tags list
        self.tags_list = QListWidget()
        layout.addWidget(self.tags_list)
        
        # Remove button
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_tag)
        layout.addWidget(remove_btn)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_tags)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        # Load existing tags
        self.load_tags()
    
    def load_tags(self):
        """Load existing tags."""
        from ..metadata import DraftMetadata
        metadata = DraftMetadata.load(self.draft_dir)
        if metadata and metadata.tags:
            for tag in metadata.tags:
                self.tags_list.addItem(tag)
    
    def add_tag(self):
        """Add a tag."""
        tag = self.tag_input.text().strip()
        if tag:
            self.tags_list.addItem(tag)
            self.tag_input.clear()
    
    def remove_tag(self):
        """Remove selected tag."""
        current = self.tags_list.currentRow()
        if current >= 0:
            self.tags_list.takeItem(current)
    
    def save_tags(self):
        """Save tags to metadata."""
        from ..metadata import DraftMetadata
        
        tags = []
        for i in range(self.tags_list.count()):
            tags.append(self.tags_list.item(i).text())
        
        metadata = DraftMetadata.load(self.draft_dir)
        if not metadata:
            metadata = DraftMetadata(
                seed="",
                mode=None,
                model="",
                tags=tags
            )
        else:
            metadata.tags = tags
        
        metadata.save(self.draft_dir)
        self.accept()


class NotesDialog(QDialog):
    """Dialog for editing notes."""
    
    def __init__(self, parent, draft_dir):
        super().__init__(parent)
        self.draft_dir = draft_dir
        
        self.setWindowTitle("Edit Notes")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Info
        info = QLabel("Add notes about this draft:")
        layout.addWidget(info)
        
        # Notes text area
        self.notes_edit = QTextEdit()
        layout.addWidget(self.notes_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_notes)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        # Load existing notes
        self.load_notes()
    
    def load_notes(self):
        """Load existing notes."""
        from ..metadata import DraftMetadata
        metadata = DraftMetadata.load(self.draft_dir)
        if metadata and metadata.notes:
            self.notes_edit.setPlainText(metadata.notes)
    
    def save_notes(self):
        """Save notes to metadata."""
        from ..metadata import DraftMetadata
        
        notes = self.notes_edit.toPlainText().strip()
        
        metadata = DraftMetadata.load(self.draft_dir)
        if not metadata:
            metadata = DraftMetadata(
                seed="",
                mode=None,
                model="",
                notes=notes
            )
        else:
            metadata.notes = notes
        
        metadata.save(self.draft_dir)
        self.accept()


class ExportDialog(QDialog):
    """Dialog for exporting with preset selection."""
    
    def __init__(self, parent, draft_dir, assets, config):
        super().__init__(parent)
        self.draft_dir = draft_dir
        self.assets = assets
        self.config = config
        
        self.setWindowTitle("Export Character")
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        
        # Character name
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        # Extract name from character sheet
        char_sheet = assets.get("character_sheet", "")
        for line in char_sheet.split("\n")[:5]:
            if line.lower().startswith("name:"):
                name = line.split(":", 1)[1].strip()
                self.name_input.setText(name)
                break
        form.addRow("Character Name:", self.name_input)
        
        # Preset selector
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "raw (no formatting)",
            "chubai (Character Hub AI)",
            "risuai (RisuAI)",
            "tavernai (TavernAI)"
        ])
        form.addRow("Export Preset:", self.preset_combo)
        
        layout.addLayout(form)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        export_btn = QPushButton("📦 Export")
        export_btn.setStyleSheet("background-color: #4a2d5f; padding: 8px 16px;")
        export_btn.clicked.connect(self.do_export)
        btn_layout.addWidget(export_btn)
        
        layout.addLayout(btn_layout)
    
    def do_export(self):
        """Perform the export."""
        from ..export import export_with_preset
        
        character_name = self.name_input.text().strip()
        if not character_name:
            self.status_label.setText("❌ Please enter a character name")
            self.status_label.setStyleSheet("color: #f44;")
            return
        
        # Get preset name
        preset_text = self.preset_combo.currentText()
        preset_name = preset_text.split(" ")[0]  # Extract "raw", "chubai", etc.
        
        self.status_label.setText("⏳ Exporting...")
        self.status_label.setStyleSheet("color: #888;")
        
        try:
            # Use the export_with_preset function which handles everything
            result = export_with_preset(
                character_name=character_name,
                source_dir=self.draft_dir,
                preset_name=preset_name,
                model=self.config.model
            )
            
            if result["success"]:
                output_dir = result.get("output_dir", "unknown")
                self.status_label.setText(f"✓ Exported to: {output_dir}")
                self.status_label.setStyleSheet("color: #4a4;")
                
                # Auto-close after 2 seconds
                from PySide6.QtCore import QTimer
                QTimer.singleShot(2000, self.accept)
            else:
                error_msg = result.get("errors", "Unknown error")
                self.status_label.setText(f"❌ Export failed: {error_msg}")
                self.status_label.setStyleSheet("color: #f44;")
            
        except Exception as e:
            self.status_label.setText(f"❌ Export failed: {e}")
            self.status_label.setStyleSheet("color: #f44;")


class SettingsDialog(QDialog):
    """Dialog for application settings."""
    
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Form
        form = QFormLayout()
        
        # Model
        self.model_input = QLineEdit(config.model)
        self.model_input.setPlaceholderText("e.g., openai/gpt-4")
        form.addRow("Model:", self.model_input)
        
        # API Key (masked)
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Enter API key...")
        
        # Try to get existing key
        provider = config.model.split("/")[0] if "/" in config.model else "openai"
        existing_key = config.get_api_key(provider)
        if existing_key:
            self.api_key_input.setText(existing_key)
        
        form.addRow("API Key:", self.api_key_input)
        
        # Batch settings
        batch_label = QLabel("<b>Batch Processing</b>")
        form.addRow(batch_label)
        
        self.max_concurrent_input = QLineEdit(str(config.batch_max_concurrent))
        form.addRow("Max Concurrent:", self.max_concurrent_input)
        
        self.rate_limit_input = QLineEdit(str(config.batch_rate_limit_delay))
        form.addRow("Rate Limit Delay (s):", self.rate_limit_input)
        
        layout.addLayout(form)
        
        # Test connection button
        test_layout = QHBoxLayout()
        test_btn = QPushButton("🔌 Test Connection")
        test_btn.clicked.connect(self.test_connection)
        test_layout.addWidget(test_btn)
        
        self.test_status = QLabel("")
        self.test_status.setStyleSheet("color: #888;")
        test_layout.addWidget(self.test_status, 1)
        
        layout.addLayout(test_layout)
        
        # Rebuild index button
        rebuild_layout = QHBoxLayout()
        rebuild_btn = QPushButton("🔄 Rebuild Draft Index")
        rebuild_btn.setToolTip("Rebuild SQLite index for fast draft search (useful after manual changes)")
        rebuild_btn.clicked.connect(self.rebuild_index)
        rebuild_layout.addWidget(rebuild_btn)
        
        self.rebuild_status = QLabel("")
        self.rebuild_status.setStyleSheet("color: #888;")
        rebuild_layout.addWidget(self.rebuild_status, 1)
        
        layout.addLayout(rebuild_layout)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def test_connection(self):
        """Test LLM connection."""
        import time
        from ..llm.litellm_engine import LiteLLMEngine
        
        self.test_status.setText("⏳ Testing connection...")
        self.test_status.setStyleSheet("color: #888;")
        
        # Get current values
        model = self.model_input.text().strip()
        api_key = self.api_key_input.text().strip()
        
        if not model:
            self.test_status.setText("❌ Please enter a model")
            self.test_status.setStyleSheet("color: #f44;")
            return
        
        try:
            # Create engine with current settings
            engine = LiteLLMEngine(
                model=model,
                api_key=api_key if api_key else self.config.get_api_key_for_model(model),
                base_url=self.config.api_base_url,
                api_version=self.config.api_version
            )
            
            # Test with simple prompt
            start_time = time.time()
            
            # Run async test in sync context
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(engine.test_connection())
            loop.close()
            
            latency = int((time.time() - start_time) * 1000)
            
            if result.get("success"):
                self.test_status.setText(f"✓ Connected! Latency: {latency}ms")
                self.test_status.setStyleSheet("color: #4a4;")
            else:
                error = result.get("error", "Unknown error")
                self.test_status.setText(f"❌ Connection failed: {error}")
                self.test_status.setStyleSheet("color: #f44;")
        
        except Exception as e:
            self.test_status.setText(f"❌ Error: {e}")
            self.test_status.setStyleSheet("color: #f44;")
    
    def rebuild_index(self):
        """Rebuild the draft index."""
        from ..draft_index import DraftIndex
        
        self.rebuild_status.setText("⏳ Rebuilding index...")
        self.rebuild_status.setStyleSheet("color: #888;")
        
        try:
            index = DraftIndex()
            result = index.rebuild_index()
            
            if result:
                msg = f"✓ Indexed {result['indexed']} drafts"
                if result['skipped'] > 0:
                    msg += f" ({result['skipped']} skipped)"
                self.rebuild_status.setText(msg)
                self.rebuild_status.setStyleSheet("color: #4a4;")
            else:
                self.rebuild_status.setText("✓ Index rebuilt")
                self.rebuild_status.setStyleSheet("color: #4a4;")
        
        except Exception as e:
            self.rebuild_status.setText(f"❌ Error: {e}")
            self.rebuild_status.setStyleSheet("color: #f44;")
    
    def save_settings(self):
        """Save settings."""
        # Update model
        self.config.set("model", self.model_input.text().strip())
        
        # Update API key
        api_key = self.api_key_input.text().strip()
        if api_key:
            provider = self.config.model.split("/")[0] if "/" in self.config.model else "openai"
            self.config.set_api_key(provider, api_key)
        
        # Update batch settings
        try:
            self.config._data["batch"]["max_concurrent"] = int(self.max_concurrent_input.text())
            self.config._data["batch"]["rate_limit_delay"] = float(self.rate_limit_input.text())
        except ValueError:
            pass  # Keep existing values if invalid
        
        self.accept()


class RegenerateWorker(QThread):
    """Worker thread for asset regeneration."""
    
    output = Signal(str)
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, config, asset_key, assets, instructions=""):
        super().__init__()
        self.config = config
        self.asset_key = asset_key
        self.assets = assets
        self.instructions = instructions
    
    def run(self):
        """Run regeneration."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._regenerate())
            loop.close()
            
            if result:
                self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
    
    async def _regenerate(self):
        """Perform regeneration."""
        from ..llm.litellm_engine import LiteLLMEngine
        from ..prompting import load_blueprint
        
        # Build regeneration prompt
        blueprint = load_blueprint(self.asset_key)
        
        context = f"Current {self.asset_key}:\n{self.assets.get(self.asset_key, '')}\n\n"
        prompt = f"{context}Using this blueprint:\n\n{blueprint}\n\n"
        
        if self.instructions:
            prompt += f"User instructions: {self.instructions}\n\n"
        
        prompt += f"Regenerate only the {self.asset_key} asset. Output only the asset content, no explanations."
        
        self.output.emit(f"Regenerating {self.asset_key}...\n\n")
        
        # Create engine
        engine = LiteLLMEngine(
            model=self.config.model,
            api_key=self.config.get_api_key_for_model(self.config.model),
            base_url=self.config.api_base_url,
            api_version=self.config.api_version
        )
        
        # Generate
        response = ""
        async for chunk in engine.generate_chat_stream([{"role": "user", "content": prompt}]):
            response += chunk
            self.output.emit(chunk)
        
        return response.strip()


class RegenerateDialog(QDialog):
    """Dialog for regenerating an asset."""
    
    def __init__(self, parent, draft_dir, assets, config, asset_key):
        super().__init__(parent)
        self.draft_dir = draft_dir
        self.assets = assets
        self.config = config
        self.asset_key = asset_key
        self.worker = None
        self.regenerated_content = ""
        
        self.setWindowTitle(f"Regenerate {asset_key}")
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(self)
        
        # Info
        info = QLabel(f"Regenerate the <b>{asset_key}</b> asset using the LLM:")
        layout.addWidget(info)
        
        # Instructions
        inst_label = QLabel("Optional instructions (leave empty for simple regeneration):")
        layout.addWidget(inst_label)
        
        self.instructions_input = QLineEdit()
        self.instructions_input.setPlaceholderText("e.g., Make it more concise, Add more detail about...")
        layout.addWidget(self.instructions_input)
        
        # Output area
        output_label = QLabel("Output:")
        layout.addWidget(output_label)
        
        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1a1a1a;
                border: 2px solid #444;
                font-family: 'Courier New';
            }
        """)
        layout.addWidget(self.output_text, 1)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.regen_btn = QPushButton("🔄 Regenerate")
        self.regen_btn.clicked.connect(self.start_regeneration)
        btn_layout.addWidget(self.regen_btn)
        
        self.cancel_btn = QPushButton("⏹️ Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_regeneration)
        btn_layout.addWidget(self.cancel_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)
        
        use_btn = QPushButton("✓ Use This")
        use_btn.setStyleSheet("background-color: #2d5f2d;")
        use_btn.clicked.connect(self.accept)
        btn_layout.addWidget(use_btn)
        
        layout.addLayout(btn_layout)
    
    def start_regeneration(self):
        """Start regeneration."""
        instructions = self.instructions_input.text().strip()
        
        self.output_text.clear()
        self.regen_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        
        self.worker = RegenerateWorker(
            self.config,
            self.asset_key,
            self.assets,
            instructions
        )
        self.worker.output.connect(self.append_output)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def append_output(self, text):
        """Append text to output."""
        self.output_text.insertPlainText(text)
        self.output_text.ensureCursorVisible()
    
    def on_finished(self, content):
        """Handle regeneration finished."""
        self.regenerated_content = content
        self.regen_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.append_output("\n\n✓ Regeneration complete")
    
    def on_error(self, error):
        """Handle regeneration error."""
        self.append_output(f"\n\n✗ Error: {error}\n")
        self.regen_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
    
    def cancel_regeneration(self):
        """Cancel regeneration."""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self.append_output("\n\n⏹️ Regeneration cancelled\n")
            self.regen_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)


class VersionHistoryDialog(QDialog):
    """Dialog for viewing and managing version history."""
    
    def __init__(self, parent, draft_dir, asset_name):
        super().__init__(parent)
        self.draft_dir = Path(draft_dir)
        self.asset_name = asset_name
        
        self.setWindowTitle(f"Version History - {asset_name}")
        self.setMinimumSize(900, 600)
        
        layout = QVBoxLayout(self)
        
        # Info label
        info = QLabel(f"Version history for {asset_name}")
        layout.addWidget(info)
        
        # Split view: versions list on left, diff viewer on right
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: versions list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_layout.addWidget(QLabel("Versions:"))
        self.versions_list = QListWidget()
        self.versions_list.currentItemChanged.connect(self.on_version_selected)
        left_layout.addWidget(self.versions_list)
        
        rollback_btn = QPushButton("Rollback to Selected")
        rollback_btn.clicked.connect(self.rollback_version)
        left_layout.addWidget(rollback_btn)
        
        splitter.addWidget(left_widget)
        
        # Right: diff viewer
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        right_layout.addWidget(QLabel("Diff:"))
        self.diff_view = QPlainTextEdit()
        self.diff_view.setReadOnly(True)
        self.diff_view.setFont(QFont("Courier", 9))
        right_layout.addWidget(self.diff_view)
        
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        # Load versions
        self.load_versions()
    
    def load_versions(self):
        """Load version history."""
        from ..asset_versions import list_versions
        
        self.versions_list.clear()
        
        try:
            versions = list_versions(self.draft_dir, self.asset_name)
            
            if not versions:
                item = QListWidgetItem("No version history available")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.versions_list.addItem(item)
                return
            
            # Add current version
            current_item = QListWidgetItem("Current (working copy)")
            current_item.setData(Qt.ItemDataRole.UserRole, None)
            self.versions_list.addItem(current_item)
            
            # Add historical versions
            for version in versions:
                # timestamp is stored as ISO string, parse it
                from datetime import datetime
                timestamp_dt = datetime.fromisoformat(version.timestamp)
                display = f"Version {version.version} - {timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')}"
                item = QListWidgetItem(display)
                item.setData(Qt.ItemDataRole.UserRole, version.version)
                self.versions_list.addItem(item)
        
        except Exception as e:
            item = QListWidgetItem(f"Error loading versions: {e}")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.versions_list.addItem(item)
    
    def on_version_selected(self, current, previous):
        """Show diff when version is selected."""
        if not current:
            return
        
        version_num = current.data(Qt.ItemDataRole.UserRole)
        
        if version_num is None:
            self.diff_view.setPlainText("(Current working copy selected - no diff)")
            return
        
        try:
            from ..asset_versions import get_diff_from_current
            from ..parse_blocks import ASSET_FILENAMES
            
            # Load current content
            asset_filename = ASSET_FILENAMES.get(self.asset_name)
            if not asset_filename:
                self.diff_view.setPlainText("Error: Unknown asset type")
                return
            
            asset_path = self.draft_dir / asset_filename
            if not asset_path.exists():
                self.diff_view.setPlainText("Error: Asset file not found")
                return
            
            current_content = asset_path.read_text(encoding='utf-8')
            diff_lines = get_diff_from_current(self.draft_dir, self.asset_name, version_num, current_content)
            diff = '\n'.join(diff_lines)
            
            if diff:
                self.diff_view.setPlainText(diff)
            else:
                self.diff_view.setPlainText("(No differences)")
        
        except Exception as e:
            self.diff_view.setPlainText(f"Error getting diff: {e}")
    
    def rollback_version(self):
        """Rollback to selected version."""
        current = self.versions_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", "Please select a version to rollback to")
            return
        
        version_num = current.data(Qt.ItemDataRole.UserRole)
        if version_num is None:
            QMessageBox.information(self, "Already Current", "This is already the current version")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Rollback",
            f"Rollback {self.asset_name} to version {version_num}?\n\nThis will create a new version with the old content.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            from ..asset_versions import rollback_to_version
            from ..parse_blocks import ASSET_FILENAMES
            
            asset_filename = ASSET_FILENAMES.get(self.asset_name)
            if not asset_filename:
                QMessageBox.critical(self, "Rollback Failed", "Unknown asset type")
                return
            
            rollback_to_version(self.draft_dir, self.asset_name, version_num, asset_filename)
            QMessageBox.information(self, "Rollback Complete", f"Rolled back to version {version_num}")
            
            # Reload versions and signal parent to refresh
            self.load_versions()
            self.accept()  # Close dialog after successful rollback
        
        except Exception as e:
            QMessageBox.critical(self, "Rollback Failed", f"Failed to rollback: {e}")


from PySide6.QtWidgets import QWidget


class GenreDialog(QDialog):
    """Dialog for selecting genre."""
    
    GENRES = [
        "Sci-fi",
        "Fantasy",
        "Romance",
        "Horror",
        "Mystery",
        "Drama",
        "Comedy",
        "Action",
        "Thriller",
        "Cyberpunk",
        "Steampunk",
        "Post-Apocalyptic",
        "Slice of Life",
        "Noir",
        "Western",
        "Historical",
        "Superhero",
        "Urban Fantasy",
        "Dark Fantasy",
        "Gothic",
        "Other"
    ]
    
    def __init__(self, parent, draft_dir, current_genre=None):
        super().__init__(parent)
        self.draft_dir = draft_dir
        self.selected_genre = current_genre
        
        self.setWindowTitle("Select Genre")
        self.setMinimumWidth(350)
        
        layout = QVBoxLayout(self)
        
        # Info
        info = QLabel("Select a genre for this character:")
        layout.addWidget(info)
        
        # Genre list
        self.genre_list = QListWidget()
        for genre in self.GENRES:
            item = QListWidgetItem(genre)
            self.genre_list.addItem(item)
            if genre == current_genre:
                item.setSelected(True)
        
        self.genre_list.itemDoubleClicked.connect(self.select_genre)
        layout.addWidget(self.genre_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_genre)
        btn_layout.addWidget(save_btn)
        
        clear_btn = QPushButton("Clear Genre")
        clear_btn.clicked.connect(self.clear_genre)
        btn_layout.addWidget(clear_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def select_genre(self, item):
        """Select genre on double-click."""
        self.selected_genre = item.text()
        self.accept()
    
    def save_genre(self):
        """Save selected genre."""
        current = self.genre_list.currentItem()
        if current:
            self.selected_genre = current.text()
        else:
            self.selected_genre = None
        
        # Save to metadata
        from ..metadata import DraftMetadata
        metadata = DraftMetadata.load(self.draft_dir)
        if metadata:
            metadata.genre = self.selected_genre
            metadata.save(self.draft_dir)
        
        self.accept()
    
    def clear_genre(self):
        """Clear genre."""
        self.selected_genre = None
        
        # Save to metadata
        from ..metadata import DraftMetadata
        metadata = DraftMetadata.load(self.draft_dir)
        if metadata:
            metadata.genre = None
            metadata.save(self.draft_dir)
        
        self.accept()

