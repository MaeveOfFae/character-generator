"""Conversation manager for persistent chat storage."""

from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict, Optional
import uuid


class Conversation:
    """Represents a single conversation."""
    
    def __init__(
        self,
        title: str = "New Chat",
        folder: str = "general",
        personality: str = "default",
        context: Optional[Dict] = None
    ):
        self.id = str(uuid.uuid4())
        self.title = title
        self.folder = folder
        self.personality = personality
        self.context = context or {}
        self.messages: List[Dict] = []
        self.created_at = datetime.now().isoformat()
        self.modified_at = self.created_at
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.modified_at = datetime.now().isoformat()
    
    def get_messages_for_llm(self) -> List[Dict]:
        """Get messages formatted for LLM API."""
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.messages
        ]
    
    def to_dict(self) -> Dict:
        """Convert conversation to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "folder": self.folder,
            "personality": self.personality,
            "context": self.context,
            "messages": self.messages,
            "created_at": self.created_at,
            "modified_at": self.modified_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Conversation':
        """Create conversation from dictionary."""
        conv = cls(
            title=data.get("title", "New Chat"),
            folder=data.get("folder", "general"),
            personality=data.get("personality", "default"),
            context=data.get("context", {})
        )
        conv.id = data.get("id", str(uuid.uuid4()))
        conv.messages = data.get("messages", [])
        conv.created_at = data.get("created_at", datetime.now().isoformat())
        conv.modified_at = data.get("modified_at", conv.created_at)
        return conv


class ConversationManager:
    """Manages conversation storage and retrieval."""
    
    DEFAULT_FOLDERS = ["general", "characters", "projects"]
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize conversation manager.
        
        Args:
            base_dir: Base directory for conversation storage.
                     Defaults to ~/.config/bpui/conversations
        """
        if base_dir is None:
            from ..config import Config
            config = Config()
            conv_dir = config.get("agent", {}).get("conversations_dir")
            if conv_dir:
                base_dir = Path(conv_dir).expanduser()
            else:
                base_dir = Path("~/.config/bpui/conversations").expanduser()
        
        self.base_dir = Path(base_dir)
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        for folder in self.DEFAULT_FOLDERS:
            (self.base_dir / folder).mkdir(parents=True, exist_ok=True)
    
    def _get_conversation_path(self, conversation_id: str, folder: str) -> Path:
        """Get file path for a conversation."""
        return self.base_dir / folder / f"{conversation_id}.json"
    
    def save_conversation(self, conversation: Conversation) -> bool:
        """Save conversation to disk."""
        try:
            path = self._get_conversation_path(conversation.id, conversation.folder)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(conversation.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return False
    
    def load_conversation(self, conversation_id: str, folder: str) -> Optional[Conversation]:
        """Load conversation from disk."""
        try:
            path = self._get_conversation_path(conversation_id, folder)
            if not path.exists():
                return None
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return Conversation.from_dict(data)
        except Exception as e:
            print(f"Error loading conversation: {e}")
            return None
    
    def list_conversations(self, folder: Optional[str] = None) -> List[Dict]:
        """List all conversations.
        
        Args:
            folder: If specified, only list conversations from this folder.
                   If None, list all conversations.
        
        Returns:
            List of conversation metadata dictionaries.
        """
        conversations = []
        
        folders_to_search = [folder] if folder else self.DEFAULT_FOLDERS
        
        for folder_name in folders_to_search:
            folder_path = self.base_dir / folder_name
            if not folder_path.exists():
                continue
            
            for file_path in folder_path.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    conversations.append({
                        "id": data.get("id"),
                        "title": data.get("title"),
                        "folder": folder_name,
                        "personality": data.get("personality"),
                        "created_at": data.get("created_at"),
                        "modified_at": data.get("modified_at"),
                        "message_count": len(data.get("messages", [])),
                        "path": file_path
                    })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    continue
        
        # Sort by modified_at descending
        conversations.sort(key=lambda x: x.get("modified_at", ""), reverse=True)
        
        return conversations
    
    def delete_conversation(self, conversation_id: str, folder: str) -> bool:
        """Delete a conversation."""
        try:
            path = self._get_conversation_path(conversation_id, folder)
            if path.exists():
                path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False
    
    def rename_conversation(self, conversation_id: str, folder: str, new_title: str) -> bool:
        """Rename a conversation."""
        try:
            conv = self.load_conversation(conversation_id, folder)
            if conv:
                conv.title = new_title
                conv.modified_at = datetime.now().isoformat()
                return self.save_conversation(conv)
            return False
        except Exception as e:
            print(f"Error renaming conversation: {e}")
            return False
    
    def move_conversation(
        self,
        conversation_id: str,
        old_folder: str,
        new_folder: str
    ) -> bool:
        """Move conversation to a different folder."""
        try:
            conv = self.load_conversation(conversation_id, old_folder)
            if not conv:
                return False
            
            # Save to new folder
            old_path = self._get_conversation_path(conversation_id, old_folder)
            conv.folder = new_folder
            self.save_conversation(conv)
            
            # Delete from old folder
            if old_path.exists():
                old_path.unlink()
            
            return True
        except Exception as e:
            print(f"Error moving conversation: {e}")
            return False
    
    def search_conversations(self, query: str) -> List[Dict]:
        """Search conversations by title and content."""
        results = []
        query_lower = query.lower()
        
        for conv_meta in self.list_conversations():
            # Search title
            if query_lower in conv_meta["title"].lower():
                results.append(conv_meta)
                continue
            
            # Load and search messages
            conv = self.load_conversation(conv_meta["id"], conv_meta["folder"])
            if conv:
                for msg in conv.messages:
                    if query_lower in msg["content"].lower():
                        results.append(conv_meta)
                        break
        
        return results
    
    def create_folder(self, folder_name: str) -> bool:
        """Create a new folder."""
        try:
            folder_path = self.base_dir / folder_name
            folder_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating folder: {e}")
            return False
    
    def list_folders(self) -> List[str]:
        """List all folders."""
        folders = []
        if self.base_dir.exists():
            for item in self.base_dir.iterdir():
                if item.is_dir():
                    folders.append(item.name)
        return sorted(folders)