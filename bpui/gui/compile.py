"""Compile screen widget."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QPlainTextEdit, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from pathlib import Path
import asyncio


class CompileWorker(QThread):
    """Worker thread for compilation."""
    
    output = Signal(str)
    finished = Signal(dict, Path)
    error = Signal(str)
    
    def __init__(self, config, seed, mode, template=None):
        super().__init__()
        self.config = config
        self.seed = seed
        self.mode = mode
        self.template = template  # Template object or None for default
    
    def run(self):
        """Run compilation."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._compile())
            loop.close()
            
            if result:
                assets, draft_dir = result
                self.finished.emit(assets, draft_dir)
        except Exception as e:
            self.error.emit(str(e))
    
    async def _compile(self):
        """Perform compilation using sequential generation (like TUI)."""
        from ..prompting import build_asset_prompt
        from ..llm.factory import create_engine
        from ..parse_blocks import extract_single_asset, extract_character_name
        from bpui.utils.file_io.pack_io import create_draft_dir
        from bpui.utils.topological_sort import topological_sort
        from bpui.features.templates.templates import TemplateManager
        from datetime import datetime

        self.output.emit(f"Compiling with seed: {self.seed}\n")
        self.output.emit(f"Mode: {self.mode or 'Auto'}\n")
        if self.template:
            self.output.emit(f"Template: {self.template.name}\n")
        self.output.emit("\nStarting sequential generation...\n\n")

        # Get LLM engine using factory
        try:
            engine = create_engine(
                self.config,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
        except (ImportError, ValueError) as e:
            raise RuntimeError(f"Failed to create engine: {e}")
        
        # Determine asset order from template
        if not self.template:
            raise RuntimeError("No template selected for compilation.")
        
        try:
            asset_order = topological_sort(self.template.assets)
        except ValueError as e:
            raise RuntimeError(f"Failed to sort assets in template '{self.template.name}': {e}")

        manager = TemplateManager()

        # Generate each asset sequentially
        assets = {}
        character_name = None
        
        for asset_name in asset_order:
            self.output.emit(f"→ Generating {asset_name}...\n")
            
            # Get blueprint content
            blueprint_content = manager.get_blueprint_content(self.template, asset_name)
            if not blueprint_content:
                raise RuntimeError(f"Blueprint for asset '{asset_name}' not found in template '{self.template.name}'.")

            # Build prompt with prior assets as context
            system_prompt, user_prompt = build_asset_prompt(
                asset_name, self.seed, self.mode, assets, blueprint_content=blueprint_content
            )
            
            # Generate this asset
            raw_output = ""
            async for chunk in engine.generate_stream(system_prompt, user_prompt):
                raw_output += chunk
                self.output.emit(chunk)
            
            # Parse this asset
            try:
                asset_content = extract_single_asset(raw_output, asset_name)
                assets[asset_name] = asset_content
                self.output.emit(f"\n✓ {asset_name} complete ({len(asset_content)} chars)\n\n")
                
                # Extract character name from character_sheet once available
                if asset_name == "character_sheet" and not character_name:
                    character_name = extract_character_name(asset_content)
                    if character_name:
                        self.output.emit(f"Character: {character_name}\n\n")
            
            except Exception as e:
                self.output.emit(f"\n✗ Failed to parse {asset_name}: {e}\n")
                raise
        
        if not character_name:
            character_name = "unnamed_character"
        
        # Save draft with metadata
        self.output.emit("\nSaving draft...\n")
        draft_dir = create_draft_dir(
            assets, 
            character_name,
            seed=self.seed,
            mode=self.mode,
            model=self.config.model
        )
        
        self.output.emit(f"\n✓ Saved to: {draft_dir}\n")
        
        return assets, draft_dir


class CompileWidget(QWidget):
    """Compile screen."""
    
    def __init__(self, config, main_window):
        super().__init__()
        self.config = config
        self.main_window = main_window
        self.worker = None
        self.templates = []  # Cache of available templates
        
        self.setup_ui()
    
    def load_templates(self):
        """Load available templates into combo box."""
        from bpui.features.templates.templates import TemplateManager
        
        self.template_combo.clear()
        
        try:
            manager = TemplateManager()
            self.templates = manager.list_templates()
            
            for template in self.templates:
                label = f"{template.name} ({len(template.assets)} assets)"
                if template.is_official:
                    label += " ★"
                self.template_combo.addItem(label, template.name)
            
            # Select "Official Aksho" template by default
            for i, template in enumerate(self.templates):
                if template.name == "Official Aksho":
                    self.template_combo.setCurrentIndex(i)
                    break
        
        except Exception as e:
            self.template_combo.addItem(f"Error loading templates: {e}", None)
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("🌱 Compile from Seed")
        title_font = QFont("Arial", 18, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Input form
        form_frame = QFrame()
        form_frame.setFrameShape(QFrame.Shape.StyledPanel)
        form_layout = QVBoxLayout(form_frame)
        
        # Seed input
        seed_label = QLabel("Seed:")
        seed_label.setStyleSheet("font-weight: bold;")
        form_layout.addWidget(seed_label)
        
        self.seed_input = QLineEdit()
        self.seed_input.setPlaceholderText("e.g., Noir detective with psychic abilities")
        self.seed_input.setMinimumHeight(35)
        form_layout.addWidget(self.seed_input)
        
        # Mode selector
        mode_label = QLabel("Content Mode:")
        mode_label.setStyleSheet("font-weight: bold;")
        form_layout.addWidget(mode_label)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Auto (infer from seed)", "SFW", "NSFW", "Platform-Safe"])
        self.mode_combo.setMinimumHeight(35)
        form_layout.addWidget(self.mode_combo)
        
        # Template selector
        template_label = QLabel("Template:")
        template_label.setStyleSheet("font-weight: bold;")
        form_layout.addWidget(template_label)
        
        self.template_combo = QComboBox()
        self.template_combo.setMinimumHeight(35)
        self.load_templates()
        form_layout.addWidget(self.template_combo)
        
        layout.addWidget(form_frame)
        
        # Output log
        output_label = QLabel("Output:")
        output_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(output_label)
        
        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Courier New", 10))
        self.output_text.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1a1a1a;
                border: 2px solid #444;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.output_text, 1)
        
        # Button bar
        btn_layout = QHBoxLayout()
        
        self.compile_btn = QPushButton("▶️ Compile")
        self.compile_btn.setFixedSize(150, 40)
        self.compile_btn.setStyleSheet("background-color: #2d5f2d; font-weight: bold;")
        self.compile_btn.clicked.connect(self.start_compile)
        btn_layout.addWidget(self.compile_btn)
        
        self.cancel_btn = QPushButton("⏹️ Cancel")
        self.cancel_btn.setFixedSize(120, 40)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_compile)
        btn_layout.addWidget(self.cancel_btn)
        
        btn_layout.addStretch()
        
        back_btn = QPushButton("⬅️ Back")
        back_btn.setFixedSize(100, 40)
        back_btn.clicked.connect(self.main_window.show_home)
        btn_layout.addWidget(back_btn)
        
        layout.addLayout(btn_layout)
    
    def set_seed(self, seed):
        """Set the seed input."""
        self.seed_input.setText(seed)
    
    def generate_seed(self):
        """Generate a random seed idea using LLM."""
        from PySide6.QtWidgets import QMessageBox
        from ..llm.litellm_engine import LiteLLMEngine
        import asyncio
        
        # Ask for genre/style
        from PySide6.QtWidgets import QInputDialog
        genre, ok = QInputDialog.getText(
            self,
            "Seed Generator",
            "Optional genre/style (leave empty for random):",
            text=""
        )
        
        if not ok:
            return
        
        try:
            # Create simple prompt for seed generation
            if genre.strip():
                prompt = f"Generate a unique, creative character concept seed in the {genre} genre. Output ONLY a single sentence describing the character concept. Be specific and intriguing. Example format: 'Cyberpunk hacker with synesthesia who can taste digital code'"
            else:
                prompt = "Generate a unique, creative character concept seed for roleplay. Output ONLY a single sentence describing the character concept. Be specific and intriguing. Mix genres if interesting. Example format: 'Victorian ghost hunter who accidentally became undead'"
            
            # Quick sync call
            engine = LiteLLMEngine(
                model=self.config.model,
                api_key=self.config.get_api_key_for_model(self.config.model),
                base_url=self.config.api_base_url,
                api_version=self.config.api_version
            )
            
            # Run async in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            seed = loop.run_until_complete(engine.generate_chat([{"role": "user", "content": prompt}]))
            loop.close()
            
            # Clean up and set
            seed = seed.strip().strip('"').strip("'")
            self.seed_input.setText(seed)
            
        except Exception as e:
            QMessageBox.warning(self, "Generator Error", f"Failed to generate seed: {e}")
    
    def start_compile(self):
        """Start compilation."""
        seed = self.seed_input.text().strip()
        if not seed:
            self.main_window.status_bar.showMessage("Please enter a seed", 3000)
            return
        
        # Get mode
        mode_text = self.mode_combo.currentText()
        if mode_text.startswith("Auto"):
            mode = None
        elif mode_text == "SFW":
            mode = "SFW"
        elif mode_text == "NSFW":
            mode = "NSFW"
        else:
            mode = "Platform-Safe"
        
        # Get selected template
        template_name = self.template_combo.currentData()
        if not template_name:
            self.main_window.status_bar.showMessage("Please select a template", 3000)
            return
        
        # Find template object
        template = None
        for t in self.templates:
            if t.name == template_name:
                template = t
                break
        
        if not template:
            self.main_window.status_bar.showMessage("Template not found", 3000)
            return
        
        # Clear output
        self.output_text.clear()
        
        # Disable compile button
        self.compile_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        
        # Start worker with template
        self.worker = CompileWorker(self.config, seed, mode, template)
        self.worker.output.connect(self.append_output)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def append_output(self, text):
        """Append text to output."""
        self.output_text.insertPlainText(text)
        self.output_text.ensureCursorVisible()
    
    def on_finished(self, assets, draft_dir):
        """Handle compilation finished."""
        self.compile_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.main_window.status_bar.showMessage(f"✓ Compilation complete: {draft_dir.name}", 5000)
        
        # Switch to review screen
        self.main_window.show_review(draft_dir, assets)
    
    def on_error(self, error):
        """Handle compilation error."""
        self.append_output(f"\n\n✗ Error: {error}\n")
        self.compile_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.main_window.status_bar.showMessage(f"✗ Compilation failed", 5000)
    
    def cancel_compile(self):
        """Cancel compilation."""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self.append_output("\n\n⏹️ Compilation cancelled\n")
            self.compile_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
