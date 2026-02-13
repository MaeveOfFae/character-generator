"""Context manager for agent awareness of current screen state."""

from typing import Dict, Any, Optional
from pathlib import Path


class AgentContext:
    """Represents the current context for the agent."""
    
    def __init__(
        self,
        screen_name: str = "home",
        screen_title: str = "Home",
        data: Optional[Dict[str, Any]] = None
    ):
        """Initialize agent context.
        
        Args:
            screen_name: Name of the current screen
            screen_title: Human-readable screen title
            data: Additional context data (can contain various types)
        """
        self.screen_name = screen_name
        self.screen_title = screen_title
        self.data: Dict[str, Any] = data if data is not None else {}  # type: ignore[assignment]
        self._timestamp = None
    
    @property
    def timestamp(self) -> str:
        """Get context timestamp."""
        if self._timestamp is None:
            from datetime import datetime
            self._timestamp = datetime.now().isoformat()
        return self._timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "screen": {
                "name": self.screen_name,
                "title": self.screen_title
            },
            "data": self.data,
            "timestamp": self.timestamp
        }
    
    def format_for_prompt(self) -> str:
        """Format context for inclusion in LLM prompt."""
        parts = [f"Current Screen: {self.screen_title} ({self.screen_name})"]
        
        if self.data:
            parts.append("\nContext Data:")
            for key, value in self.data.items():
                if isinstance(value, str):
                    parts.append(f"  - {key}: {value[:200]}{'...' if len(value) > 200 else ''}")
                elif isinstance(value, dict):
                    parts.append(f"  - {key}: {len(value)} items")
                elif isinstance(value, list):
                    parts.append(f"  - {key}: {len(value)} items")
                else:
                    parts.append(f"  - {key}: {str(value)}")
        
        return "\n".join(parts)


class ContextProvider:
    """Base class for context providers."""
    
    def get_context(self) -> Dict[str, Any]:
        """Get context data from this provider."""
        return {}
    
    def get_full_context(self) -> Dict[str, Any]:
        """Get full context including nested data."""
        return self.get_context()


class AgentContextManager:
    """Manages context awareness for the agent."""
    
    def __init__(self, main_window):
        """Initialize context manager.
        
        Args:
            main_window: Reference to the main window
        """
        self.main_window = main_window
        self.current_context: Optional[AgentContext] = None
        self._context_providers: Dict[str, ContextProvider] = {}
    
    def register_provider(self, screen_name: str, provider: ContextProvider) -> None:
        """Register a context provider for a screen.
        
        Args:
            screen_name: Name of the screen
            provider: Context provider instance
        """
        self._context_providers[screen_name] = provider
    
    def update_context(self, screen_name: str, screen_title: Optional[str] = None) -> AgentContext:
        """Update context based on current screen.
        
        Args:
            screen_name: Name of the current screen
            screen_title: Optional title override
        
        Returns:
            Updated AgentContext
        """
        if screen_title is None:
            screen_title = self._get_screen_title(screen_name)
        
        # Get context from provider if available
        context_data = {}
        if screen_name in self._context_providers:
            try:
                context_data = self._context_providers[screen_name].get_full_context()
            except Exception as e:
                print(f"Error getting context from provider: {e}")
        
        self.current_context = AgentContext(
            screen_name=screen_name,
            screen_title=screen_title,
            data=context_data
        )
        
        return self.current_context
    
    def _get_screen_title(self, screen_name: str) -> str:
        """Get human-readable title for screen."""
        titles = {
            "home": "Home Screen",
            "compile": "Character Compiler",
            "batch": "Batch Processing",
            "review": "Character Review",
            "seed_generator": "Seed Generator",
            "validate": "Validation",
            "template_manager": "Template Manager",
            "offspring": "Offspring Generator",
            "similarity": "Similarity Analyzer",
            "blueprint_browser": "Blueprint Browser",
            "blueprint_editor": "Blueprint Editor",
            "asset_designer": "Asset Designer"
        }
        return titles.get(screen_name, screen_name.title())
    
    def get_current_context(self) -> Optional[AgentContext]:
        """Get the current context."""
        return self.current_context
    
    def get_context_summary(self) -> str:
        """Get a summary of the current context."""
        if not self.current_context:
            return "No context available"
        return self.current_context.format_for_prompt()
    
    def enrich_prompt_with_context(self, base_prompt: str) -> str:
        """Enrich a prompt with current context.
        
        Args:
            base_prompt: The original user prompt
        
        Returns:
            Prompt with context information added
        """
        if not self.current_context:
            return base_prompt
        
        context_info = self.current_context.format_for_prompt()
        return f"{context_info}\n\nUser Request:\n{base_prompt}"


