"""Theme management for Qt6 GUI."""

from PySide6.QtGui import QTextCharFormat, QColor, QFont, QPalette
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import QRegularExpression, Qt
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from bpui.core.config import Config

# Import unified theme definitions
from bpui.core.theme import BUILTIN_THEMES, load_theme


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
        
        background = app_colors.get("background", DEFAULT_THEME["app"]["background"])
        text = app_colors.get("text", DEFAULT_THEME["app"]["text"])
        accent = app_colors.get("accent", DEFAULT_THEME["app"]["accent"])
        button = app_colors.get("button", DEFAULT_THEME["app"]["button"])
        button_text = app_colors.get("button_text", DEFAULT_THEME["app"]["button_text"])
        border = app_colors.get("border", DEFAULT_THEME["app"]["border"])
        highlight = app_colors.get("highlight", DEFAULT_THEME["app"]["highlight"])
        window = app_colors.get("window", DEFAULT_THEME["app"]["window"])
        
        return f"""
            QMainWindow {{
                background-color: {background};
                color: {text};
            }}
            
            QWidget {{
                background-color: {background};
                color: {text};
            }}
            
            QLabel {{
                color: {text};
            }}
            
            QPushButton {{
                background-color: {button};
                color: {button_text};
                border: 2px solid {border};
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {accent};
            }}
            
            QPushButton:pressed {{
                background-color: {highlight};
            }}
            
            QPushButton:disabled {{
                background-color: {border};
                color: {border};
            }}
            
            QLineEdit {{
                background-color: {window};
                color: {text};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            
            QLineEdit:focus {{
                border: 1px solid {accent};
            }}
            
            QTextEdit, QPlainTextEdit {{
                background-color: {window};
                color: {text};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 4px;
            }}
            
            QTextEdit:focus, QPlainTextEdit:focus {{
                border: 1px solid {accent};
            }}
            
            QComboBox {{
                background-color: {window};
                color: {text};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            
            QComboBox:hover {{
                border: 1px solid {accent};
            }}
            
            QComboBox::drop-down {{
                border: none;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {text};
            }}
            
            QListWidget {{
                background-color: {window};
                color: {text};
                border: 1px solid {border};
                border-radius: 4px;
            }}
            
            QListWidget::item {{
                padding: 4px;
            }}
            
            QListWidget::item:selected {{
                background-color: {accent};
                color: {button_text};
            }}
            
            QListWidget::item:hover {{
                background-color: {highlight};
            }}
            
            QTabWidget::pane {{
                border: 1px solid {border};
                background-color: {window};
            }}
            
            QTabBar::tab {{
                background-color: {button};
                color: {button_text};
                border: 1px solid {border};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 6px 12px;
                margin-right: 2px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {accent};
            }}
            
            QTabBar::tab:hover {{
                background-color: {highlight};
            }}
            
            QTabBar::tab:!selected {{
                margin-top: 2px;
            }}
            
            QScrollBar:vertical {{
                background-color: {window};
                width: 12px;
                border: none;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {border};
                border-radius: 6px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {accent};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            
            QScrollBar:horizontal {{
                background-color: {window};
                height: 12px;
                border: none;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {border};
                border-radius: 6px;
                min-width: 20px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {accent};
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
            }}
            
            QFrame[frameShape="4"] {{
                border: 2px solid {border};
                border-radius: 4px;
                background-color: {window};
            }}
            
            QProgressBar {{
                background-color: {window};
                border: 1px solid {border};
                border-radius: 4px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {accent};
                border-radius: 2px;
            }}
            
            QGroupBox {{
                border: 1px solid {border};
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 4px;
            }}
        """
    
    def apply_theme(self, widget):
        """Apply theme to a widget and all its children."""
        widget.setStyleSheet(self.get_app_stylesheet())
    
    def get_syntax_highlighter(self):
        """Get a syntax highlighter instance."""
        return SyntaxHighlighter(self.theme_colors)
    
    def refresh_theme(self):
        """Reload theme colors from config."""
        self.theme_colors = self.load_theme_colors()