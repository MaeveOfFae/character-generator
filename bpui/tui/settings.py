"""Settings screen for Blueprint UI."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Select, Static, Label, Footer
from textual.validation import Function


class SettingsScreen(Screen):
    """Settings configuration screen."""
    
    BINDINGS = [
        ("escape,q", "go_back", "Back"),
        ("t", "test_connection", "Test Connection"),
        ("enter", "save_settings", "Save"),
    ]

    CSS = """
    SettingsScreen {
        align: center middle;
    }

    #settings-container {
        width: 80;
        height: 100%;
        border: solid $primary;
        padding: 2;
    }

    .title {
        content-align: center middle;
        text-style: bold;
        color: $primary;
        margin-bottom: 2;
        margin-top: 1;
    }

    .subtitle {
        content-align: center middle;
        color: $text-muted;
        margin-bottom: 1;
    }

    .field-label {
        margin-top: 1;
        margin-bottom: 0;
        color: $text;
    }

    Input, Select {
        width: 100%;
        margin-bottom: 1;
    }

    .button-row {
        layout: horizontal;
        width: 100%;
        height: auto;
        margin-top: 2;
    }

    .button-row Button {
        width: 1fr;
        margin-right: 1;
    }

    .status {
        margin-top: 1;
        text-align: center;
        color: $success;
    }

    .error {
        color: $error;
    }
    """

    def __init__(self, config):
        """Initialize settings screen."""
        super().__init__()
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose settings screen."""
        with VerticalScroll(id="settings-container"):
            yield Static("⚙️  Settings", classes="title")

            yield Label("Engine:", classes="field-label")
            yield Select(
                [("OpenAI Compatible", "openai_compatible")],
                value=self.config.engine,
                id="engine",
            )

            yield Label("Model:", classes="field-label")
            yield Input(
                value=self.config.model,
                placeholder="e.g., openai/gpt-4 or local-model",
                id="model",
            )

            yield Label("Base URL (OpenAI Compatible only):", classes="field-label")
            yield Input(
                value=self.config.base_url,
                placeholder="e.g., http://localhost:11434/v1",
                id="base_url",
            )

            yield Label("Temperature:", classes="field-label")
            yield Input(
                value=str(self.config.temperature),
                placeholder="0.0 - 2.0",
                id="temperature",
            )

            yield Label("Max Tokens:", classes="field-label")
            yield Input(
                value=str(self.config.max_tokens),
                placeholder="e.g., 4096",
                id="max_tokens",
            )

            yield Static("🔑 API Keys", classes="title")
            yield Static("Enter keys for each provider you use:", classes="subtitle")

            # Common providers
            for provider, label in [
                ("openai", "OpenAI"),
                ("anthropic", "Anthropic"),
                ("deepseek", "DeepSeek"),
                ("google", "Google"),
                ("cohere", "Cohere"),
                ("mistral", "Mistral"),
                ("zai", "Zhipu AI (GLM)"),
                ("moonshot", "Moonshot AI"),
            ]:
                yield Label(f"{label}:", classes="field-label")
                yield Input(
                    value=self.config.get_api_key(provider) or "",
                    placeholder=f"API key for {label}",
                    password=True,
                    id=f"api_key_{provider}",
                )

            yield Label("Environment Variable (legacy fallback):", classes="field-label")
            yield Input(
                value=self.config.get("api_key_env", ""),
                placeholder="e.g., OPENAI_API_KEY",
                id="api_key_env",
            )

            with Vertical(classes="button-row"):
                yield Button("💾 [Enter] Save", id="save", variant="success")
                yield Button("🔌 [T] Test Connection", id="test", variant="primary")
                yield Button("⬅️  [Q] Back", id="back")

            yield Static("", id="status", classes="status")
            yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "back":
            self.app.pop_screen()

        elif event.button.id == "save":
            await self.save_settings()

        elif event.button.id == "test":
            await self.test_connection()

    async def save_settings(self) -> None:
        """Save settings to config file."""
        try:
            engine_select = self.query_one("#engine", Select)
            model_input = self.query_one("#model", Input)
            api_key_env_input = self.query_one("#api_key_env", Input)
            base_url_input = self.query_one("#base_url", Input)
            temp_input = self.query_one("#temperature", Input)
            max_tokens_input = self.query_one("#max_tokens", Input)

            # Get and validate model value
            model_value = model_input.value.strip()
            if not model_value:
                raise ValueError("Model cannot be empty")

            # Save basic settings
            self.config.set("engine", engine_select.value)
            self.config.set("model", model_value)
            self.config.set("api_key_env", api_key_env_input.value)
            self.config.set("base_url", base_url_input.value)
            
            # Validate and save temperature
            try:
                temp_value = float(temp_input.value)
                self.config.set("temperature", temp_value)
            except ValueError:
                raise ValueError("Temperature must be a valid number")
            
            # Validate and save max_tokens
            try:
                max_tokens_value = int(max_tokens_input.value)
                if max_tokens_value <= 0:
                    raise ValueError("Max tokens must be positive")
                self.config.set("max_tokens", max_tokens_value)
            except ValueError as e:
                if "positive" in str(e):
                    raise
                raise ValueError("Max tokens must be a valid integer")

            # Get current API keys
            api_keys = self.config.get("api_keys", {}).copy() if isinstance(self.config.get("api_keys"), dict) else {}

            # Save provider-specific API keys
            for provider in ["openai", "anthropic", "deepseek", "google", "cohere", "mistral", "zai", "moonshot"]:
                api_key_input = self.query_one(f"#api_key_{provider}", Input)
                if api_key_input.value:
                    api_keys[provider] = api_key_input.value
                elif provider in api_keys:
                    # Remove key if input is empty but key exists
                    del api_keys[provider]
            
            # Save updated API keys
            self.config.set("api_keys", api_keys)

            # Save to file
            self.config.save()

            # Verify save by reloading from disk
            self.config.load()
            saved_model = self.config.get("model", "")
            if saved_model != model_value:
                raise ValueError(f"Model save verification failed: expected '{model_value}', got '{saved_model}'")

            status = self.query_one("#status", Static)
            status.update(f"✓ Settings saved! Model: {model_value}")
            status.remove_class("error")
        except Exception as e:
            status = self.query_one("#status", Static)
            status.update(f"✗ Error: {e}")
            status.add_class("error")

    async def test_connection(self) -> None:
        """Test LLM connection."""
        status = self.query_one("#status", Static)
        status.update("⏳ Testing connection...")
        status.remove_class("error")

        try:
            # First update config with current values
            engine_select = self.query_one("#engine", Select)
            model_input = self.query_one("#model", Input)
            base_url_input = self.query_one("#base_url", Input)
            temp_input = self.query_one("#temperature", Input)
            max_tokens_input = self.query_one("#max_tokens", Input)

            # Create temporary config for testing
            from bpui.core.config import Config
            temp_config = Config()
            temp_config.set("engine", engine_select.value)
            temp_config.set("model", model_input.value.strip())
            temp_config.set("base_url", base_url_input.value)
            temp_config.set("temperature", float(temp_input.value))
            temp_config.set("max_tokens", int(max_tokens_input.value))

            # Copy API keys
            api_keys = {}
            for provider in ["openai", "anthropic", "deepseek", "google", "cohere", "mistral", "zai", "moonshot"]:
                api_key_input = self.query_one(f"#api_key_{provider}", Input)
                if api_key_input.value:
                    api_keys[provider] = api_key_input.value
            temp_config.set("api_keys", api_keys)

            # Test with OpenAI Compatible engine
            from ..llm.openai_compat_engine import OpenAICompatEngine
            engine = OpenAICompatEngine(
                model=temp_config.model,
                api_key=temp_config.api_key,
                base_url=temp_config.base_url,
                temperature=temp_config.temperature,
                max_tokens=temp_config.max_tokens,
            )

            result = await engine.test_connection()

            if result["success"]:
                status.update(f"✓ Connected! Latency: {result['latency_ms']}ms")
            else:
                status.update(f"✗ Connection failed: {result['error']}")
                status.add_class("error")

        except Exception as e:
            status.update(f"✗ Error: {e}")
            status.add_class("error")
    
    def action_go_back(self) -> None:
        """Go back to home screen."""
        from .home import HomeScreen
        self.app.switch_screen(HomeScreen(self.config))
    
    def action_test_connection(self) -> None:
        """Test connection (T key)."""
        self.run_worker(self.test_connection, exclusive=False)
    
    def action_save_settings(self) -> None:
        """Save settings (Enter key)."""
        self.run_worker(self.save_settings, exclusive=False)