class ReviewScreenContextProvider(ContextProvider):
    """Context provider for the review screen."""
    
    def __init__(self, review_widget):
        """Initialize with reference to review widget."""
        self.review_widget = review_widget
    
    def get_full_context(self) -> Dict[str, Any]:
        """Get full context from review screen."""
        context: Dict[str, Any] = {
            "draft_id": str(self.review_widget.draft_dir.name) if self.review_widget.draft_dir else "",
            "draft_path": str(self.review_widget.draft_dir) if self.review_widget.draft_dir else ""
        }
        
        # Add metadata
        try:
            from ..metadata import DraftMetadata
            metadata = DraftMetadata.load(self.review_widget.draft_dir)
            if metadata:
                context["seed"] = metadata.seed[:100] + "..." if len(metadata.seed) > 100 else metadata.seed
                context["mode"] = metadata.mode if metadata.mode else ""
                context["model"] = metadata.model if metadata.model else ""
                context["tags"] = metadata.tags if metadata.tags else []
                context["genre"] = metadata.genre if metadata.genre else ""
                context["favorite"] = metadata.favorite if metadata.favorite is not None else False
        except Exception as e:
            print(f"Error loading metadata: {e}")
        
        # Add current tab content
        try:
            current_tab = self.review_widget.tab_widget.currentIndex()
            asset_keys = list(self.review_widget.text_editors.keys())
            if 0 <= current_tab < len(asset_keys):
                current_asset = asset_keys[current_tab]
                editor = self.review_widget.text_editors[current_asset]
                content = editor.toPlainText()
                
                context["current_asset"] = current_asset
                context["current_asset_content"] = (content[:1000] + "..." if len(content) > 1000 else content)
                
                # Also add all assets (full access mode)
                context["assets"] = {}
                for asset_key, asset_editor in self.review_widget.text_editors.items():
                    asset_content = asset_editor.toPlainText()
                    context["assets"][asset_key] = (asset_content[:2000] + "..." if len(asset_content) > 2000 else asset_content)
        except Exception as e:
            print(f"Error getting editor content: {e}")
        
        return context


class CompileScreenContextProvider(ContextProvider):
    """Context provider for the compile screen."""
    
    def __init__(self, compile_widget):
        """Initialize with reference to compile widget."""
        self.compile_widget = compile_widget
    
    def get_full_context(self) -> Dict[str, Any]:
        """Get full context from compile screen."""
        context: Dict[str, Any] = {}
        
        try:
            if hasattr(self.compile_widget, 'seed_input'):
                context["seed"] = self.compile_widget.seed_input.text()
            
            if hasattr(self.compile_widget, 'template_combo'):
                context["template"] = self.compile_widget.template_combo.currentText()
            
            if hasattr(self.compile_widget, 'output_text'):
                output = self.compile_widget.output_text.toPlainText()
                context["output"] = output[:1000] + "..." if len(output) > 1000 else output
        except Exception as e:
            print(f"Error getting compile context: {e}")
        
        return context


