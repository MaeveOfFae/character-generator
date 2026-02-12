"""Main window for Qt6 GUI."""

from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QStatusBar
)
from PySide6.QtCore import Qt

from .home import HomeWidget
from .compile import CompileWidget
from .review import ReviewWidget
from .batch import BatchScreen
from .theme import ThemeManager


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.theme_manager = ThemeManager(config)
        
        self.setWindowTitle("Blueprint UI")
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply theme to entire window
        self.theme_manager.apply_theme(self)
        
        # Stacked widget for screens
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Create screens
        from .seed_generator import SeedGeneratorScreen
        from .validate import ValidateScreen
        from .template_manager import TemplateManagerScreen
        from .offspring import OffspringWidget
        from .similarity import SimilarityWidget
        
        self.home = HomeWidget(self.config, self)
        self.compile = CompileWidget(self.config, self)
        self.batch = BatchScreen(self.config)
        self.seed_gen = SeedGeneratorScreen(self, self.config)
        self.validate = ValidateScreen(self, self.config)
        self.template_manager = TemplateManagerScreen(self, self.config)
        self.offspring = OffspringWidget(self.config, self)
        self.similarity = SimilarityWidget(self)
        
        # Add screens to stack
        self.stack.addWidget(self.home)
        self.stack.addWidget(self.compile)
        self.stack.addWidget(self.batch)
        self.stack.addWidget(self.seed_gen)
        self.stack.addWidget(self.validate)
        self.stack.addWidget(self.template_manager)
        self.stack.addWidget(self.offspring)
        self.stack.addWidget(self.similarity)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Connect signals
        self.batch.back_requested.connect(self.show_home)
        
        # Start on home screen
        self.show_home()
    
    def show_home(self):
        """Show home screen."""
        self.stack.setCurrentWidget(self.home)
        self.home.refresh()
    
    def show_compile(self, seed=""):
        """Show compile screen."""
        self.compile.set_seed(seed)
        self.stack.setCurrentWidget(self.compile)
    
    def show_batch(self):
        """Show batch screen."""
        self.stack.setCurrentWidget(self.batch)
    
    def show_seed_generator(self):
        """Show seed generator screen."""
        self.stack.setCurrentWidget(self.seed_gen)
        self.status_bar.showMessage("Seed Generator")
    
    def show_validate(self):
        """Show validate screen."""
        self.stack.setCurrentWidget(self.validate)
        self.status_bar.showMessage("Validate Directory")
    
    def show_template_manager(self):
        """Show template manager screen."""
        self.stack.setCurrentWidget(self.template_manager)
        self.status_bar.showMessage("Template Manager")
    
    def show_offspring(self):
        """Show offspring generator screen."""
        self.stack.setCurrentWidget(self.offspring)
        self.status_bar.showMessage("Offspring Generator")
    
    def show_similarity(self):
        """Show similarity analyzer screen."""
        self.stack.setCurrentWidget(self.similarity)
        self.status_bar.showMessage("Similarity Analyzer")
    
    def show_review(self, draft_dir, assets):
        """Show review screen."""
        review = ReviewWidget(self.config, self, draft_dir, assets)
        
        # Remove old review widgets
        for i in range(self.stack.count()):
            widget = self.stack.widget(i)
            if isinstance(widget, ReviewWidget) and widget != review:
                self.stack.removeWidget(widget)
                widget.deleteLater()
        
        self.stack.addWidget(review)
        self.stack.setCurrentWidget(review)
    
    def refresh_all_highlighters(self):
        """Refresh syntax highlighters in all review widgets."""
        for i in range(self.stack.count()):
            widget = self.stack.widget(i)
            if isinstance(widget, ReviewWidget):
                widget.refresh_highlighters()
