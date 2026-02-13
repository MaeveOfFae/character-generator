"""Seed generator screen with LLM-powered generation."""

import asyncio
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QTextEdit, QSpinBox
)
from PySide6.QtCore import QThread, Signal


class SeedGenWorker(QThread):
    """Worker thread for seed generation."""
    
    output = Signal(str)  # Single seed
    finished = Signal(list)  # All seeds
    error = Signal(str)
    
    def __init__(self, config, genre_lines=None, surprise_mode=False):
        super().__init__()
        self.config = config
        self.genre_lines = genre_lines
        self.surprise_mode = surprise_mode
    
    def run(self):
        """Run seed generation."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            seeds = loop.run_until_complete(self._generate())
            self.finished.emit(seeds)
        except Exception as e:
            self.error.emit(str(e))
    
    async def _generate(self):
        """Generate seeds."""
        from ..llm.litellm_engine import LiteLLMEngine
        
        # Build prompt based on mode
        if self.surprise_mode:
            system_prompt = """You are a creative character concept generator.
Generate diverse, interesting character seeds for roleplay scenarios.
Output exactly 12 creative character concepts, one per line.
Make them varied in genre, tone, and theme.
Include specific details that spark imagination.
Skip numbering or commentary - just the seed lines."""

            user_prompt = """Generate 12 unique character seeds.
Mix genres: fantasy, sci-fi, horror, noir, cyberpunk, romance, thriller, historical, etc.
Include power dynamics, personality quirks, conflicts, or unique hooks.
Be specific and evocative.

