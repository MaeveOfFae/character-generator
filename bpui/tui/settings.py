"""Settings screen for Blueprint UI."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Select, Static, Label
from textual.validation import Function


class SettingsScreen(Screen):
    """Settings configuration screen."""

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
                [("LiteLLM", "litellm"), ("OpenAI Compatible", "openai_compatible")],
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
                yield Button("💾 Save", id="save", variant="success")
                yield Button("🔌 Test Connection", id="test", variant="primary")
                yield Button("⬅️  Back", id="back")

            yield Static("", id="status", classes="status")

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

            self.config.set("engine", engine_select.value)
            self.config.set("model", model_input.value)
            self.config.set("api_key_env", api_key_env_input.value)
            self.config.set("base_url", base_url_input.value)
            self.config.set("temperature", float(temp_input.value))
            self.config.set("max_tokens", int(max_tokens_input.value))

            # Save provider-specific API keys
            for provider in ["openai", "anthropic", "deepseek", "google", "cohere", "mistral"]:
                api_key_input = self.query_one(f"#api_key_{provider}", Input)
                if api_key_input.value:
                    self.config.set_api_key(provider, api_key_input.value)

            self.config.save()

            status = self.query_one("#status", Static)
            status.update("✓ Settings saved!")
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
            from ..llm.litellm_engine import LiteLLMEngine
            from ..llm.openai_compat_engine import OpenAICompatEngine

            if self.config.engine == "litellm":
                engine = LiteLLMEngine(
                    model=self.config.model,
                    api_key=self.config.api_key,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
            else:
                engine = OpenAICompatEngine(
                    model=self.config.model,
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
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