class HomeScreenContextProvider(ContextProvider):
    """Context provider for the home screen."""
    
    def __init__(self, home_widget):
        """Initialize with reference to home widget."""
        self.home_widget = home_widget
    
    def get_full_context(self) -> Dict[str, Any]:
        """Get full context from home screen."""
        context: Dict[str, Any] = {"screen": "home"}
        
        try:
            if hasattr(self.home_widget, 'drafts_list'):
                count = self.home_widget.drafts_list.count()
                context["draft_count"] = count
            
            if hasattr(self.home_widget, 'search_input'):
                context["search_query"] = self.home_widget.search_input.text()
            
            # Get selected draft if any
            if hasattr(self.home_widget, 'drafts_list'):
                current_item = self.home_widget.drafts_list.currentItem()
                if current_item:
                    context["selected_draft"] = current_item.text()
        except Exception as e:
            print(f"Error getting home context: {e}")
        
        return context


class SeedGeneratorContextProvider(ContextProvider):
    """Context provider for seed generator screen."""
    
    def __init__(self, seed_gen_widget):
        """Initialize with reference to seed generator widget."""
        self.seed_gen_widget = seed_gen_widget
    
    def get_full_context(self) -> Dict[str, Any]:
        """Get full context from seed generator screen."""
        context: Dict[str, Any] = {"screen": "seed_generator"}
        
        try:
            # Get genre input
            if hasattr(self.seed_gen_widget, 'genre_input'):
                context["genre_input"] = self.seed_gen_widget.genre_input.toPlainText()
            
            # Get count setting
            if hasattr(self.seed_gen_widget, 'count_spin'):
                context["seeds_per_genre"] = self.seed_gen_widget.count_spin.value()
            
            # Get generated seeds
            if hasattr(self.seed_gen_widget, 'seeds'):
                context["generated_seeds_count"] = len(self.seed_gen_widget.seeds)
                if self.seed_gen_widget.seeds:
                    # Show first few seeds as preview
                    context["seeds_preview"] = self.seed_gen_widget.seeds[:5]
            
            # Check if generation is running
            if hasattr(self.seed_gen_widget, 'worker') and self.seed_gen_widget.worker:
                context["is_generating"] = self.seed_gen_widget.worker.isRunning()
            else:
                context["is_generating"] = False
                
        except Exception as e:
            print(f"Error getting seed generator context: {e}")
        
        return context


class BatchScreenContextProvider(ContextProvider):
    """Context provider for batch processing screen."""
    
    def __init__(self, batch_widget):
        """Initialize with reference to batch widget."""
        self.batch_widget = batch_widget
    
    def get_full_context(self) -> Dict[str, Any]:
        """Get full context from batch screen."""
        context: Dict[str, Any] = {"screen": "batch"}
        
        try:
            # Get seeds input
            if hasattr(self.batch_widget, 'seeds_input'):
                seeds_text = self.batch_widget.seeds_input.toPlainText()
                seeds_lines = [l.strip() for l in seeds_text.split('\n') if l.strip()]
                context["seeds_count"] = len(seeds_lines)
                context["seeds_preview"] = seeds_lines[:3]
            
            # Get mode
            if hasattr(self.batch_widget, 'mode_combo'):
                context["mode"] = self.batch_widget.mode_combo.currentText()
            
            # Check if processing
            if hasattr(self.batch_widget, 'is_processing'):
                context["is_processing"] = self.batch_widget.is_processing
            
        except Exception as e:
            print(f"Error getting batch context: {e}")
        
        return context


class ValidateScreenContextProvider(ContextProvider):
    """Context provider for validate screen."""
    
    def __init__(self, validate_widget):
        """Initialize with reference to validate widget."""
        self.validate_widget = validate_widget
    
    def get_full_context(self) -> Dict[str, Any]:
        """Get full context from validate screen."""
        context: Dict[str, Any] = {"screen": "validate"}
        
        try:
            # Get selected directory
            if hasattr(self.validate_widget, 'path_input'):
                context["selected_path"] = self.validate_widget.path_input.text()
            
            # Get validation results if available
            if hasattr(self.validate_widget, 'results_text'):
                results = self.validate_widget.results_text.toPlainText()
                if results:
                    context["has_results"] = True
                    context["results_preview"] = results[:500]
                
        except Exception as e:
            print(f"Error getting validate context: {e}")
        
        return context