Examples (don't copy these):
- Clockwork assassin haunted by memories of their human life
- Fae debt collector who trades in secrets instead of gold
- Retired superhero running a dive bar in the bad part of town
- Moreau bartender with canine traits, secretly investigates missing persons cases

Now generate 12 new seeds:"""
        else:
            from ..prompting import build_seedgen_prompt
            system_prompt, user_prompt = build_seedgen_prompt(self.genre_lines or "")
        
        # Create engine
        engine = LiteLLMEngine(
            model=self.config.model,
            api_key=self.config.get_api_key_for_model(self.config.model),
            base_url=self.config.api_base_url,
            api_version=self.config.api_version
        )
        
        # Generate
        output = await engine.generate(system_prompt, user_prompt)
        
        # Parse seeds (one per line, skip empty and comments)
        seeds = [
            line.strip()
            for line in output.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]
        
        return seeds


class SeedGeneratorScreen(QWidget):
    """Screen for generating character seeds."""
    
    def __init__(self, parent, config):
        super().__init__(parent)
        self.main_window = parent
        self.config = config
        self.worker = None
        self.seeds = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🎲 Seed Generator")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Enter genre lines (one per line) or click Surprise Me for random seeds.\n"
            "Example: fantasy, cyberpunk noir, Victorian horror"
        )
        instructions.setStyleSheet("color: #888; margin: 5px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Genre input
        genre_label = QLabel("Genre Lines (one per line):")
        layout.addWidget(genre_label)
        
        self.genre_input = QTextEdit()
        self.genre_input.setPlaceholderText("fantasy\ncyberpunk noir\nVictorian horror")
        self.genre_input.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                border: 2px solid #444;
                padding: 8px;
                font-family: monospace;
                min-height: 100px;
            }
        """)
        layout.addWidget(self.genre_input)
        
        # Count spinner
        count_layout = QHBoxLayout()
        count_label = QLabel("Seeds per genre:")
        count_layout.addWidget(count_label)
        
        self.count_spin = QSpinBox()
        self.count_spin.setRange(5, 30)
        self.count_spin.setValue(12)
        self.count_spin.setStyleSheet("""
            QSpinBox {
                background-color: #1a1a1a;
                border: 2px solid #444;
                padding: 5px;
            }
        """)
        count_layout.addWidget(self.count_spin)
        count_layout.addStretch()
        layout.addLayout(count_layout)
        
        # Button row
        btn_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Back")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(self.go_back)
        btn_layout.addWidget(back_btn)
        
        btn_layout.addStretch()
        
        self.surprise_btn = QPushButton("🎲 Surprise Me!")
        self.surprise_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d5f5f;
                padding: 10px 20px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #3d6f6f;
            }
        """)
        self.surprise_btn.setToolTip("Generate random creative character seeds without input")
        self.surprise_btn.clicked.connect(self.surprise_me)
        btn_layout.addWidget(self.surprise_btn)
        
        self.generate_btn = QPushButton("✨ Generate Seeds")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a2d5f;
                padding: 10px 20px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #5a3d6f;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_seeds)
        btn_layout.addWidget(self.generate_btn)
        
        self.cancel_btn = QPushButton("⏹️ Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_generation)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        
        # Seeds list
        list_label = QLabel("Generated Seeds (click to use):")
        layout.addWidget(list_label)
        
        self.seeds_list = QListWidget()
        self.seeds_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                border: 2px solid #444;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
            }
            QListWidget::item:selected {
                background-color: #4a2d5f;
            }
        """)
        self.seeds_list.itemDoubleClicked.connect(self.use_seed)
        layout.addWidget(self.seeds_list)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; margin: 5px;")
        layout.addWidget(self.status_label)
    
    def go_back(self):
        """Go back to home screen."""
        if self.main_window and hasattr(self.main_window, 'show_home'):
            self.main_window.show_home()
    
    def surprise_me(self):
        """Generate random creative seeds without genre input."""
        self.status_label.setText("⏳ Generating surprise seeds...")
        self.status_label.setStyleSheet("color: #888;")
        self.generate_btn.setEnabled(False)
        self.surprise_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.seeds_list.clear()
        
        self.worker = SeedGenWorker(self.config, surprise_mode=True)
        self.worker.finished.connect(self.on_seeds_generated)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def generate_seeds(self):
        """Generate seeds from genre input."""
        genre_text = self.genre_input.toPlainText().strip()
        if not genre_text:
            self.status_label.setText("⚠️ Enter at least one genre line")
            self.status_label.setStyleSheet("color: #f80;")
            return
        
        self.status_label.setText("⏳ Generating seeds...")
        self.status_label.setStyleSheet("color: #888;")
        self.generate_btn.setEnabled(False)
        self.surprise_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.seeds_list.clear()
        
        self.worker = SeedGenWorker(self.config, genre_lines=genre_text)
        self.worker.finished.connect(self.on_seeds_generated)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def on_seeds_generated(self, seeds):
        """Handle seeds generated."""
        self.seeds = seeds
        
        for seed in seeds:
            item = QListWidgetItem(seed)
            self.seeds_list.addItem(item)
        
        self.status_label.setText(f"✓ Generated {len(seeds)} seeds")
        self.status_label.setStyleSheet("color: #4a4;")
        self.generate_btn.setEnabled(True)
        self.surprise_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
    
    def on_error(self, error):
        """Handle generation error."""
        self.status_label.setText(f"❌ Error: {error}")
        self.status_label.setStyleSheet("color: #f44;")
        self.generate_btn.setEnabled(True)
        self.surprise_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
    
    def cancel_generation(self):
        """Cancel seed generation."""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self.status_label.setText("⏹️ Generation cancelled")
            self.status_label.setStyleSheet("color: #888;")
            self.generate_btn.setEnabled(True)
            self.surprise_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
    
    def use_seed(self, item):
        """Use selected seed in compile screen."""
        seed = item.text()
        
        # Get main window and switch to compile with this seed
        main_window = self.window()
        if hasattr(main_window, 'compile') and hasattr(main_window, 'show_compile'):
            # Pass seed to show_compile to avoid it being cleared
            main_window.show_compile(seed)  # type: ignore
            self.status_label.setText(f"✓ Using seed: {seed[:50]}...")
            self.status_label.setStyleSheet("color: #4a4;")
