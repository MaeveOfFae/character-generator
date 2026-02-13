"""Batch compilation screen."""
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QComboBox, QListWidget, QListWidgetItem,
    QProgressBar, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
import asyncio


class BatchWorker(QThread):
    """Worker thread for batch compilation."""
    progress = Signal(int, int, str)  # current, total, status_message
    seed_complete = Signal(str, bool, str)  # seed, success, message
    finished = Signal(bool, str)  # success, summary
    
    def __init__(self, seeds, mode, config):
        super().__init__()
        self.seeds = seeds
        self.mode = mode
        self.config = config
        self._running = True
    
    def run(self):
        """Run batch compilation."""
        try:
            asyncio.run(self._run_async())
        except Exception as e:
            self.finished.emit(False, f"Fatal error: {e}")
    
    async def _run_async(self):
        """Async batch compilation with parallel execution using sequential generation."""
        import asyncio
        from ..config import Config
        from ..llm.factory import create_engine
        from ..pack_io import create_draft_dir

        total = len(self.seeds)
        completed = 0
        failed = 0

        # Create LLM engine using factory
        try:
            engine = create_engine(
                self.config,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
        except (ImportError, ValueError, RuntimeError) as e:
            self.finished.emit(False, f"Failed to initialize LLM: {e}")
            return
        
        # Parallel execution with semaphore
        max_concurrent = getattr(self.config, 'batch_max_concurrent', 3)
        rate_limit = getattr(self.config, 'batch_rate_limit_delay', 1.0)
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def compile_one(seed, index):
            """Compile one seed using sequential generation."""
            nonlocal completed, failed
            
            async with semaphore:
                await asyncio.sleep(rate_limit)
                
                try:
                    # Import sequential generation components
                    from ..prompting import build_asset_prompt
                    from ..parse_blocks import extract_single_asset, extract_character_name, ASSET_ORDER
                    
                    # Generate each asset sequentially
                    assets = {}
                    character_name = None
                    
                    for asset_name in ASSET_ORDER:
                        # Build prompt with prior assets as context
                        system_prompt, user_prompt = build_asset_prompt(
                            asset_name, seed, self.mode, assets
                        )
                        
                        # Generate this asset
                        output = await engine.generate(system_prompt, user_prompt)
                        
                        # Parse this asset
                        asset_content = extract_single_asset(output, asset_name)
                        assets[asset_name] = asset_content
                        
                        # Extract character name from character_sheet once available
                        if asset_name == "character_sheet" and not character_name:
                            character_name = extract_character_name(asset_content)
                    
                    if not character_name:
                        character_name = f"character_{index:03d}"
                    
                    # Save
                    draft_dir = create_draft_dir(
                        assets,
                        character_name,
                        seed=seed,
                        mode=self.mode,
                        model=self.config.model
                    )
                    
                    completed += 1
                    self.seed_complete.emit(seed, True, f"Saved to {draft_dir.name}")
                    self.progress.emit(completed, total, f"Completed {completed}/{total} ({failed} failed)")
                
                except Exception as e:
                    completed += 1
                    failed += 1
                    self.seed_complete.emit(seed, False, str(e))
                    self.progress.emit(completed, total, f"Completed {completed}/{total} ({failed} failed)")
        
        # Run all seeds
        tasks = [compile_one(seed, i+1) for i, seed in enumerate(self.seeds)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        summary = f"Batch complete: {completed-failed}/{total} succeeded, {failed} failed"
        self.finished.emit(failed == 0, summary)
    
    def stop(self):
        """Stop the worker."""
        self._running = False


class BatchScreen(QWidget):
    """Batch compilation screen."""
    back_requested = Signal()
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.worker = None
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Batch Compilation")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # Mode selector
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Content Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Auto", "NSFW", "SFW", "Platform-Safe"])
        self.mode_combo.setCurrentText("Auto")
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # Seed input area
        seed_header = QHBoxLayout()
        seed_header.addWidget(QLabel("Seeds (one per line):"))
        
        load_btn = QPushButton("Load from File")
        load_btn.clicked.connect(self.load_seeds_file)
        seed_header.addWidget(load_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_seeds)
        seed_header.addWidget(clear_btn)
        
        seed_header.addStretch()
        layout.addLayout(seed_header)
        
        self.seed_input = QPlainTextEdit()
        self.seed_input.setPlaceholderText("Enter character seeds, one per line...\n\nExample:\nNoir detective with psychic abilities\nCyberpunk hacker with neon dreams\nElven bard who tells dad jokes")
        self.seed_input.setMaximumHeight(150)
        layout.addWidget(self.seed_input)
        
        # Start/Cancel buttons
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Batch")
        self.start_btn.clicked.connect(self.start_batch)
        btn_layout.addWidget(self.start_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_batch)
        self.cancel_btn.setEnabled(False)
        btn_layout.addWidget(self.cancel_btn)
        
        btn_layout.addStretch()
        
        back_btn = QPushButton("Back to Home")
        back_btn.clicked.connect(self.back_requested.emit)
        btn_layout.addWidget(back_btn)
        
        layout.addLayout(btn_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Results list
        layout.addWidget(QLabel("Results:"))
        self.results_list = QListWidget()
        layout.addWidget(self.results_list)
        
        self.setLayout(layout)
    
    def load_seeds_file(self):
        """Load seeds from a text file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Seeds File",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.seed_input.setPlainText(content)
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load file: {e}")
    
    def clear_seeds(self):
        """Clear the seed input."""
        self.seed_input.clear()
        self.results_list.clear()
        self.status_label.clear()
        self.progress_bar.setVisible(False)
    
    def start_batch(self):
        """Start batch compilation."""
        # Get seeds
        text = self.seed_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "No Seeds", "Please enter at least one seed")
            return
        
        seeds = [line.strip() for line in text.split('\n') if line.strip()]
        if not seeds:
            QMessageBox.warning(self, "No Seeds", "No valid seeds found")
            return
        
        # Confirm
        mode = self.mode_combo.currentText()
        reply = QMessageBox.question(
            self,
            "Confirm Batch",
            f"Start batch compilation of {len(seeds)} seeds in {mode} mode?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Clear previous results
        self.results_list.clear()
        
        # Update UI state
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.seed_input.setReadOnly(True)
        self.mode_combo.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(seeds))
        self.progress_bar.setValue(0)
        
        # Start worker
        self.worker = BatchWorker(seeds, mode, self.config)
        self.worker.progress.connect(self.on_progress)
        self.worker.seed_complete.connect(self.on_seed_complete)
        self.worker.finished.connect(self.on_batch_finished)
        self.worker.start()
    
    def cancel_batch(self):
        """Cancel batch compilation."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Cancel Batch",
                "Cancel batch compilation? In-progress generations will complete.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.stop()
                self.status_label.setText("Cancelling...")
                self.cancel_btn.setEnabled(False)
    
    def on_progress(self, current, total, message):
        """Update progress."""
        self.progress_bar.setValue(current)
        self.status_label.setText(message)
    
    def on_seed_complete(self, seed, success, message):
        """Handle seed completion."""
        if success:
            icon = "✅"
            text = f"{icon} {seed}: {message}"
        else:
            icon = "❌"
            text = f"{icon} {seed}: {message}"
        
        item = QListWidgetItem(text)
        self.results_list.addItem(item)
        self.results_list.scrollToBottom()
    
    def on_batch_finished(self, success, summary):
        """Handle batch completion."""
        self.status_label.setText(summary)
        
        # Reset UI state
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.seed_input.setReadOnly(False)
        self.mode_combo.setEnabled(True)
        
        # Show completion message
        if success:
            QMessageBox.information(self, "Batch Complete", summary)
        else:
            QMessageBox.warning(self, "Batch Issues", summary)
        
        self.worker = None
