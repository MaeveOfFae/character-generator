"""Review and save screen for Blueprint UI."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static, TabbedContent, TabPane, TextArea, RichLog
from pathlib import Path


class ReviewScreen(Screen):
    """Review generated assets screen."""

    CSS = """
    ReviewScreen {
        layout: vertical;
    }

    #review-container {
        height: 100%;
        width: 100%;
        padding: 1;
    }

    .title {
        content-align: center middle;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    #tabs {
        height: 1fr;
        margin-bottom: 1;
    }

    TextArea {
        height: 100%;
    }

    .button-row {
        layout: horizontal;
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    .button-row Button {
        width: 1fr;
        margin-right: 1;
    }

    #validation-log {
        height: 10;
        border: solid $primary;
        margin-bottom: 1;
    }

    .status {
        text-align: center;
        color: $text-muted;
    }

    .error {
        color: $error;
    }
    """

    def __init__(self, config, draft_dir: Path, assets: dict):
        """Initialize review screen."""
        super().__init__()
        self.config = config
        self.draft_dir = draft_dir
        self.assets = assets

    def compose(self) -> ComposeResult:
        """Compose review screen."""
        with Container(id="review-container"):
            yield Static(f"📝 Review: {self.draft_dir.name}", classes="title")

            with TabbedContent(id="tabs"):
                with TabPane("System Prompt"):
                    yield TextArea(
                        read_only=True,
                        language="markdown",
                        id="system_prompt_area",
                    )
                with TabPane("Post History"):
                    yield TextArea(
                        read_only=True,
                        language="markdown",
                        id="post_history_area",
                    )
                with TabPane("Character Sheet"):
                    yield TextArea(
                        read_only=True,
                        language="markdown",
                        id="character_sheet_area",
                    )
                with TabPane("Intro Scene"):
                    yield TextArea(
                        read_only=True,
                        language="markdown",
                        id="intro_scene_area",
                    )
                with TabPane("Intro Page"):
                    yield TextArea(
                        read_only=True,
                        language="markdown",
                        id="intro_page_area",
                    )
                with TabPane("A1111"):
                    yield TextArea(
                        read_only=True,
                        language="text",
                        id="a1111_area",
                    )
                with TabPane("Suno"):
                    yield TextArea(
                        read_only=True,
                        language="text",
                        id="suno_area",
                    )

            with Vertical(classes="button-row"):
                yield Button("✓ Validate", id="validate", variant="primary")
                yield Button("📦 Export", id="export", variant="success")
                yield Button("⬅️  Back to Home", id="home")

            yield RichLog(id="validation-log", highlight=True, markup=True)
            yield Static("", id="status", classes="status")

    async def on_mount(self) -> None:
        """Handle mount - load text and auto-validate."""
        validation_log = self.query_one("#validation-log", RichLog)
        validation_log.write(f"[dim]Loading {len(self.assets)} assets...[/dim]")
        
        for asset_name, content in self.assets.items():
            validation_log.write(f"[dim]{asset_name}: {len(content)} chars[/dim]")
        
        # Load text into each TextArea using text property
        try:
            self.query_one("#system_prompt_area", TextArea).text = self.assets.get("system_prompt", "")
            self.query_one("#post_history_area", TextArea).text = self.assets.get("post_history", "")
            self.query_one("#character_sheet_area", TextArea).text = self.assets.get("character_sheet", "")
            self.query_one("#intro_scene_area", TextArea).text = self.assets.get("intro_scene", "")
            self.query_one("#intro_page_area", TextArea).text = self.assets.get("intro_page", "")
            self.query_one("#a1111_area", TextArea).text = self.assets.get("a1111", "")
            self.query_one("#suno_area", TextArea).text = self.assets.get("suno", "")
            validation_log.write("[dim]✓ Text loaded into TextAreas[/dim]")
        except Exception as e:
            validation_log.write(f"[red]Error loading text: {e}[/red]")
        
        await self.validate_pack()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "home":
            from .home import HomeScreen
            self.app.switch_screen(HomeScreen(self.config))

        elif event.button.id == "validate":
            await self.validate_pack()

        elif event.button.id == "export":
            await self.export_pack()

    async def validate_pack(self) -> None:
        """Validate the pack."""
        status = self.query_one("#status", Static)
        validation_log = self.query_one("#validation-log", RichLog)

        status.update("⏳ Validating pack...")
        status.remove_class("error")
        validation_log.clear()

        try:
            from ..validate import validate_pack

            result = validate_pack(self.draft_dir)

            validation_log.write("[bold cyan]Validation Results:[/]\n")
            validation_log.write(result["output"])

            if result["errors"]:
                validation_log.write(f"\n[bold red]Errors:[/]\n{result['errors']}")

            if result["success"]:
                status.update("✓ Validation passed")
            else:
                status.update("✗ Validation failed")
                status.add_class("error")

        except Exception as e:
            validation_log.write(f"[bold red]✗ Error: {e}[/]")
            status.update(f"✗ Error: {e}")
            status.add_class("error")

    async def export_pack(self) -> None:
        """Export the pack."""
        status = self.query_one("#status", Static)
        validation_log = self.query_one("#validation-log", RichLog)

        status.update("⏳ Exporting pack...")
        status.remove_class("error")

        try:
            from ..export import export_character
            from ..parse_blocks import extract_character_name

            character_name = extract_character_name(self.assets["character_sheet"])
            if not character_name:
                character_name = "unnamed_character"

            model_name = self.config.model.split("/")[-1] if "/" in self.config.model else self.config.model

            result = export_character(character_name, self.draft_dir, model_name)

            validation_log.write("\n[bold cyan]Export Results:[/]\n")
            validation_log.write(result["output"])

            if result["errors"]:
                validation_log.write(f"\n[bold red]Errors:[/]\n{result['errors']}")

            if result["success"]:
                status.update(f"✓ Exported to {result['output_dir']}")
            else:
                status.update("✗ Export failed")
                status.add_class("error")

        except Exception as e:
            validation_log.write(f"\n[bold red]✗ Error: {e}[/]")
            status.update(f"✗ Error: {e}")
            status.add_class("error")
