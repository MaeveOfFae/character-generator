"""Agent chatbox widget for context-aware AI assistance."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QTabWidget, QListWidget, QListWidgetItem,
    QComboBox, QSplitter, QFrame, QMessageBox, QFileDialog,
    QDialog, QFormLayout, QDoubleSpinBox, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QTextCursor
from pathlib import Path
import asyncio
import html
import json
from typing import Optional, Dict, Any

from .conversation_manager import Conversation, ConversationManager
from .personality_manager import PersonalityManager, Personality
from .agent_context import AgentContextManager
from .agent_context import ReviewScreenContextProvider, CompileScreenContextProvider, HomeScreenContextProvider
from .agent_actions import AgentActionHandler, AGENT_TOOLS


class AgentWorker(QThread):
    """Worker thread for LLM communication."""
    
    chunk_received = Signal(str)
    finished = Signal(str)
    error = Signal(str)
    tool_call_started = Signal(str, dict)  # tool_name, arguments
    tool_call_completed = Signal(str, bool, str)  # tool_name, success, result
    
    def __init__(self, config, personality: Personality, messages: list, context: Optional[dict] = None, action_handler: Optional[Any] = None):
        super().__init__()
        self.config = config
        self.personality = personality
        self.messages = messages
        self.context = context or {}
        self.action_handler = action_handler
        # Enable tools only for agent personality
        self.use_tools = (personality.id == "agent" and action_handler is not None)
    
    def run(self):
        """Run LLM generation."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._generate())
            loop.close()
            
            if result:
                self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
    
    async def _generate(self):
        """Perform LLM generation with optional tool calling and robust error handling."""
        from ..llm.litellm_engine import LiteLLMEngine
        
        # Build full messages list
        full_messages = [
            {"role": "system", "content": self.personality.system_prompt}
        ]
        
        # Add context if available
        if self.context:
            context_str = self._format_context()
            full_messages.append({
                "role": "system",
                "content": f"Context Information:\n{context_str}\n\nKeep this context in mind when responding."
            })
        
        # Add conversation history
        full_messages.extend(self.messages)
        
        # Create engine
        try:
            engine = LiteLLMEngine(
                model=self.config.model,
                api_key=self.config.get_api_key_for_model(self.config.model),
                base_url=self.config.api_base_url,
                api_version=self.config.api_version,
                temperature=self.personality.temperature,
                max_tokens=self.personality.max_tokens
            )
        except Exception as e:
            raise Exception(f"Failed to create LLM engine: {str(e)}")
        
        # Loop for tool calling
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        final_response = ""
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                # Generate with optional tools
                if self.use_tools and self.action_handler:
                    # Use non-streaming for tool calls
                    import litellm
                    
                    try:
                        response = await litellm.acompletion(
                            model=self.config.model,
                            messages=full_messages,
                            temperature=self.personality.temperature,
                            max_tokens=self.personality.max_tokens,
                            api_key=self.config.get_api_key_for_model(self.config.model),
                            tools=AGENT_TOOLS,
                            tool_choice="auto",
                            stream=False,
                            timeout=60.0,  # 60 second timeout for LLM calls
                            **engine.extra_params
                        )
                    except Exception as llm_error:
                        # LLM API error - report to user and try to recover
                        error_msg = f"LLM API error: {str(llm_error)}"
                        self.chunk_received.emit(f"\n[Error: {error_msg}]\n")
                        
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            raise Exception(f"Too many consecutive LLM errors: {error_msg}")
                        
                        # Add error to conversation for recovery
                        full_messages.append({
                            "role": "system",
                            "content": f"Previous request failed with error: {error_msg}. Please try again with a simpler approach."
                        })
                        continue
                    
                    message = response.choices[0].message  # type: ignore[attr-defined]
                    
                    # Reset error counter on success
                    consecutive_errors = 0
                    
                    # Check for tool calls
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        # Execute tool calls
                        tool_results = []
                        all_tools_succeeded = True
                        
                        for tool_call in message.tool_calls:
                            tool_name = "unknown"  # default
                            try:
                                tool_name = tool_call.function.name
                                
                                # Parse arguments with error handling
                                try:
                                    tool_args = json.loads(tool_call.function.arguments)
                                except json.JSONDecodeError as e:
                                    # JSON parsing failed
                                    result = {
                                        "success": False,
                                        "message": f"Invalid JSON arguments: {str(e)}",
                                        "error_type": "json_parse_error",
                                        "suggestion": "Ensure arguments are valid JSON format"
                                    }
                                    tool_args = {}
                                    all_tools_succeeded = False
                                else:
                                    # Emit tool call started
                                    self.tool_call_started.emit(tool_name, tool_args)
                                    
                                    # Execute action with error handling
                                    try:
                                        result = self.action_handler.execute_action(tool_name, tool_args)
                                        if not result.get("success", False):
                                            all_tools_succeeded = False
                                    except Exception as action_error:
                                        # Catch any unexpected errors from action handler
                                        result = {
                                            "success": False,
                                            "message": f"Unexpected error: {str(action_error)}",
                                            "error_type": "unexpected_error",
                                            "suggestion": "Check if you're on the correct screen or try a different approach"
                                        }
                                        all_tools_succeeded = False
                                
                                # Emit tool call completed
                                self.tool_call_completed.emit(
                                    tool_name,
                                    result.get("success", False),
                                    result.get("message", "")
                                )
                                
                                # Format result with helpful information for LLM
                                result_content = json.dumps(result)
                                
                                # Add tool result to messages
                                tool_results.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": tool_name,
                                    "content": result_content
                                })
                                
                            except Exception as tool_error:
                                # Unexpected error in tool call handling
                                error_result = {
                                    "success": False,
                                    "message": f"Tool call error: {str(tool_error)}",
                                    "error_type": "tool_call_error"
                                }
                                tool_results.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": tool_name,
                                    "content": json.dumps(error_result)
                                })
                                all_tools_succeeded = False
                        
                        # Add assistant message with tool calls
                        tool_calls_list = []
                        for tc in message.tool_calls:
                            tool_calls_list.append({
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            })
                        
                        full_messages.append({
                            "role": "assistant",
                            "content": message.content or "",
                            "tool_calls": tool_calls_list  # type: ignore[typeddict-item]
                        })
                        
                        # Add tool results
                        full_messages.extend(tool_results)  # type: ignore[arg-type]
                        
                        # If tools failed, give LLM guidance
                        if not all_tools_succeeded:
                            full_messages.append({
                                "role": "system",
                                "content": "Some tools failed. Review the error messages and try a different approach. You can use get_screen_state to check the current state before taking actions."
                            })
                        
                        # Continue loop to get final response
                        continue
                    else:
                        # No tool calls, we have final response
                        final_response = message.content or ""
                        if final_response:
                            self.chunk_received.emit(final_response)
                        break
                else:
                    # Regular streaming without tools
                    try:
                        async for chunk in engine.generate_chat_stream(full_messages):
                            final_response += chunk
                            self.chunk_received.emit(chunk)
                    except Exception as stream_error:
                        raise Exception(f"Streaming error: {str(stream_error)}")
                    break
                    
            except Exception as iter_error:
                # Iteration-level error
                consecutive_errors += 1
                error_msg = f"Iteration {iteration} failed: {str(iter_error)}"
                self.chunk_received.emit(f"\n[Error: {error_msg}]\n")
                
                if consecutive_errors >= max_consecutive_errors:
                    raise Exception(f"Too many consecutive errors. Last: {error_msg}")
                
                # Try to recover
                full_messages.append({
                    "role": "system",
                    "content": f"Error occurred: {error_msg}. Please simplify your approach."
                })
                continue
        
        # Check if we hit max iterations
        if iteration >= max_iterations and not final_response:
            self.chunk_received.emit(f"\n[Warning: Reached maximum tool calling iterations ({max_iterations}). Requesting final response...]\n")
            # Try one more time without tools to get a response
            try:
                async for chunk in engine.generate_chat_stream(full_messages):
                    final_response += chunk
                    self.chunk_received.emit(chunk)
            except Exception as e:
                final_response = f"I encountered too many tool calls and couldn't complete the task. Error: {str(e)}"
                self.chunk_received.emit(final_response)
        
        return final_response.strip()
    
    def _format_context(self) -> str:
        """Format context for inclusion in prompt."""
        parts = []
        for key, value in self.context.items():
            if isinstance(value, str):
                parts.append(f"{key}: {value[:500]}{'...' if len(value) > 500 else ''}")
            elif isinstance(value, dict):
                parts.append(f"{key}: {len(value)} items")
            elif isinstance(value, list):
                parts.append(f"{key}: {len(value)} items")
            else:
                parts.append(f"{key}: {str(value)}")
        return "\n".join(parts)


