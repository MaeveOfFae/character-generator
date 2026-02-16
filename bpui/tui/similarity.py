"""Similarity analyzer screen for TUI."""

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Header,
    Select,
    Static,
    Footer,
    ProgressBar,
    Label,
    Checkbox,
)
from textual import on

from bpui.utils.file_io.pack_io import list_drafts
from bpui.features.similarity.engine import SimilarityAnalyzer, format_similarity_report


class SimilarityScreen(Screen):
    """Character similarity analysis screen."""
    
    BINDINGS = [
        ("q", "app.pop_screen", "Quit"),
        ("escape", "app.pop_screen", "Back"),
    ]
    
    CSS = """
    SimilarityScreen {
        align: center middle;
    }
    
    #similarity-container {
        width: 80;
        height: auto;
        border: solid $primary;
        padding: 2;
    }
    
    .title {
        content-align: center middle;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    Button {
        width: 100%;
        margin-bottom: 1;
    }
    
    #results-container {
        margin-top: 1;
        border-top: solid $panel;
        padding-top: 1;
    }
    
    #results-text {
        height: 30;
        overflow-y: auto;
    }
    """
    
    def __init__(self, config):
        """Initialize similarity screen."""
        super().__init__()
        self.config = config
        self.analyzer = SimilarityAnalyzer()
        self.drafts_root = Path.cwd() / "drafts"
        self.draft_list = []
        self.result = None
        self.use_llm = False
    
    def on_mount(self) -> None:
        """Load drafts when screen is mounted."""
        self._load_drafts()
    
    def _load_drafts(self) -> None:
        """Load list of available drafts."""
        try:
            draft_paths = list_drafts(self.drafts_root)
            self.draft_list = [
                (draft.name, draft)
                for draft in sorted(draft_paths, key=lambda x: x.name)
            ]
        except Exception as e:
            self.draft_list = []
            print(f"Error loading drafts: {e}")
    
    def compose(self) -> ComposeResult:
        """Compose similarity screen."""
        with Container(id="similarity-container"):
            yield Static("🔍 Character Similarity Analyzer", classes="title")
            yield Static("Compare two characters to find commonalities and differences")
            yield Static("")
            
            # Character 1 selection
            yield Label("Select First Character:")
            yield Select(
                [(name, draft) for name, draft in self.draft_list],
                id="character1_select",
                prompt="Character 1",
                value=None,
            )
            
            # Character 2 selection
            yield Label("Select Second Character:")
            yield Select(
                [(name, draft) for name, draft in self.draft_list],
                id="character2_select",
                prompt="Character 2",
                value=None,
            )
            
            yield Static("")
            
            # LLM analysis checkbox
            yield Checkbox(
                "Enable LLM Deep Analysis",
                id="use_llm",
                value=False,
                tooltip="Use LLM for deeper character relationship analysis"
            )
            
            yield Static("")
            
            # Compare button
            yield Button("🔍 Compare Characters", id="compare", variant="primary")
            yield Button("❌ Cancel", id="cancel", variant="error")
            
            # Results area (hidden initially)
            with Container(id="results-container"):
                yield Static("📊 Results", classes="title")
                yield Static("", id="results-text")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "cancel":
            self.app.pop_screen()
        elif event.button.id == "compare":
            self._compare_characters()
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox change."""
        if event.checkbox.id == "use_llm":
            self.use_llm = event.value
    
    def _compare_characters(self) -> None:
        """Compare two selected characters."""
        # Get selected drafts
        char1_select = self.query_one("#character1_select", Select)
        char2_select = self.query_one("#character2_select", Select)
        
        # Check if values are set
        if not char1_select.value or not char2_select.value:
            self._show_error("Please select both characters")
            return
        
        # Convert to Path (handle None/NoSelection)
        draft1 = char1_select.value if isinstance(char1_select.value, Path) else None
        draft2 = char2_select.value if isinstance(char2_select.value, Path) else None
        
        if not draft1 or not draft2:
            self._show_error("Please select both characters")
            return
        
        if draft1 == draft2:
            self._show_error("Please select different characters")
            return
        
        # Setup LLM engine if requested
        use_llm = self.use_llm
        llm_engine = None
        
        if use_llm:
            from ..llm.litellm_engine import LiteLLMEngine
            from ..llm.openai_compat_engine import OpenAICompatEngine
            
            try:
                engine_config = {
                    'model': self.config.model,
                    'temperature': self.config.temperature,
                    'max_tokens': self.config.max_tokens,
                }
                
                if self.config.engine == "litellm":
                    import litellm
                    llm_engine = LiteLLMEngine(**engine_config)
                else:
                    llm_engine = OpenAICompatEngine(**engine_config)
                
                self._show_status("Comparing with LLM analysis...")
            except Exception as e:
                self._show_error(f"LLM error: {e}. Using basic analysis.")
                use_llm = False
        else:
            self._show_status("Comparing characters...")
        
        # Perform comparison
        try:
            result = self.analyzer.compare_drafts(draft1, draft2, use_llm=use_llm, llm_engine=llm_engine)
            
            if result:
                self.result = result
                self._show_results(result)
            else:
                self._show_error("Failed to compare characters")
        
        except Exception as e:
            self._show_error(f"Error comparing characters: {e}")
    
    def _show_results(self, result) -> None:
        """Show comparison results."""
        # Format and display results
        report = format_similarity_report(result)
        results_text = self.query_one("#results-text", Static)
        results_text.update(report)
    
    def _show_error(self, message: str) -> None:
        """Show error message."""
        results_text = self.query_one("#results-text", Static)
        results_text.update(f"⚠️ {message}")
    
    def _show_status(self, message: str) -> None:
        """Show status message."""
        results_text = self.query_one("#results-text", Static)
        results_text.update(f"ℹ️ {message}")
