#!/usr/bin/env python3
"""Minimal test of TextArea rendering."""

from textual.app import App, ComposeResult
from textual.widgets import TextArea, Button
from textual.containers import Container


class TestApp(App):
    """Test app."""
    
    def compose(self) -> ComposeResult:
        """Compose UI."""
        with Container():
            yield TextArea("Initial text in constructor", id="area1")
            yield TextArea(id="area2")
            yield Button("Load Text", id="load")
    
    async def on_mount(self) -> None:
        """Mount - try setting text."""
        area2 = self.query_one("#area2", TextArea)
        area2.text = "Text set in on_mount"
    
    async def on_button_pressed(self) -> None:
        """Load more text."""
        area2 = self.query_one("#area2", TextArea)
        area2.text = "Text changed on button press"


if __name__ == "__main__":
    TestApp().run()