class PersonalityEditorDialog(QDialog):
    """Dialog for editing or creating personalities."""
    
    def __init__(self, parent, personality_manager: PersonalityManager, personality: Optional[Personality] = None):
        super().__init__(parent)
        self.personality_manager = personality_manager
        self.personality = personality
        self.saved_personality: Optional[Personality] = None
        
        self.setWindowTitle("Edit Personality" if personality else "New Personality")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        
        # Form
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        if personality:
            self.name_input.setText(personality.name)
        form.addRow("Name:", self.name_input)
        
        self.description_input = QLineEdit()
        if personality:
            self.description_input.setText(personality.description)
        form.addRow("Description:", self.description_input)
        
        self.system_prompt_input = QTextEdit()
        self.system_prompt_input.setMinimumHeight(200)
        if personality:
            self.system_prompt_input.setPlainText(personality.system_prompt)
        else:
            # Default template
            self.system_prompt_input.setPlainText(
                "You are an AI assistant for the Blueprint UI character generator.\n\n"
                "Your role is to:\n"
                "- [Add specific role 1]\n"
                "- [Add specific role 2]\n"
                "- [Add specific role 3]\n\n"
                "[Add any additional instructions]"
            )
        form.addRow("System Prompt:", self.system_prompt_input)
        
        self.temperature_input = QDoubleSpinBox()
        self.temperature_input.setRange(0.0, 2.0)
        self.temperature_input.setSingleStep(0.1)
        self.temperature_input.setValue(personality.temperature if personality else 0.7)
        form.addRow("Temperature:", self.temperature_input)
        
        self.max_tokens_input = QSpinBox()
        self.max_tokens_input.setRange(256, 32768)
        self.max_tokens_input.setValue(personality.max_tokens if personality else 4096)
        form.addRow("Max Tokens:", self.max_tokens_input)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_personality)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def save_personality(self):
        """Save personality."""
        name = self.name_input.text().strip()
        description = self.description_input.text().strip()
        system_prompt = self.system_prompt_input.toPlainText().strip()
        temperature = self.temperature_input.value()
        max_tokens = self.max_tokens_input.value()
        
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a name")
            return
        
        if not system_prompt:
            QMessageBox.warning(self, "Error", "Please enter a system prompt")
            return
        
        if self.personality:
            # Update existing
            self.personality.name = name
            self.personality.description = description
            self.personality.system_prompt = system_prompt
            self.personality.temperature = temperature
            self.personality.max_tokens = max_tokens
            self.saved_personality = self.personality
        else:
            # Create new
            new_personality = self.personality_manager.create_personality(
                name=name,
                description=description,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if not new_personality:
                QMessageBox.critical(self, "Error", "Failed to create personality")
                return
            
            self.saved_personality = new_personality
        
        self.accept()


class AgentChatbox(QWidget):
    """Permanent sidebar chatbox for AI assistance."""
    
    def __init__(self, config, main_window):
        super().__init__()
        self.config = config
        self.main_window = main_window
        
        # Initialize managers
        self.conversation_manager = ConversationManager()
        self.personality_manager = PersonalityManager()
        # Use main window's context manager instead of creating our own
        self.context_manager = main_window.context_manager
        
        # Action handler for agent capabilities
        self.action_handler = AgentActionHandler(main_window)
        
        # State
        self.current_conversation: Optional[Conversation] = None
        self.current_personality_id = config.get("agent", {}).get("default_personality", "default")
        self.worker: Optional[AgentWorker] = None
        self.is_generating = False
        
        self.setup_ui()
        self.setup_connections()
        self.load_personalities()
        self.new_conversation()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Header
        header = QLabel("🤖 AI Assistant")
        header_font = QFont("Arial", 12, QFont.Weight.Bold)
        header.setFont(header_font)
        header.setStyleSheet("padding: 5px;")
        layout.addWidget(header)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        layout.addWidget(self.tabs)
        
        # Create tabs
        self.create_chat_tab()
        self.create_conversations_tab()
        self.create_settings_tab()
        
        # Current personality indicator
        self.personality_label = QLabel()
        self.update_personality_label()
        self.personality_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.personality_label)
    
    def create_chat_tab(self):
        """Create the chat tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Quick actions
        action_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.clicked.connect(self.clear_chat)
        action_layout.addWidget(self.clear_btn)
        
        self.export_btn = QPushButton("📤 Export")
        self.export_btn.clicked.connect(self.export_conversation)
        action_layout.addWidget(self.export_btn)
        
        self.new_chat_btn = QPushButton("➕ New Chat")
        self.new_chat_btn.clicked.connect(self.new_conversation)
        action_layout.addWidget(self.new_chat_btn)
        
        layout.addLayout(action_layout)
        
        # Chat history
        chat_label = QLabel("Conversation:")
        layout.addWidget(chat_label)
        
        # Context indicator
        self.context_indicator = QLabel()
        self.context_indicator.setStyleSheet("color: #888; font-size: 10px; font-style: italic; padding: 3px 5px;")
        self.context_indicator.setText("Context: Home Screen")
        layout.addWidget(self.context_indicator)
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                border: 1px solid #333;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.chat_history, 1)
        
        # Input area
        input_label = QLabel("Message:")
        layout.addWidget(input_label)
        
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Ask the AI assistant...")
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        
        layout.addLayout(input_layout)
        
        # Status
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.status_label)
        
        self.tabs.addTab(widget, "Chat")
    
    def create_conversations_tab(self):
        """Create the conversations browser tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Folder selection
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Folder:"))
        
        self.folder_combo = QComboBox()
        self.folder_combo.currentTextChanged.connect(self.load_conversations_list)
        folder_layout.addWidget(self.folder_combo)
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedWidth(35)
        refresh_btn.clicked.connect(self.refresh_folders)
        folder_layout.addWidget(refresh_btn)
        
        layout.addLayout(folder_layout)
        
        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search conversations...")
        self.search_input.textChanged.connect(self.search_conversations)
        search_layout.addWidget(self.search_input)
        
        layout.addLayout(search_layout)
        
        # Conversation list
        self.conversations_list = QListWidget()
        self.conversations_list.itemDoubleClicked.connect(self.load_selected_conversation)
        layout.addWidget(self.conversations_list, 1)
        
        # Conversation actions
        conv_actions = QHBoxLayout()
        
        self.rename_btn = QPushButton("Rename")
        self.rename_btn.clicked.connect(self.rename_conversation)
        self.rename_btn.setEnabled(False)
        conv_actions.addWidget(self.rename_btn)
        
        self.move_btn = QPushButton("Move")
        self.move_btn.clicked.connect(self.move_conversation)
        self.move_btn.setEnabled(False)
        conv_actions.addWidget(self.move_btn)
        
        self.delete_conv_btn = QPushButton("Delete")
        self.delete_conv_btn.clicked.connect(self.delete_conversation)
        self.delete_conv_btn.setEnabled(False)
        conv_actions.addWidget(self.delete_conv_btn)
        
        conv_actions.addStretch()
        
        self.load_conv_btn = QPushButton("Load")
        self.load_conv_btn.clicked.connect(self.load_selected_conversation)
        self.load_conv_btn.setEnabled(False)
        conv_actions.addWidget(self.load_conv_btn)
        
        layout.addLayout(conv_actions)
        
        self.tabs.addTab(widget, "History")
    
    def create_settings_tab(self):
        """Create the settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Personality selection
        pers_label = QLabel("<b>Personality</b>")
        layout.addWidget(pers_label)
        
        pers_form = QFormLayout()
        
        self.personality_combo = QComboBox()
        self.personality_combo.currentIndexChanged.connect(self.change_personality)
        pers_form.addRow("Current:", self.personality_combo)
        
        edit_pers_btn = QPushButton("Edit Selected")
        edit_pers_btn.clicked.connect(self.edit_personality)
        pers_form.addRow("", edit_pers_btn)
        
        new_pers_btn = QPushButton("Create New")
        new_pers_btn.clicked.connect(self.create_personality)
        pers_form.addRow("", new_pers_btn)
        
        layout.addLayout(pers_form)
        
        layout.addStretch()
        
        # Clear all
        clear_frame = QFrame()
        clear_frame.setFrameShape(QFrame.Shape.StyledPanel)
        clear_layout = QVBoxLayout(clear_frame)
        
        clear_label = QLabel("<b>Danger Zone</b>")
        clear_label.setStyleSheet("color: #f44;")
        clear_layout.addWidget(clear_label)
        
        clear_all_btn = QPushButton("🗑️ Clear All Conversations")
        clear_all_btn.setStyleSheet("background-color: #522;")
        clear_all_btn.clicked.connect(self.clear_all_conversations)
        clear_layout.addWidget(clear_all_btn)
        
        layout.addWidget(clear_frame)
        
        self.tabs.addTab(widget, "Settings")
    
    def setup_connections(self):
        """Setup signal connections."""
        self.conversations_list.itemSelectionChanged.connect(self.on_conversation_selected)
    
    def load_personalities(self):
        """Load personalities into combo box."""
        self.personality_combo.clear()
        
        personalities = self.personality_manager.list_personalities()
        for pers in personalities:
            self.personality_combo.addItem(
                f"{pers['name']} ({pers['description']})",
                pers['id']
            )
        
        # Select current personality
        index = self.personality_combo.findData(self.current_personality_id)
        if index >= 0:
            self.personality_combo.setCurrentIndex(index)
    
    def update_personality_label(self):
        """Update personality indicator label."""
        personality = self.personality_manager.get_personality(self.current_personality_id)
        if personality:
            self.personality_label.setText(f"Personality: {personality.name}")
        else:
            self.personality_label.setText("Personality: Default")
    
    def change_personality(self, index: int):
        """Change current personality."""
        personality_id = self.personality_combo.itemData(index)
        if personality_id:
            self.current_personality_id = personality_id
            self.update_personality_label()
            
            # Update config
            self.config.set("agent", {"default_personality": personality_id})
            self.config.save()
    
    def edit_personality(self):
        """Edit selected personality."""
        index = self.personality_combo.currentIndex()
        personality_id = self.personality_combo.itemData(index)
        
        if not personality_id or personality_id in ["default", "creative", "technical", "storyteller", "analyst"]:
            QMessageBox.warning(self, "Error", "Cannot edit built-in personalities")
            return
        
        personality = self.personality_manager.get_personality(personality_id)
        if not personality:
            return
        
        dialog = PersonalityEditorDialog(self, self.personality_manager, personality)
        if dialog.exec() and dialog.saved_personality:
            self.personality_manager.save_personality(dialog.saved_personality)
            self.load_personalities()
    
    def create_personality(self):
        """Create new personality."""
        dialog = PersonalityEditorDialog(self, self.personality_manager)
        if dialog.exec():
            self.load_personalities()
            # Select new personality
            if dialog.saved_personality:
                index = self.personality_combo.findData(dialog.saved_personality.id)
                if index >= 0:
                    self.personality_combo.setCurrentIndex(index)
    
    def refresh_folders(self):
        """Refresh folder list."""
        self.folder_combo.clear()
        folders = self.conversation_manager.list_folders()
        self.folder_combo.addItems(folders)
    
    def load_conversations_list(self, folder: Optional[str] = None):
        """Load conversations list."""
        if folder is None:
            folder = self.folder_combo.currentText()
        
        self.conversations_list.clear()
        
        conversations = self.conversation_manager.list_conversations(folder)
        
        for conv in conversations:
            item = QListWidgetItem(f"{conv['title']}")
            item.setData(Qt.ItemDataRole.UserRole, conv)
            self.conversations_list.addItem(item)
        
        self.on_conversation_selected()
    
    def search_conversations(self, query: str):
        """Search conversations."""
        if not query:
            self.load_conversations_list()
            return
        
        self.conversations_list.clear()
        
        results = self.conversation_manager.search_conversations(query)
        
        for conv in results:
            item = QListWidgetItem(f"{conv['title']} ({conv['folder']})")
            item.setData(Qt.ItemDataRole.UserRole, conv)
            self.conversations_list.addItem(item)
        
        self.on_conversation_selected()
    
    def on_conversation_selected(self):
        """Handle conversation selection change."""
        has_selection = self.conversations_list.currentItem() is not None
        self.rename_btn.setEnabled(has_selection)
        self.move_btn.setEnabled(has_selection)
        self.delete_conv_btn.setEnabled(has_selection)
        self.load_conv_btn.setEnabled(has_selection)
    
    def load_selected_conversation(self):
        """Load selected conversation."""
        current = self.conversations_list.currentItem()
        if not current:
            return
        
        conv_data = current.data(Qt.ItemDataRole.UserRole)
        if not conv_data:
            return
        
        conversation = self.conversation_manager.load_conversation(
            conv_data['id'],
            conv_data['folder']
        )
        
        if conversation:
            self.current_conversation = conversation
            self.render_chat_history()
            self.tabs.setCurrentIndex(0)  # Switch to chat tab
    
    def rename_conversation(self):
        """Rename selected conversation."""
        current = self.conversations_list.currentItem()
        if not current:
            return
        
        conv_data = current.data(Qt.ItemDataRole.UserRole)
        if not conv_data:
            return
        
        from PySide6.QtWidgets import QInputDialog
        new_title, ok = QInputDialog.getText(
            self,
            "Rename Conversation",
            "New title:",
            text=conv_data['title']
        )
        
        if ok and new_title:
            self.conversation_manager.rename_conversation(
                conv_data['id'],
                conv_data['folder'],
                new_title
            )
            self.load_conversations_list()
    
    def move_conversation(self):
        """Move conversation to different folder."""
        current = self.conversations_list.currentItem()
        if not current:
            return
        
        conv_data = current.data(Qt.ItemDataRole.UserRole)
        if not conv_data:
            return
        
        # Get target folder
        folders = self.conversation_manager.list_folders()
        
        from PySide6.QtWidgets import QInputDialog, QComboBox
        combo = QComboBox()
        combo.addItems(folders)
        combo.setCurrentText(conv_data['folder'])
        
        from PySide6.QtWidgets import QDialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Folder")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Move to folder:"))
        layout.addWidget(combo)
        
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        move_btn = QPushButton("Move")
        move_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(move_btn)
        
        layout.addLayout(btn_layout)
        
        if dialog.exec():
            target_folder = combo.currentText()
            if target_folder != conv_data['folder']:
                self.conversation_manager.move_conversation(
                    conv_data['id'],
                    conv_data['folder'],
                    target_folder
                )
                self.load_conversations_list()
    
    def delete_conversation(self):
        """Delete selected conversation."""
        current = self.conversations_list.currentItem()
        if not current:
            return
        
        conv_data = current.data(Qt.ItemDataRole.UserRole)
        if not conv_data:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete conversation '{conv_data['title']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.conversation_manager.delete_conversation(
                conv_data['id'],
                conv_data['folder']
            )
            self.load_conversations_list()
    
    def new_conversation(self):
        """Start a new conversation."""
        self.current_conversation = Conversation(
            title="New Chat",
            folder=self.folder_combo.currentText() if self.folder_combo.count() > 0 else "general",
            personality=self.current_personality_id
        )
        
        # Save initial context
        context = self.context_manager.get_current_context()
        if context:
            self.current_conversation.context = context.to_dict()
        
        self.render_chat_history()
        self.chat_history.clear()
        self.status_label.setText("New conversation started")
    
    def clear_chat(self):
        """Clear current chat display."""
        if self.current_conversation:
            self.current_conversation.messages = []
            self.render_chat_history()
    
    def render_chat_history(self):
        """Render chat history to display."""
        self.chat_history.clear()
        
        if not self.current_conversation:
            return
        
        cursor = QTextCursor(self.chat_history.document())
        
        for msg in self.current_conversation.messages:
            role = msg['role']
            content = msg['content']
            
            # Format the content properly
            formatted_content = self._format_message_content(content)
            
            if role == 'user':
                cursor.insertHtml(
                    f'<div style="margin: 15px 0; padding: 10px; background-color: #1e3a5f; border-left: 3px solid #6a9;">'
                    f'<b style="color: #6a9;">You:</b><br/>'
                    f'<span style="color: #e8e8e8;">{formatted_content}</span>'
                    f'</div>'
                )
            else:
                cursor.insertHtml(
                    f'<div style="margin: 15px 0; padding: 10px; background-color: #1a2a1a; border-left: 3px solid #4a4;">'
                    f'<b style="color: #4a4;">Assistant:</b><br/>'
                    f'<span style="color: #e0e0e0;">{formatted_content}</span>'
                    f'</div>'
                )
        
        self.chat_history.verticalScrollBar().setValue(
            self.chat_history.verticalScrollBar().maximum()
        )
    
    def _format_message_content(self, content: str) -> str:
        """Format message content with proper HTML escaping and line breaks."""
        # Escape HTML
        escaped = html.escape(content)
        
        # Convert line breaks to <br/>
        formatted = escaped.replace('\n', '<br/>')
        
        # Handle code blocks (simple version)
        # Look for ```triple backticks``` and format them
        import re
        formatted = re.sub(
            r'```(.*?)```',
            r'<pre style="background-color: #0a0a0a; padding: 8px; margin: 8px 0; border-radius: 4px; overflow-x: auto;"><code>\1</code></pre>',
            formatted,
            flags=re.DOTALL
        )
        
        # Handle inline code `backticks`
        formatted = re.sub(
            r'`([^`]+)`',
            r'<code style="background-color: #2a2a2a; padding: 2px 4px; border-radius: 2px; font-family: monospace;">\1</code>',
            formatted
        )
        
        return formatted
    
    def update_context_indicator(self, screen_title: str):
        """Update the context indicator label."""
        self.context_indicator.setText(f"📍 Context: {screen_title}")
    
    def send_message(self):
        """Send a message to the agent."""
        if self.is_generating:
            return
        
        if not self.current_conversation:
            return
        
        message = self.message_input.text().strip()
        if not message:
            return
        
        # Add user message
        self.current_conversation.add_message("user", message)
        self.render_chat_history()
        self.message_input.clear()
        
        # Update title if first message
        if len(self.current_conversation.messages) == 1:
            self.current_conversation.title = message[:50] + "..." if len(message) > 50 else message
        
        # Save conversation
        self.conversation_manager.save_conversation(self.current_conversation)
        
        # Generate response
        self.generate_response(message)
    
    def generate_response(self, user_message: str):
        """Generate AI response."""
        self.is_generating = True
        self.send_btn.setEnabled(False)
        self.status_label.setText("Generating response...")
        
        # Get context and update indicator
        context_data = {}
        context = self.context_manager.get_current_context()
        if context:
            context_data = context.data
            self.update_context_indicator(context.screen_title)
        else:
            self.update_context_indicator("No Context")
        
        # Prepare messages (last 10 messages to stay within context limits)
        messages = []
        if self.current_conversation:
            messages = self.current_conversation.get_messages_for_llm()[-10:]
        
        # Get personality
        personality = self.personality_manager.get_personality(self.current_personality_id)
        if not personality:
            # Fallback to default
            personality = self.personality_manager.get_personality("default")
        
        # Don't start worker if no personality
        if not personality:
            self.is_generating = False
            self.send_btn.setEnabled(True)
            self.status_label.setText("Error: No personality available")
            return
        
        # Start worker
        self.worker = AgentWorker(
            self.config,
            personality,
            messages,
            context_data,
            self.action_handler
        )
        self.worker.chunk_received.connect(self.on_chunk_received)
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.error.connect(self.on_generation_error)
        self.worker.tool_call_started.connect(self.on_tool_call_started)
        self.worker.tool_call_completed.connect(self.on_tool_call_completed)
        self.worker.start()
    
    def on_tool_call_started(self, tool_name: str, arguments: Dict[str, Any]):
        """Handle tool call started."""
        # Add system message to chat showing tool call
        if self.current_conversation:
            args_str = json.dumps(arguments, indent=2)
            self.current_conversation.add_message(
                "assistant",
                f"🔧 Calling tool: **{tool_name}**\n```json\n{args_str}\n```"
            )
            self.render_chat_history()
    
    def on_tool_call_completed(self, tool_name: str, success: bool, message: str):
        """Handle tool call completed."""
        # Add system message to chat showing result
        if self.current_conversation:
            emoji = "✅" if success else "❌"
            self.current_conversation.add_message(
                "assistant",
                f"{emoji} Tool result: {message}"
            )
            self.render_chat_history()
    
    def on_chunk_received(self, chunk: str):
        """Handle received chunk from LLM."""
        if not self.current_conversation:
            return
        
        if len(self.current_conversation.messages) == 0 or \
           self.current_conversation.messages[-1]['role'] != 'assistant':
            # First chunk of new assistant message
            self.current_conversation.add_message("assistant", "")
        
        # Append text to message
        self.current_conversation.messages[-1]['content'] += chunk
        
        # Re-render to show updated content with proper formatting
        self.render_chat_history()
    
    def on_generation_finished(self, content: str):
        """Handle generation completion."""
        self.is_generating = False
        self.send_btn.setEnabled(True)
        self.status_label.setText("Ready")
        
        # Final render with complete formatting
        self.render_chat_history()
        
        # Save conversation
        if self.current_conversation:
            self.conversation_manager.save_conversation(self.current_conversation)
        
        # Refresh list if on history tab
        if self.tabs.currentIndex() == 1:
            self.load_conversations_list()
    
    def on_generation_error(self, error: str):
        """Handle generation error."""
        self.is_generating = False
        self.send_btn.setEnabled(True)
        self.status_label.setText(f"Error: {error}")
        
        # Show error in chat
        cursor = QTextCursor(self.chat_history.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(f'<p style="color: #f44; margin: 10px 0;"><b>Error:</b> {error}</p>')
        self.chat_history.verticalScrollBar().setValue(
            self.chat_history.verticalScrollBar().maximum()
        )
    
    def export_conversation(self):
        """Export current conversation."""
        if not self.current_conversation:
            return
        
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Conversation",
            f"{self.current_conversation.title}.txt",
            "Text Files (*.txt);;JSON Files (*.json)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    # Export as JSON
                    import json
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(self.current_conversation.to_dict(), f, indent=2)
                else:
                    # Export as text
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"Title: {self.current_conversation.title}\n")
                        f.write(f"Folder: {self.current_conversation.folder}\n")
                        f.write(f"Personality: {self.current_conversation.personality}\n")
                        f.write(f"Created: {self.current_conversation.created_at}\n\n")
                        f.write("=" * 50 + "\n\n")
                        
                        for msg in self.current_conversation.messages:
                            role = "You" if msg['role'] == 'user' else "Assistant"
                            f.write(f"{role}:\n{msg['content']}\n\n")
                
                self.status_label.setText(f"Exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export: {e}")
    
    def clear_all_conversations(self):
        """Clear all conversations."""
        reply = QMessageBox.question(
            self,
            "Confirm Clear All",
            "This will delete ALL conversations. Are you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Delete all conversation files
            import shutil
            from pathlib import Path
            
            base_dir = self.conversation_manager.base_dir
            if base_dir.exists():
                shutil.rmtree(base_dir)
            
            # Reinitialize
            self.conversation_manager = ConversationManager()
            self.new_conversation()
            self.load_conversations_list()
            self.refresh_folders()
            
            self.status_label.setText("All conversations cleared")