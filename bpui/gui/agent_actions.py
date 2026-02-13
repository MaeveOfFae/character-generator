"""Agent action system for performing operations in the GUI."""

from typing import Dict, Any, List, Callable, Optional
from PySide6.QtCore import QObject, Signal, QTimer
import json
import time
import traceback
from functools import wraps
from collections import defaultdict


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
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_draft_metadata",
            "description": "Get metadata for the currently open draft in review mode (name, model, seed, mode, tags, genre, etc.)",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


class AgentActionHandler(QObject):
    """Handles execution of agent actions with error handling, timeouts, and circuit breaker."""
    
    action_completed = Signal(str, bool, str)  # action_name, success, message
    
    def __init__(self, main_window):
        """Initialize action handler.
        
        Args:
            main_window: Reference to main window
        """
        super().__init__()
        self.main_window = main_window
        
        # Configuration
        self.DEFAULT_TIMEOUT = 30.0  # seconds
        self.MAX_RETRIES = 2
        self.CIRCUIT_BREAKER_THRESHOLD = 3  # failures before opening circuit
        self.CIRCUIT_BREAKER_TIMEOUT = 60.0  # seconds to wait before retry
        
        # Circuit breaker state
        self._failure_counts: Dict[str, int] = defaultdict(int)
        self._circuit_open: Dict[str, float] = {}  # action_name -> timestamp when opened
        self._last_error: Dict[str, str] = {}  # action_name -> last error message
        
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
            "get_current_draft_metadata": self._get_current_draft_metadata,
        }
    
    def execute_action(self, action_name: str, arguments: Dict[str, Any], timeout: Optional[float] = None) -> Dict[str, Any]:
        """Execute an agent action with error handling, timeout, and circuit breaker.
        
        Args:
            action_name: Name of the action to execute
            arguments: Action arguments
            timeout: Timeout in seconds (uses DEFAULT_TIMEOUT if not specified)
        
        Returns:
            Result dict with success status, message, and optional error details
        """
        if action_name not in self._actions:
            return {
                "success": False,
                "message": f"Unknown action: {action_name}",
                "error_type": "unknown_action"
            }
        
        # Check circuit breaker
        if action_name in self._circuit_open:
            time_since_open = time.time() - self._circuit_open[action_name]
            if time_since_open < self.CIRCUIT_BREAKER_TIMEOUT:
                return {
                    "success": False,
                    "message": f"Action '{action_name}' temporarily disabled due to repeated failures. Last error: {self._last_error.get(action_name, 'unknown')}. Retry in {int(self.CIRCUIT_BREAKER_TIMEOUT - time_since_open)}s.",
                    "error_type": "circuit_breaker_open",
                    "retry_after": int(self.CIRCUIT_BREAKER_TIMEOUT - time_since_open)
                }
            else:
                # Timeout expired, reset circuit breaker
                del self._circuit_open[action_name]
                self._failure_counts[action_name] = 0
        
        # Validate arguments
        validation_result = self._validate_arguments(action_name, arguments)
        if not validation_result["valid"]:
            return {
                "success": False,
                "message": f"Invalid arguments: {validation_result['error']}",
                "error_type": "validation_error",
                "suggestion": validation_result.get("suggestion")
            }
        
        # Execute with retry logic
        timeout_seconds = timeout or self.DEFAULT_TIMEOUT
        last_error: Optional[str] = None
        error_type = "execution_error"  # default
        attempt = 0
        
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                # Execute with timeout
                result = self._execute_with_timeout(
                    action_name,
                    arguments,
                    timeout_seconds
                )
                
                # Success - reset failure count
                if action_name in self._failure_counts:
                    self._failure_counts[action_name] = 0
                
                self.action_completed.emit(action_name, True, result.get("message", ""))
                return result
                
            except TimeoutError as e:
                last_error = f"Action timed out after {timeout_seconds}s"
                error_type = "timeout"
                # Don't retry on timeout
                break
                
            except ValueError as e:
                # Validation or argument errors - don't retry
                last_error = f"Invalid input: {str(e)}"
                error_type = "validation_error"
                break
                
            except Exception as e:
                last_error = str(e)
                error_type = "execution_error"
                
                # For transient errors, retry
                if attempt < self.MAX_RETRIES:
                    # Exponential backoff
                    wait_time = 0.5 * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                break
        
        # All retries failed
        self._failure_counts[action_name] += 1
        error_message = last_error or "Unknown error"
        self._last_error[action_name] = error_message
        
        # Check if we should open circuit breaker
        if self._failure_counts[action_name] >= self.CIRCUIT_BREAKER_THRESHOLD:
            self._circuit_open[action_name] = time.time()
            error_msg = f"Action '{action_name}' failed {self._failure_counts[action_name]} times. Circuit breaker activated. {error_message}"
        else:
            error_msg = f"Action failed after {self.MAX_RETRIES + 1} attempts: {error_message}"
        
        self.action_completed.emit(action_name, False, error_msg)
        
        return {
            "success": False,
            "message": error_msg,
            "error_type": error_type,
            "attempts": attempt + 1,
            "suggestion": self._get_error_suggestion(action_name, error_type, error_message)
        }
    
    def _execute_with_timeout(self, action_name: str, arguments: Dict[str, Any], timeout: float) -> Dict[str, Any]:
        """Execute action with timeout.
        
        Note: This is a simple timeout implementation. For production,
        consider using QTimer or threading.Timer for true async timeout.
        """
        start_time = time.time()
        
        try:
            result = self._actions[action_name](**arguments)
            
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Action exceeded timeout of {timeout}s")
            
            # Ensure result is a dict
            if not isinstance(result, dict):
                result = {"success": True, "message": str(result)}
            
            # Add timing info
            result["execution_time"] = round(elapsed, 2)
            
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Action exceeded timeout of {timeout}s")
            raise
    
    def _validate_arguments(self, action_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate action arguments against tool definition."""
        # Find tool definition
        tool_def = None
        for tool in AGENT_TOOLS:
            if tool["function"]["name"] == action_name:
                tool_def = tool["function"]
                break
        
        if not tool_def:
            return {"valid": True}  # No validation available
        
        params = tool_def.get("parameters", {})
        required = params.get("required", [])
        properties = params.get("properties", {})
        
        # Check required parameters
        for req_param in required:
            if req_param not in arguments:
                return {
                    "valid": False,
                    "error": f"Missing required parameter: {req_param}",
                    "suggestion": f"Add '{req_param}' parameter to the action call"
                }
        
        # Validate parameter types and enums
        for param_name, param_value in arguments.items():
            if param_name not in properties:
                continue
            
            prop = properties[param_name]
            
            # Check enum values
            if "enum" in prop:
                if param_value not in prop["enum"]:
                    return {
                        "valid": False,
                        "error": f"Invalid value for {param_name}: {param_value}",
                        "suggestion": f"Use one of: {', '.join(prop['enum'])}"
                    }
            
            # Basic type checking
            expected_type = prop.get("type")
            if expected_type == "string" and not isinstance(param_value, str):
                return {
                    "valid": False,
                    "error": f"Parameter {param_name} must be a string",
                    "suggestion": f"Convert {param_name} to string"
                }
            elif expected_type == "boolean" and not isinstance(param_value, bool):
                return {
                    "valid": False,
                    "error": f"Parameter {param_name} must be a boolean",
                    "suggestion": f"Use true or false for {param_name}"
                }
            elif expected_type == "integer" and not isinstance(param_value, int):
                return {
                    "valid": False,
                    "error": f"Parameter {param_name} must be an integer",
                    "suggestion": f"Convert {param_name} to integer"
                }
        
        return {"valid": True}
    
    def _get_error_suggestion(self, action_name: str, error_type: str, error_msg: str) -> str:
        """Get helpful suggestion based on error type."""
        suggestions = {
            "timeout": "Try breaking the task into smaller steps or navigate to the correct screen first.",
            "validation_error": "Check the parameter values and types match the expected format.",
            "circuit_breaker_open": "This action has failed multiple times. Try a different approach or check if you're on the correct screen.",
            "unknown_action": "Use get_screen_state to see what actions are available."
        }
        
        base_suggestion = suggestions.get(error_type, "Try a different approach or check the current state with get_screen_state.")
        
        # Add action-specific suggestions
        if "review" in action_name and "Not on review screen" in error_msg:
            return "Navigate to review screen first using navigate_to_screen('review')."
        elif "compile" in action_name and "Not on compile screen" in error_msg:
            return "Navigate to compile screen first using navigate_to_screen('compile')."
        elif "draft" in action_name.lower():
            return "Make sure you have drafts available. Use list_available_drafts to check."
        
        return base_suggestion
    
    def reset_circuit_breaker(self, action_name: Optional[str] = None):
        """Reset circuit breaker for specific action or all actions."""
        if action_name:
            if action_name in self._circuit_open:
                del self._circuit_open[action_name]
            if action_name in self._failure_counts:
                self._failure_counts[action_name] = 0
        else:
            self._circuit_open.clear()
            self._failure_counts.clear()
            self._last_error.clear()
    
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
        """Export character pack.
        
        Note: The 'name' parameter is currently not used by the underlying export system.
        The export dialog will prompt for the character name if needed.
        """
        current_screen = self.main_window.stack.currentWidget()
        
        from .review import ReviewWidget
        if not isinstance(current_screen, ReviewWidget):
            return {"success": False, "message": "Not on review screen"}
        
        review_widget = current_screen
        
        # Trigger export (name parameter not currently supported by export_pack)
        if hasattr(review_widget, 'export_pack'):
            review_widget.export_pack()
            msg = "Export dialog opened"
            if name:
                msg += f" (Note: Suggested name '{name}' - please enter in dialog)"
            return {"success": True, "message": msg}
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
        from .template_manager import TemplateManagerScreen
        from .offspring import OffspringWidget
        from .similarity import SimilarityWidget
        
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
        
        elif isinstance(current_screen, TemplateManagerScreen):
            screen_info["screen_name"] = "template_manager"
            
            # Get selected template
            if hasattr(current_screen, 'selected_template'):
                screen_info["elements"]["selected_template"] = current_screen.selected_template
            
            # Get templates count
            if hasattr(current_screen, 'templates'):
                screen_info["elements"]["templates_count"] = len(current_screen.templates)
                if current_screen.templates:
                    screen_info["elements"]["templates_preview"] = current_screen.templates[:5]
            
            # Get template list selection
            if hasattr(current_screen, 'templates_list'):
                current_item = current_screen.templates_list.currentItem()
                if current_item:
                    screen_info["elements"]["selected_template_item"] = current_item.text()
        
        elif isinstance(current_screen, OffspringWidget):
            screen_info["screen_name"] = "offspring"
            
            # Get parent info
            if hasattr(current_screen, 'parent1_name'):
                screen_info["elements"]["parent1"] = current_screen.parent1_name or "[Not selected]"
            if hasattr(current_screen, 'parent2_name'):
                screen_info["elements"]["parent2"] = current_screen.parent2_name or "[Not selected]"
            
            # Check if parents are loaded
            has_parent1 = hasattr(current_screen, 'parent1_path') and current_screen.parent1_path
            has_parent2 = hasattr(current_screen, 'parent2_path') and current_screen.parent2_path
            screen_info["elements"]["both_parents_selected"] = has_parent1 and has_parent2
            
            # Check if offspring generation is running
            if hasattr(current_screen, 'generation_thread') and current_screen.generation_thread:
                screen_info["elements"]["is_generating"] = current_screen.generation_thread.isRunning()
            else:
                screen_info["elements"]["is_generating"] = False
        
        elif isinstance(current_screen, SimilarityWidget):
            screen_info["screen_name"] = "similarity"
            
            # Get search/comparison mode
            if hasattr(current_screen, 'comparison_mode'):
                screen_info["elements"]["comparison_mode"] = current_screen.comparison_mode  # type: ignore[attr-defined]
            
            # Get selected characters
            if hasattr(current_screen, 'selected_char1'):
                screen_info["elements"]["character1"] = current_screen.selected_char1 or "[Not selected]"  # type: ignore[attr-defined]
            if hasattr(current_screen, 'selected_char2'):
                screen_info["elements"]["character2"] = current_screen.selected_char2 or "[Not selected]"  # type: ignore[attr-defined]
            
            # Check if analysis is running
            if hasattr(current_screen, 'analysis_running'):
                screen_info["elements"]["is_analyzing"] = current_screen.analysis_running  # type: ignore[attr-defined]
            else:
                screen_info["elements"]["is_analyzing"] = False
            
            # Get results if available
            if hasattr(current_screen, 'results_text'):
                results = current_screen.results_text.toPlainText()  # type: ignore[attr-defined]
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
        
        # Get seed generator widget (attribute is named 'seed_gen' not 'seed_generator')
        seed_gen = None
        if hasattr(self.main_window, 'seed_gen'):
            seed_gen = self.main_window.seed_gen  # type: ignore[attr-defined]
        
        if not seed_gen:
            return {"success": False, "message": "Could not access seed generator widget"}
        
        # Set genre input and count
        if hasattr(seed_gen, 'genre_input'):
            seed_gen.genre_input.setPlainText(genres)
        else:
            return {"success": False, "message": "Seed generator missing genre_input field"}
        
        if hasattr(seed_gen, 'count_spin'):
            seed_gen.count_spin.setValue(count)
        else:
            return {"success": False, "message": "Seed generator missing count_spin field"}
        
        # Start generation
        if genres.strip():
            if hasattr(seed_gen, 'generate_seeds'):
                seed_gen.generate_seeds()
                return {
                    "success": True,
                    "message": f"Started generating seeds for genres: {genres[:50]}..."
                }
            else:
                return {"success": False, "message": "Seed generator missing generate_seeds method"}
        else:
            # Surprise mode
            if hasattr(seed_gen, 'surprise_me'):
                seed_gen.surprise_me()
                return {
                    "success": True,
                    "message": "Started generating surprise seeds"
                }
            else:
                return {"success": False, "message": "Seed generator missing surprise_me method"}
        
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
    
    def _get_current_draft_metadata(self) -> Dict[str, Any]:
        """Get metadata for the currently open draft in review mode."""
        current_screen = self.main_window.stack.currentWidget()
        
        from .review import ReviewWidget
        if not isinstance(current_screen, ReviewWidget):
            return {"success": False, "message": "Not on review screen"}
        
        review_widget = current_screen
        
        if not review_widget.draft_dir:
            return {"success": False, "message": "No draft currently open"}
        
        try:
            from ..metadata import DraftMetadata
            metadata = DraftMetadata.load(review_widget.draft_dir)
            
            if not metadata:
                return {
                    "success": True,
                    "message": "Draft open but no metadata found",
                    "draft_name": review_widget.draft_dir.name,
                    "draft_path": str(review_widget.draft_dir)
                }
            
            # Return full metadata
            return {
                "success": True,
                "message": "Retrieved draft metadata",
                "metadata": {
                    "draft_name": review_widget.draft_dir.name,
                    "draft_path": str(review_widget.draft_dir),
                    "character_name": metadata.character_name,
                    "seed": metadata.seed,
                    "mode": metadata.mode,
                    "model": metadata.model,
                    "template_name": metadata.template_name,
                    "tags": metadata.tags or [],
                    "genre": metadata.genre,
                    "favorite": metadata.favorite,
                    "created": metadata.created,
                    "modified": metadata.modified,
                    "parent_drafts": metadata.parent_drafts or [],
                    "offspring_type": metadata.offspring_type,
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to load metadata: {str(e)}",
                "draft_name": review_widget.draft_dir.name
            }
