"""Agent action system for performing operations in the GUI."""

from typing import Dict, Any, List, Callable, Optional
from PySide6.QtCore import QObject, Signal
import json


# Action tool definitions for LLM
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "navigate_to_screen",
            "description": "Navigate to a different screen in the application",
            "parameters": {
                "type": "object",
                "properties": {
                    "screen": {
                        "type": "string",
                        "enum": ["home", "compile", "batch", "review", "seed_generator", "validate", "template_manager", "offspring", "similarity"],
                        "description": "The screen to navigate to"
                    }
                },
                "required": ["screen"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_current_asset",
            "description": "Edit the currently visible asset in review mode. Only works when on the review screen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The new content for the asset"
                    },
                    "append": {
                        "type": "boolean",
                        "description": "If true, append to existing content instead of replacing",
                        "default": False
                    }
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "switch_asset_tab",
            "description": "Switch to a different asset tab in review mode",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset": {
                        "type": "string",
                        "enum": ["system_prompt", "post_history", "character_sheet", "intro_scene", "intro_page", "a1111", "suno"],
                        "description": "The asset tab to switch to"
                    }
                },
                "required": ["asset"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_draft",
            "description": "Save the current draft in review mode",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compile_character",
            "description": "Start compiling a character from a seed on the compile screen",
            "parameters": {
                "type": "object",
                "properties": {
                    "seed": {
                        "type": "string",
                        "description": "The character description seed"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["Auto", "SFW", "NSFW", "Platform-Safe"],
                        "description": "Content mode for generation",
                        "default": "Auto"
                    }
                },
                "required": ["seed"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_asset_content",
            "description": "Get the full content of a specific asset in review mode",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset": {
                        "type": "string",
                        "enum": ["system_prompt", "post_history", "character_sheet", "intro_scene", "intro_page", "a1111", "suno"],
                        "description": "The asset to retrieve"
                    }
                },
                "required": ["asset"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_draft",
            "description": "Open a draft by name from the home screen",
            "parameters": {
                "type": "object",
                "properties": {
                    "draft_name": {
                        "type": "string",
                        "description": "The name of the draft to open (e.g., '20260212_154450_kaela')"
                    }
                },
                "required": ["draft_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "export_character",
            "description": "Export the current character pack from review mode",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Optional character name for export. If not provided, uses character name from sheet."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_screen_state",
            "description": "Get detailed information about the current screen including visible elements, field values, and available actions",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_drafts",
            "description": "Get a list of all available character drafts with their metadata",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of drafts to return (default: 20)",
                        "default": 20
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_drafts",
            "description": "Search for drafts by name, seed, tags, or other metadata",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query text"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_compile_status",
            "description": "Check if a character compilation is currently in progress and get its status",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_seeds",
            "description": "Generate character seeds using the seed generator with optional genre input",
            "parameters": {
                "type": "object",
                "properties": {
                    "genres": {
                        "type": "string",
                        "description": "Genre lines separated by newlines (e.g., 'fantasy\\ncyberpunk noir'). If empty, uses surprise mode."
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of seeds to generate per genre (default: 12)",
                        "default": 12
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "use_seed_from_generator",
            "description": "Take a generated seed from the seed generator and use it in the compile screen",
            "parameters": {
                "type": "object",
                "properties": {
                    "seed_index": {
                        "type": "integer",
                        "description": "Index of the seed to use (0-based) from the generated seeds list"
                    }
                },
                "required": ["seed_index"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_generated_seeds",
            "description": "Get the list of currently generated seeds from the seed generator",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "start_batch_compilation",
            "description": "Start batch compilation of multiple character seeds",
            "parameters": {
                "type": "object",
                "properties": {
                    "seeds": {
                        "type": "string",
                        "description": "Seeds separated by newlines, one seed per line"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["Auto", "SFW", "NSFW", "Platform-Safe"],
                        "description": "Content mode for generation",
                        "default": "Auto"
                    }
                },
                "required": ["seeds"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_character_pack",
            "description": "Validate a character pack directory for errors and issues",
            "parameters": {
                "type": "object",
                "properties": {
                    "draft_name": {
                        "type": "string",
                        "description": "Name of the draft to validate (e.g., '20260212_154450_kaela')"
                    }
                },
                "required": ["draft_name"]
            }
        }
    }
]


class AgentActionHandler(QObject):
    """Handles execution of agent actions."""
    
    action_completed = Signal(str, bool, str)  # action_name, success, message
    
    def __init__(self, main_window):
        """Initialize action handler.
        
        Args:
            main_window: Reference to main window
        """
        super().__init__()
        self.main_window = main_window
        self._actions: Dict[str, Callable] = {
            "navigate_to_screen": self._navigate_to_screen,
            "edit_current_asset": self._edit_current_asset,
            "switch_asset_tab": self._switch_asset_tab,
            "save_draft": self._save_draft,
            "compile_character": self._compile_character,
            "get_asset_content": self._get_asset_content,
            "open_draft": self._open_draft,
            "export_character": self._export_character,
            "get_screen_state": self._get_screen_state,
            "list_available_drafts": self._list_available_drafts,
            "search_drafts": self._search_drafts,
            "get_compile_status": self._get_compile_status,
            "generate_seeds": self._generate_seeds,
            "use_seed_from_generator": self._use_seed_from_generator,
            "get_generated_seeds": self._get_generated_seeds,
            "start_batch_compilation": self._start_batch_compilation,
            "validate_character_pack": self._validate_character_pack,
        }
    
    def execute_action(self, action_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an agent action.
        
        Args:
            action_name: Name of the action to execute
            arguments: Action arguments
        
        Returns:
            Result dict with success status and message
        """
        if action_name not in self._actions:
            return {
                "success": False,
                "message": f"Unknown action: {action_name}"
            }
        
        try:
            result = self._actions[action_name](**arguments)
            self.action_completed.emit(action_name, True, result.get("message", ""))
            return result
        except Exception as e:
            error_msg = f"Action failed: {str(e)}"
            self.action_completed.emit(action_name, False, error_msg)
            return {
                "success": False,
                "message": error_msg
            }
    
    def _navigate_to_screen(self, screen: str) -> Dict[str, Any]:
        """Navigate to a screen."""
        screen_map = {
            "home": self.main_window.show_home,
            "compile": self.main_window.show_compile,
            "batch": self.main_window.show_batch,
            "seed_generator": self.main_window.show_seed_generator,
            "validate": self.main_window.show_validate,
            "template_manager": self.main_window.show_template_manager,
            "offspring": self.main_window.show_offspring,
            "similarity": self.main_window.show_similarity,
        }
        
        if screen not in screen_map:
            return {"success": False, "message": f"Unknown screen: {screen}"}
        
        screen_map[screen]()
        return {"success": True, "message": f"Navigated to {screen}"}
    
    def _edit_current_asset(self, content: str, append: bool = False) -> Dict[str, Any]:
        """Edit the current asset in review mode."""
        current_screen = self.main_window.stack.currentWidget()
        
        # Check if we're on review screen
        from .review import ReviewWidget
        if not isinstance(current_screen, ReviewWidget):
            return {"success": False, "message": "Not on review screen"}
        
        review_widget = current_screen
        current_tab = review_widget.tab_widget.currentIndex()
        asset_keys = list(review_widget.text_editors.keys())
        
        if current_tab < 0 or current_tab >= len(asset_keys):
            return {"success": False, "message": "No asset tab selected"}
        
        asset_key = asset_keys[current_tab]
        editor = review_widget.text_editors[asset_key]
        
        if append:
            existing = editor.toPlainText()
            editor.setPlainText(existing + "\n\n" + content)
        else:
            editor.setPlainText(content)
        
        return {"success": True, "message": f"Updated {asset_key}"}
    
    def _switch_asset_tab(self, asset: str) -> Dict[str, Any]:
        """Switch to a different asset tab."""
        current_screen = self.main_window.stack.currentWidget()
        
        from .review import ReviewWidget
        if not isinstance(current_screen, ReviewWidget):
            return {"success": False, "message": "Not on review screen"}
        
        review_widget = current_screen
        asset_keys = list(review_widget.text_editors.keys())
        
        if asset not in asset_keys:
            return {"success": False, "message": f"Asset not found: {asset}"}
        
        index = asset_keys.index(asset)
        review_widget.tab_widget.setCurrentIndex(index)
        
        return {"success": True, "message": f"Switched to {asset}"}
    
    def _save_draft(self) -> Dict[str, Any]:
        """Save the current draft."""
        current_screen = self.main_window.stack.currentWidget()
        
        from .review import ReviewWidget
        if not isinstance(current_screen, ReviewWidget):
            return {"success": False, "message": "Not on review screen"}
        
        review_widget = current_screen
        review_widget.save_changes()
        
        return {"success": True, "message": "Draft saved"}
    
    def _compile_character(self, seed: str, mode: str = "Auto") -> Dict[str, Any]:
        """Compile a character."""
        # Navigate to compile screen
        self.main_window.show_compile()
        
        # Get compile widget
        compile_widget = self.main_window.compile
        
        # Set seed and mode
        compile_widget.seed_input.setText(seed)
        
        # Set mode
        mode_index = compile_widget.mode_combo.findText(mode)
        if mode_index >= 0:
            compile_widget.mode_combo.setCurrentIndex(mode_index)
        
        # Start compilation
        compile_widget.start_compilation()
        
        return {"success": True, "message": f"Started compiling character with seed: {seed[:50]}..."}
    
    def _get_asset_content(self, asset: str) -> Dict[str, Any]:
        """Get full asset content."""
        current_screen = self.main_window.stack.currentWidget()
        
        from .review import ReviewWidget
        if not isinstance(current_screen, ReviewWidget):
            return {"success": False, "message": "Not on review screen"}
        
        review_widget = current_screen
        
        if asset not in review_widget.text_editors:
            return {"success": False, "message": f"Asset not found: {asset}"}
        
        content = review_widget.text_editors[asset].toPlainText()
        
        return {
            "success": True,
            "message": f"Retrieved {asset}",
            "content": content
        }
    
    def _open_draft(self, draft_name: str) -> Dict[str, Any]:
        """Open a draft by name."""
        from pathlib import Path
        
        draft_path = Path("drafts") / draft_name
        if not draft_path.exists():
            return {"success": False, "message": f"Draft not found: {draft_name}"}
        
        self.main_window.show_review(draft_path)
        
        return {"success": True, "message": f"Opened draft: {draft_name}"}
    
    def _export_character(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Export character pack."""
        current_screen = self.main_window.stack.currentWidget()
        
        from .review import ReviewWidget
        if not isinstance(current_screen, ReviewWidget):
            return {"success": False, "message": "Not on review screen"}
        
        review_widget = current_screen
        
        # Trigger export
        if hasattr(review_widget, 'export_pack'):
            review_widget.export_pack()
            return {"success": True, "message": "Export started"}
        else:
            return {"success": False, "message": "Export not available"}
    
    def _get_screen_state(self) -> Dict[str, Any]:
        """Get detailed state of current screen."""
        current_screen = self.main_window.stack.currentWidget()
        screen_info = {
            "success": True,
            "screen_type": type(current_screen).__name__,
            "screen_name": "unknown",
            "elements": {}
        }
        
        # Detect screen type and gather relevant state
        from .review import ReviewWidget
        from .compile import CompileWidget
        from .home import HomeWidget
        from .seed_generator import SeedGeneratorScreen
        from .batch import BatchScreen
        from .validate import ValidateScreen
        
        if isinstance(current_screen, ReviewWidget):
            screen_info["screen_name"] = "review"
            
            # Get current tab
            current_tab = current_screen.tab_widget.currentIndex()
            asset_keys = list(current_screen.text_editors.keys())
            if 0 <= current_tab < len(asset_keys):
                current_asset = asset_keys[current_tab]
                screen_info["elements"]["current_asset_tab"] = current_asset
                screen_info["elements"]["available_asset_tabs"] = asset_keys
            
            # Get draft info
            if current_screen.draft_dir:
                screen_info["elements"]["draft_name"] = current_screen.draft_dir.name
                screen_info["elements"]["draft_path"] = str(current_screen.draft_dir)
            
            # Check if there are unsaved changes
            screen_info["elements"]["has_changes"] = hasattr(current_screen, 'has_unsaved_changes')
            
        elif isinstance(current_screen, CompileWidget):
            screen_info["screen_name"] = "compile"
            
            # Get form values
            if hasattr(current_screen, 'seed_input'):
                screen_info["elements"]["seed"] = current_screen.seed_input.text()
            
            if hasattr(current_screen, 'mode_combo'):
                screen_info["elements"]["mode"] = current_screen.mode_combo.currentText()
            
            if hasattr(current_screen, 'template_combo'):
                screen_info["elements"]["template"] = current_screen.template_combo.currentText()
            
            # Check if compilation is running
            if hasattr(current_screen, 'worker') and current_screen.worker is not None:
                screen_info["elements"]["is_compiling"] = current_screen.worker.isRunning()
            else:
                screen_info["elements"]["is_compiling"] = False
            
            # Get output preview
            if hasattr(current_screen, 'output_text'):
                output = current_screen.output_text.toPlainText()
                screen_info["elements"]["output_preview"] = output[:500] + "..." if len(output) > 500 else output
                screen_info["elements"]["output_length"] = len(output)
            
        elif isinstance(current_screen, HomeWidget):
            screen_info["screen_name"] = "home"
            
            # Get drafts list info
            if hasattr(current_screen, 'drafts_list'):
                screen_info["elements"]["draft_count"] = current_screen.drafts_list.count()
                
                # Get selected draft
                current_item = current_screen.drafts_list.currentItem()
                if current_item:
                    screen_info["elements"]["selected_draft"] = current_item.text()
            
            # Get search query
            if hasattr(current_screen, 'search_input'):
                screen_info["elements"]["search_query"] = current_screen.search_input.text()
            
            # Get filter settings (if available)
            if hasattr(current_screen, 'filter_combo'):
                screen_info["elements"]["active_filter"] = current_screen.filter_combo.currentText()  # type: ignore[attr-defined]
        
        elif isinstance(current_screen, SeedGeneratorScreen):
            screen_info["screen_name"] = "seed_generator"
            
            # Get genre input
            if hasattr(current_screen, 'genre_input'):
                screen_info["elements"]["genre_input"] = current_screen.genre_input.toPlainText()
            
            # Get count
            if hasattr(current_screen, 'count_spin'):
                screen_info["elements"]["seeds_per_genre"] = current_screen.count_spin.value()
            
            # Get generated seeds
            if hasattr(current_screen, 'seeds'):
                screen_info["elements"]["generated_seeds_count"] = len(current_screen.seeds)
                if current_screen.seeds:
                    screen_info["elements"]["seeds_preview"] = current_screen.seeds[:5]
            
            # Check if generating
            if hasattr(current_screen, 'worker') and current_screen.worker:
                screen_info["elements"]["is_generating"] = current_screen.worker.isRunning()
            else:
                screen_info["elements"]["is_generating"] = False
        
        elif isinstance(current_screen, BatchScreen):
            screen_info["screen_name"] = "batch"
            
            # Get seeds input
            if hasattr(current_screen, 'seeds_input'):
                seeds_text = current_screen.seeds_input.toPlainText()  # type: ignore[attr-defined]
                seeds_lines = [l.strip() for l in seeds_text.split('\n') if l.strip()]
                screen_info["elements"]["seeds_count"] = len(seeds_lines)
                screen_info["elements"]["seeds_preview"] = seeds_lines[:3]
            
            # Get mode
            if hasattr(current_screen, 'mode_combo'):
                screen_info["elements"]["mode"] = current_screen.mode_combo.currentText()
            
            # Check if processing
            if hasattr(current_screen, 'is_processing'):
                screen_info["elements"]["is_processing"] = current_screen.is_processing  # type: ignore[attr-defined]
        
        elif isinstance(current_screen, ValidateScreen):
            screen_info["screen_name"] = "validate"
            
            # Get selected path
            if hasattr(current_screen, 'path_input'):
                screen_info["elements"]["selected_path"] = current_screen.path_input.text()  # type: ignore[attr-defined]
            
            # Get validation results
            if hasattr(current_screen, 'results_text'):
                results = current_screen.results_text.toPlainText()
                if results:
                    screen_info["elements"]["has_results"] = True
                    screen_info["elements"]["results_preview"] = results[:500]
        
        else:
            # Generic screen
            screen_info["screen_name"] = screen_info["screen_type"]
        
        return screen_info
    
    def _list_available_drafts(self, limit: int = 20) -> Dict[str, Any]:
        """List available drafts with metadata."""
        from pathlib import Path
        
        drafts_dir = Path("drafts")
        if not drafts_dir.exists():
            return {
                "success": True,
                "message": "No drafts directory found",
                "drafts": []
            }
        
        drafts = []
        for draft_path in sorted(drafts_dir.iterdir(), reverse=True):
            if not draft_path.is_dir():
                continue
            
            draft_info: Dict[str, Any] = {
                "name": draft_path.name,
                "path": str(draft_path)
            }
            
            # Try to load metadata
            try:
                from ..metadata import DraftMetadata
                metadata = DraftMetadata.load(draft_path)
                if metadata:
                    draft_info["seed"] = metadata.seed[:100] + "..." if len(metadata.seed) > 100 else metadata.seed
                    draft_info["mode"] = metadata.mode
                    draft_info["model"] = metadata.model
                    draft_info["tags"] = metadata.tags or []
                    draft_info["genre"] = metadata.genre
                    draft_info["favorite"] = metadata.favorite
            except Exception:
                pass
            
            drafts.append(draft_info)
            
            if len(drafts) >= limit:
                break
        
        return {
            "success": True,
            "message": f"Found {len(drafts)} drafts",
            "drafts": drafts,
            "total_available": len(list(drafts_dir.iterdir()))
        }
    
    def _search_drafts(self, query: str) -> Dict[str, Any]:
        """Search for drafts by query."""
        from pathlib import Path
        
        drafts_dir = Path("drafts")
        if not drafts_dir.exists():
            return {
                "success": True,
                "message": "No drafts directory found",
                "drafts": []
            }
        
        query_lower = query.lower()
        matching_drafts = []
        
        for draft_path in sorted(drafts_dir.iterdir(), reverse=True):
            if not draft_path.is_dir():
                continue
            
            # Check if query matches name
            if query_lower in draft_path.name.lower():
                matching_drafts.append({
                    "name": draft_path.name,
                    "path": str(draft_path),
                    "match_reason": "name"
                })
                continue
            
            # Check metadata
            try:
                from ..metadata import DraftMetadata
                metadata = DraftMetadata.load(draft_path)
                if metadata:
                    # Check seed
                    if query_lower in metadata.seed.lower():
                        match_info: Dict[str, Any] = {
                            "name": draft_path.name,
                            "path": str(draft_path),
                            "match_reason": "seed",
                            "seed": metadata.seed[:100]
                        }
                        matching_drafts.append(match_info)
                        continue
                    
                    # Check tags
                    if metadata.tags:
                        for tag in metadata.tags:
                            if query_lower in tag.lower():
                                tag_match_info: Dict[str, Any] = {
                                    "name": draft_path.name,
                                    "path": str(draft_path),
                                    "match_reason": f"tag: {tag}",
                                    "tags": metadata.tags
                                }
                                matching_drafts.append(tag_match_info)
                                break
            except Exception:
                pass
        
        return {
            "success": True,
            "message": f"Found {len(matching_drafts)} matching drafts",
            "drafts": matching_drafts
        }
    
    def _get_compile_status(self) -> Dict[str, Any]:
        """Get compilation status."""
        compile_widget = self.main_window.compile
        
        is_compiling = False
        if hasattr(compile_widget, 'worker') and compile_widget.worker is not None:
            is_compiling = compile_widget.worker.isRunning()
        
        status_info = {
            "success": True,
            "is_compiling": is_compiling
        }
        
        if is_compiling:
            # Get progress info if available
            if hasattr(compile_widget, 'output_text'):
                output = compile_widget.output_text.toPlainText()
                status_info["output_length"] = len(output)
                status_info["preview"] = output[-200:] if len(output) > 200 else output
        else:
            status_info["message"] = "No compilation in progress"
        
        return status_info
    
    def _generate_seeds(self, genres: str = "", count: int = 12) -> Dict[str, Any]:
        """Generate seeds using the seed generator."""
        # Navigate to seed generator
        if hasattr(self.main_window, 'show_seed_generator'):
            self.main_window.show_seed_generator()  # type: ignore[attr-defined]
        else:
            return {"success": False, "message": "Seed generator not available"}
        
        # Get seed generator widget
        seed_gen = None
        if hasattr(self.main_window, 'seed_generator'):
            seed_gen = self.main_window.seed_generator  # type: ignore[attr-defined]
        
        if not seed_gen:
            return {"success": False, "message": "Could not access seed generator"}
        
        # Set genre input and count
        if hasattr(seed_gen, 'genre_input'):
            seed_gen.genre_input.setPlainText(genres)
        
        if hasattr(seed_gen, 'count_spin'):
            seed_gen.count_spin.setValue(count)
        
        # Start generation
        if genres.strip():
            if hasattr(seed_gen, 'generate_seeds'):
                seed_gen.generate_seeds()
                return {
                    "success": True,
                    "message": f"Started generating seeds for genres: {genres[:50]}..."
                }
        else:
            # Surprise mode
            if hasattr(seed_gen, 'surprise_me'):
                seed_gen.surprise_me()
                return {
                    "success": True,
                    "message": "Started generating surprise seeds"
                }
        
        return {"success": False, "message": "Could not start seed generation"}
    
    def _use_seed_from_generator(self, seed_index: int) -> Dict[str, Any]:
        """Use a seed from the generator."""
        current_screen = self.main_window.stack.currentWidget()
        
        from .seed_generator import SeedGeneratorScreen
        if not isinstance(current_screen, SeedGeneratorScreen):
            return {"success": False, "message": "Not on seed generator screen"}
        
        seed_gen = current_screen
        
        # Check if we have seeds
        if not hasattr(seed_gen, 'seeds') or not seed_gen.seeds:
            return {"success": False, "message": "No seeds generated yet"}
        
        if seed_index < 0 or seed_index >= len(seed_gen.seeds):
            return {
                "success": False,
                "message": f"Invalid seed index {seed_index}. Available: 0-{len(seed_gen.seeds)-1}"
            }
        
        seed = seed_gen.seeds[seed_index]
        
        # Use the seed
        if hasattr(self.main_window, 'compile'):
            self.main_window.compile.seed_input.setText(seed)
            self.main_window.show_compile()
            return {
                "success": True,
                "message": f"Using seed: {seed[:50]}..."
            }
        
        return {"success": False, "message": "Could not access compile screen"}
    
    def _get_generated_seeds(self) -> Dict[str, Any]:
        """Get list of generated seeds."""
        current_screen = self.main_window.stack.currentWidget()
        
        from .seed_generator import SeedGeneratorScreen
        if not isinstance(current_screen, SeedGeneratorScreen):
            return {"success": False, "message": "Not on seed generator screen"}
        
        seed_gen = current_screen
        
        if not hasattr(seed_gen, 'seeds') or not seed_gen.seeds:
            return {
                "success": True,
                "message": "No seeds generated yet",
                "seeds": []
            }
        
        return {
            "success": True,
            "message": f"Found {len(seed_gen.seeds)} generated seeds",
            "seeds": seed_gen.seeds,
            "count": len(seed_gen.seeds)
        }
    
    def _start_batch_compilation(self, seeds: str, mode: str = "Auto") -> Dict[str, Any]:
        """Start batch compilation."""
        # Navigate to batch screen
        if hasattr(self.main_window, 'show_batch'):
            self.main_window.show_batch()  # type: ignore[attr-defined]
        else:
            return {"success": False, "message": "Batch screen not available"}
        
        # Get batch widget
        batch_widget = None
        if hasattr(self.main_window, 'batch'):
            batch_widget = self.main_window.batch  # type: ignore[attr-defined]
        
        if not batch_widget:
            return {"success": False, "message": "Could not access batch screen"}
        
        # Set seeds
        if hasattr(batch_widget, 'seeds_input'):
            batch_widget.seeds_input.setPlainText(seeds)
        
        # Set mode
        if hasattr(batch_widget, 'mode_combo'):
            mode_index = batch_widget.mode_combo.findText(mode)
            if mode_index >= 0:
                batch_widget.mode_combo.setCurrentIndex(mode_index)
        
        # Start processing
        if hasattr(batch_widget, 'start_batch'):
            batch_widget.start_batch()
            seed_lines = [l.strip() for l in seeds.split('\n') if l.strip()]
            return {
                "success": True,
                "message": f"Started batch compilation of {len(seed_lines)} seeds"
            }
        
        return {"success": False, "message": "Could not start batch compilation"}
    
    def _validate_character_pack(self, draft_name: str) -> Dict[str, Any]:
        """Validate a character pack."""
        from pathlib import Path
        
        draft_path = Path("drafts") / draft_name
        if not draft_path.exists():
            return {"success": False, "message": f"Draft not found: {draft_name}"}
        
        # Navigate to validate screen
        if hasattr(self.main_window, 'show_validate'):
            self.main_window.show_validate()  # type: ignore[attr-defined]
        else:
            return {"success": False, "message": "Validate screen not available"}
        
        # Get validate widget
        validate_widget = None
        if hasattr(self.main_window, 'validate'):
            validate_widget = self.main_window.validate  # type: ignore[attr-defined]
        
        if not validate_widget:
            return {"success": False, "message": "Could not access validate screen"}
        
        # Set path
        if hasattr(validate_widget, 'path_input'):
            validate_widget.path_input.setText(str(draft_path))
        
        # Run validation
        if hasattr(validate_widget, 'validate_pack'):
            validate_widget.validate_pack()
            return {
                "success": True,
                "message": f"Started validation of {draft_name}"
            }
        
        return {"success": False, "message": "Could not start validation"}
