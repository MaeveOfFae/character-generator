"""Validate directory screen for Blueprint UI."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static, Input, Label, RichLog, Footer
from pathlib import Path


class ValidateScreen(Screen):
    """Validate any directory screen."""
    
    BINDINGS = [
        ("escape,q", "go_back", "Back"),
        ("enter", "run_validation", "Validate"),
    ]

    CSS = """
    ValidateScreen {
        layout: vertical;
    }

    #validate-container {
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

    .field-label {
        margin-top: 1;
        margin-bottom: 0;
    }

    Input {
        width: 100%;
        margin-bottom: 1;
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
        height: 1fr;
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

    def __init__(self, config):
        """Initialize validate screen."""
        super().__init__()
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose validate screen."""
        with Container(id="validate-container"):
            yield Static("✓ Validate Directory", classes="title")

            yield Label("Directory Path:", classes="field-label")
            yield Input(
                value="",
                placeholder="e.g., output/character_name or drafts/...",
                id="directory",
            )

            with Vertical(classes="button-row"):
                yield Button("✓ [Enter] Validate", id="validate", variant="primary")
                yield Button("⬅️  [Q] Back", id="back")

            yield Label("Validation Results:")
            yield RichLog(id="validation-log", highlight=True, markup=True)

            yield Static("", id="status", classes="status")
            yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "validate":
            await self.validate_directory()

    async def validate_directory(self) -> None:
        """Validate the specified directory."""
        status = self.query_one("#status", Static)
        validation_log = self.query_one("#validation-log", RichLog)
        directory_input = self.query_one("#directory", Input)

        directory = directory_input.value.strip()
        if not directory:
            status.update("✗ Please enter a directory path")
            status.add_class("error")
            return

        status.update("⏳ Validating...")
        status.remove_class("error")
        validation_log.clear()

        try:
            from ..validate import validate_pack

            # Resolve path relative to current directory
            pack_dir = Path(directory).expanduser()
            if not pack_dir.is_absolute():
                pack_dir = Path.cwd() / pack_dir
            
            validation_log.write(f"[dim]Checking: {pack_dir}[/dim]\n")
            
            if not pack_dir.exists():
                status.update("✗ Directory does not exist")
                status.add_class("error")
                validation_log.write(f"[red]✗ Directory not found: {pack_dir}[/red]")
                return

            if not pack_dir.is_dir():
                status.update("✗ Path is not a directory")
                status.add_class("error")
                validation_log.write(f"[red]✗ Not a directory: {pack_dir}[/red]")
                return

            result = validate_pack(pack_dir)

            # Display output with formatting
            if result["output"]:
                output_lines = result["output"].strip().split('\n')
                for line in output_lines:
                    if line.startswith('VALIDATION FAILED'):
                        validation_log.write(f"[bold red]{line}[/bold red]")
                    elif line.startswith('OK'):
                        validation_log.write(f"[bold green]{line}[/bold green]")
                    elif line.startswith('- '):
                        # Validation finding
                        validation_log.write(f"[yellow]{line}[/yellow]")
                    else:
                        validation_log.write(line)
            else:
                validation_log.write("[dim]No output from validator[/dim]")
            
            if result["errors"]:
                validation_log.write(f"\n[bold red]Stderr:[/bold red]")
                validation_log.write(result['errors'])

            if result["success"]:
                status.update("✓ Validation passed")
                status.remove_class("error")
            else:
                status.update("✗ Validation failed")
                status.add_class("error")

        except Exception as e:
            validation_log.write(f"[bold red]✗ Error: {e}[/]")
            status.update(f"✗ Error: {e}")
            status.add_class("error")
    
    def action_go_back(self) -> None:
        """Go back to home screen."""
        from .home import HomeScreen
        self.app.switch_screen(HomeScreen(self.config))
    
    def action_run_validation(self) -> None:
        """Run validation (Enter key)."""
        self.run_worker(self.run_validation, exclusive=False)
