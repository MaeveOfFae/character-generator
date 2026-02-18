"""Theme management for Qt6 GUI."""

from PySide6.QtGui import QTextCharFormat, QColor, QFont, QPalette
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import QRegularExpression, Qt
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from bpui.core.config import Config

# Import unified theme definitions
from bpui.core.theme import BUILTIN_THEMES, load_theme, reload_themes


# Legacy DEFAULT_THEME for backward compatibility
DEFAULT_THEME = {
    "tokenizer": BUILTIN_THEMES["dark"].tokenizer_colors,
    "app": BUILTIN_THEMES["dark"].app_colors,
}


class SyntaxHighlighter:
    """Syntax highlighter for tokenizer patterns."""
    
    PATTERNS = [
        ("brackets", r"\[[^\]]*\]"),  # [text]
        ("asterisk", r"\*\*[^*]+\*\*"),  # **text**
        ("parentheses", r"\([^)]*\)"),  # (text)
        ("double_brackets", r"\{\{[^}]+\}\}"),  # {{text}}
        ("curly_braces", r"\{[^}]+\}"),  # {text}
        ("pipes", r"\|[^|]+\|"),  # |text|
        ("at_sign", r"@[^\s@]+"),  # @text
    ]
    
    def __init__(self, theme_colors: Dict[str, Any]):
        """Initialize highlighter with theme colors."""
        self.theme_colors = theme_colors
        self.formats = self._create_formats()
    
    def _create_formats(self) -> Dict[str, QTextCharFormat]:
        """Create text formats for each pattern."""
        formats = {}
        tokenizer_colors = self.theme_colors.get("tokenizer", DEFAULT_THEME["tokenizer"])
        
        for pattern_name, pattern in self.PATTERNS:
            color = tokenizer_colors.get(pattern_name, DEFAULT_THEME["tokenizer"][pattern_name])
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            fmt.setFontWeight(QFont.Weight.Bold)
            formats[pattern_name] = fmt
        
        return formats
    
    def get_highlight_data(self, text: str):
        """Get highlight data for text.
        
        Returns a list of tuples (start, end, QTextCharFormat) for each match.
        """
        highlights = []
        
        for pattern_name, pattern_regex in self.PATTERNS:
            regex = QRegularExpression(pattern_regex)
            match_iterator = regex.globalMatch(text)
            
            while match_iterator.hasNext():
                match = match_iterator.next()
                start = match.capturedStart()
                end = match.capturedEnd()
                highlights.append((start, end, self.formats[pattern_name]))
        
        # Sort by start position
        highlights.sort(key=lambda x: x[0])
        
        return highlights


class ThemeManager:
    """Manages application theme and color application."""
    
    def __init__(self, config):
        """Initialize theme manager from config."""
        self.config = config
        self.theme_colors = self.load_theme_colors()
    
    def load_theme_colors(self) -> Dict[str, Any]:
        """Load theme colors from config using unified theme system."""
        # Load theme using unified system
        theme_def = load_theme(self.config)
        
        # Return in legacy format for compatibility
        return {
            "tokenizer": theme_def.tokenizer_colors,
            "app": theme_def.app_colors
        }
    
    def get_app_stylesheet(self) -> str:
        """Generate application stylesheet from theme colors."""
        app_colors = self.theme_colors.get("app", DEFAULT_THEME["app"])

        bg = app_colors.get("background", DEFAULT_THEME["app"]["background"])
        txt = app_colors.get("text", DEFAULT_THEME["app"]["text"])
        acc = app_colors.get("accent", DEFAULT_THEME["app"]["accent"])
        btn = app_colors.get("button", DEFAULT_THEME["app"]["button"])
        btn_txt = app_colors.get("button_text", DEFAULT_THEME["app"]["button_text"])
        bdr = app_colors.get("border", DEFAULT_THEME["app"]["border"])
        hi = app_colors.get("highlight", DEFAULT_THEME["app"]["highlight"])
        win = app_colors.get("window", DEFAULT_THEME["app"]["window"])
        muted = app_colors.get("muted_text", DEFAULT_THEME["app"]["muted_text"])

        return f"""
QMainWindow, QWidget {{ background-color: {bg}; color: {txt}; border: none; }}
QLabel {{ color: {txt}; padding: 2px; }}
QLabel#subtitleLabel {{ color: {muted}; font-size: 14px; }}

QListWidget#draftsList {{
    background-color: {win};
    border: 1px solid {bdr};
    border-radius: 5px;
    font-size: 13px;
}}
QListWidget#draftsList::item {{
    padding: 10px;
    border-bottom: 1px solid {bdr};
}}
QListWidget#draftsList::item:hover {{
    background-color: {hi};
}}
QListWidget#draftsList::item:selected {{
    background-color: {acc};
}}

QPushButton {{
    background-color: {btn}; color: {btn_txt}; border: 1px solid {bdr};
    border-radius: 4px; padding: 8px 12px;
}}
QPushButton:hover {{ background-color: {acc}; border-color: {acc}; }}
QPushButton:pressed {{ background-color: {hi}; }}
QPushButton:disabled {{ background-color: {bdr}; color: {muted}; }}

QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QListWidget {{
    background-color: {win}; color: {txt}; border: 1px solid {bdr};
    border-radius: 4px; padding: 4px;
}}
QLineEdit, QComboBox {{ padding: 4px 8px; min-height: 24px; }}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:hover {{ border-color: {acc}; }}

QComboBox::drop-down {{ border: none; }}
QComboBox::down-arrow {{
    image: none; border-left: 5px solid transparent;
    border-right: 5px solid transparent; border-top: 5px solid {txt};
}}

QListWidget::item {{ padding: 4px; }}
QListWidget::item:selected {{ background-color: {acc}; color: {btn_txt}; }}
QListWidget::item:hover {{ background-color: {hi}; }}

QTabWidget::pane {{ border: 1px solid {bdr}; background-color: {win}; border-radius: 4px; }}
QTabBar::tab {{
    background-color: {btn}; color: {btn_txt}; border: 1px solid {bdr};
    border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px;
    padding: 8px 14px; margin-right: 2px;
}}
QTabBar::tab:selected {{ background-color: {acc}; }}
QTabBar::tab:hover {{ background-color: {hi}; }}
QTabBar::tab:!selected {{ margin-top: 2px; background-color: {bdr}; }}

QScrollBar:vertical {{ background-color: {win}; width: 14px; border: none; margin: 0; }}
QScrollBar:horizontal {{ background-color: {win}; height: 14px; border: none; margin: 0; }}
QScrollBar::handle {{
    background-color: {bdr}; border-radius: 7px;
}}
QScrollBar::handle:vertical {{ min-height: 24px; }}
QScrollBar::handle:horizontal {{ min-width: 24px; }}
QScrollBar::handle:hover {{ background-color: {acc}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ border: none; background: none; height: 0; width: 0; }}
QScrollBar::up-arrow, QScrollBar::down-arrow, QScrollBar::left-arrow, QScrollBar::right-arrow {{ background: none; }}

QFrame[frameShape="6"] {{ /* StyledPanel */
    border: 1px solid {bdr};
    border-radius: 4px;
    background-color: {win};
}}
QFrame[frameShape="4"] {{ /* HLine */
    border: none;
    border-top: 1px solid {bdr};
    margin: 4px 0;
}}
QFrame[frameShape="5"] {{ /* VLine */
    border: none;
    border-left: 1px solid {bdr};
    margin: 0 4px;
}}

QProgressBar {{
    background-color: {win}; border: 1px solid {bdr};
    border-radius: 4px; text-align: center;
}}
QProgressBar::chunk {{ background-color: {acc}; border-radius: 2px; }}

QGroupBox {{
    border: 1px solid {bdr};
    border-radius: 6px;
    margin-top: 10px;
    padding: 12px;
    background-color: {win};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    margin-left: 10px;
    background-color: {win};
}}
"""
    
    def apply_theme(self, widget):
        """Apply theme to a widget and all its children."""
        widget.setStyleSheet(self.get_app_stylesheet())
    
    def get_syntax_highlighter(self):
        """Get a syntax highlighter instance."""
        return SyntaxHighlighter(self.theme_colors)
    
    def refresh_theme(self):
        """Reload all themes from disk and refresh the UI."""
        reload_themes()
        self.theme_colors = self.load_theme_colors()