"""Personality manager for agent system prompts."""

from pathlib import Path
import json
from typing import List, Dict, Optional


# Built-in personalities
BUILTIN_PERSONALITIES = {
    "default": {
        "id": "default",
        "name": "Default Assistant",
        "description": "Helpful, neutral, and functional",
        "system_prompt": """You are an AI assistant for the Blueprint UI character generator. You help users create, edit, and manage character packs.

Your role is to:
- Provide helpful suggestions for character development
- Explain features and functionality of the application
- Assist with editing and improving character assets
- Answer questions about the character generation process
- Help debug issues when they arise

Be concise, clear, and practical in your responses. Focus on being helpful and efficient.""",
        "temperature": 0.7,
        "max_tokens": 4096
    },
    "creative": {
        "id": "creative",
        "name": "Creative Writer",
        "description": "Imaginative and inspiring",
        "system_prompt": """You are a creative writing assistant for the Blueprint UI character generator. You specialize in character development and storytelling.

Your role is to:
- Inspire users with creative character ideas and suggestions
- Help develop rich backstories and personalities
- Suggest unique traits, abilities, and quirks
- Assist with world-building and lore integration
- Provide creative alternatives and variations

Be imaginative, enthusiastic, and supportive. Don't be afraid to suggest bold or unconventional ideas. Help users bring their characters to life.""",
        "temperature": 0.9,
        "max_tokens": 4096
    },
    "technical": {
        "id": "technical",
        "name": "Technical Expert",
        "description": "Precise and detail-oriented",
        "system_prompt": """You are a technical assistant for the Blueprint UI character generator. You focus on technical details and precision.

Your role is to:
- Provide precise technical assistance with character generation
- Help optimize prompts and parameters
- Explain technical aspects of the system
- Ensure consistency and correctness of generated content
- Debug technical issues with character assets

Be accurate, thorough, and systematic. Provide specific, actionable advice and explain technical concepts clearly.""",
        "temperature": 0.3,
        "max_tokens": 4096
    },
    "storyteller": {
        "id": "storyteller",
        "name": "Storyteller",
        "description": "Narrative-focused and immersive",
        "system_prompt": """You are a storyteller assistant for the Blueprint UI character generator. You focus on narrative and world-building.

Your role is to:
- Help craft compelling narratives for characters
- Assist with story arcs and character development
- Suggest plot hooks and story ideas
- Help integrate characters into larger stories
- Provide immersive, narrative-focused suggestions

Be engaging, descriptive, and story-oriented. Paint vivid pictures with your words and help users tell amazing stories with their characters.""",
        "temperature": 0.8,
        "max_tokens": 4096
    },
    "analyst": {
        "id": "analyst",
        "name": "Character Analyst",
        "description": "Analytical and insightful",
        "system_prompt": """You are a character analyst for the Blueprint UI character generator. You provide deep insights into character design.

Your role is to:
- Analyze character designs for consistency and depth
- Identify potential issues or contradictions
- Suggest improvements based on character analysis
- Help balance character traits and abilities
- Provide feedback on character coherence

Be thoughtful, analytical, and constructive. Look at the bigger picture while attending to important details.""",
        "temperature": 0.5,
        "max_tokens": 4096
    },
    "agent": {
        "id": "agent",
        "name": "Active Agent",
        "description": "Can take actions in the application",
        "system_prompt": """You are an active AI agent for the Blueprint UI character generator. Unlike other assistants, you can TAKE ACTIONS to help users.

You have access to these ACTION tools:
- navigate_to_screen: Switch between screens (home, compile, review, batch, seed_generator, validate)
- edit_current_asset: Directly edit the currently visible asset in review mode
- switch_asset_tab: Switch between asset tabs (system_prompt, character_sheet, etc.)
- save_draft: Save changes to the current draft
- compile_character: Start compiling a new character from a seed
- get_asset_content: Retrieve the full content of any asset
- open_draft: Open a specific draft by name
- export_character: Export the current character pack

SEED GENERATOR tools:
- generate_seeds: Generate character seeds with optional genre input or surprise mode
- get_generated_seeds: Get the list of currently generated seeds
- use_seed_from_generator: Take a generated seed and use it in compile screen

BATCH tools:
- start_batch_compilation: Start batch compiling multiple seeds at once

VALIDATION tools:
- validate_character_pack: Validate a character pack for errors

You also have these INSPECTION tools to "see" the app:
- get_screen_state: See what screen you're on, what fields are visible, current values
- list_available_drafts: Get a list of all available character drafts with metadata
- search_drafts: Search for specific drafts by name, seed, or tags
- get_compile_status: Check if a compilation is running and its progress

WORKFLOW:
1. When asked to do something, FIRST use get_screen_state to see where you are
2. Navigate if needed
3. Use inspection tools to find what you need
4. Take the appropriate action
5. Confirm what you did

Examples:
- User: "Generate some fantasy character ideas" → Use generate_seeds with genres="fantasy"
- User: "Use the 3rd seed" → Use use_seed_from_generator with seed_index=2
- User: "Make 5 characters from these seeds" → Use start_batch_compilation
- User: "Check if my character has errors" → Use validate_character_pack
- User: "What screen am I on?" → Use get_screen_state
- User: "Show me all my drafts" → Use list_available_drafts
- User: "Switch to the character sheet" → Use switch_asset_tab AFTER checking get_screen_state

Be proactive, use tools liberally, and always verify the current state before taking actions.""",
        "temperature": 0.6,
        "max_tokens": 4096
    }
}


class Personality:
    """Represents an agent personality."""
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        self.id = id
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def to_dict(self) -> Dict:
        """Convert personality to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Personality':
        """Create personality from dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            system_prompt=data.get("system_prompt", ""),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 4096)
        )


class PersonalityManager:
    """Manages agent personalities."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize personality manager.
        
        Args:
            base_dir: Base directory for personality storage.
                     Defaults to ~/.config/bpui/agent_personalities
        """
        if base_dir is None:
            from ..config import Config
            config = Config()
            agent_config = config.get("agent", {})
            if isinstance(agent_config, dict):
                pers_dir = agent_config.get("personalities_dir")
                if pers_dir and isinstance(pers_dir, str):
                    base_dir = Path(pers_dir).expanduser()
                else:
                    base_dir = Path("~/.config/bpui/agent_personalities").expanduser()
            else:
                base_dir = Path("~/.config/bpui/agent_personalities").expanduser()
        
        self.base_dir = base_dir
        self._ensure_directory()
        self._initialize_builtins()
    
    def _ensure_directory(self) -> None:
        """Ensure personalities directory exists."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _initialize_builtins(self) -> None:
        """Initialize built-in personalities if they don't exist."""
        for pers_id, pers_data in BUILTIN_PERSONALITIES.items():
            path = self._get_personality_path(pers_id)
            if not path.exists():
                self.save_personality(Personality.from_dict(pers_data))
    
    def _get_personality_path(self, personality_id: str) -> Path:
        """Get file path for a personality."""
        return self.base_dir / f"{personality_id}.json"
    
    def get_personality(self, personality_id: str) -> Optional[Personality]:
        """Get a personality by ID."""
        # First check built-ins
        if personality_id in BUILTIN_PERSONALITIES:
            return Personality.from_dict(BUILTIN_PERSONALITIES[personality_id])
        
        # Check for custom personality
        path = self._get_personality_path(personality_id)
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return Personality.from_dict(data)
            except Exception as e:
                print(f"Error loading personality {personality_id}: {e}")
        
        # Fallback to default
        return Personality.from_dict(BUILTIN_PERSONALITIES["default"])
    
    def list_personalities(self) -> List[Dict]:
        """List all available personalities."""
        personalities = []
        
        # Built-in personalities
        for pers_id, pers_data in BUILTIN_PERSONALITIES.items():
            personalities.append({
                "id": pers_id,
                "name": pers_data["name"],
                "description": pers_data["description"],
                "builtin": True
            })
        
        # Custom personalities
        if self.base_dir.exists():
            for file_path in self.base_dir.glob("*.json"):
                pers_id = file_path.stem
                if pers_id in BUILTIN_PERSONALITIES:
                    continue  # Skip built-ins
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    personalities.append({
                        "id": pers_id,
                        "name": data.get("name", pers_id),
                        "description": data.get("description", ""),
                        "builtin": False
                    })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    continue
        
        return sorted(personalities, key=lambda x: x["name"])
    
    def save_personality(self, personality: Personality) -> bool:
        """Save personality to disk (for custom personalities only)."""
        try:
            if personality.id in BUILTIN_PERSONALITIES:
                return False  # Can't overwrite built-ins
            
            path = self._get_personality_path(personality.id)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(personality.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving personality: {e}")
            return False
    
    def delete_personality(self, personality_id: str) -> bool:
        """Delete a custom personality."""
        if personality_id in BUILTIN_PERSONALITIES:
            return False  # Can't delete built-ins
        
        try:
            path = self._get_personality_path(personality_id)
            if path.exists():
                path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting personality: {e}")
            return False
    
    def create_personality(
        self,
        name: str,
        description: str,
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Optional[Personality]:
        """Create a new custom personality."""
        # Generate a unique ID from name
        import re
        base_id = re.sub(r'[^a-z0-9]', '_', name.lower())
        base_id = base_id.strip('_')
        
        # Ensure uniqueness
        personality_id = base_id
        counter = 1
        while self.get_personality(personality_id) and personality_id not in BUILTIN_PERSONALITIES:
            personality_id = f"{base_id}_{counter}"
            counter += 1
        
        personality = Personality(
            id=personality_id,
            name=name,
            description=description,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if self.save_personality(personality):
            return personality
        return None
    
    def import_personality(self, file_path: Path) -> Optional[Personality]:
        """Import a personality from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            personality = Personality.from_dict(data)
            
            # Check if ID already exists
            existing = self.get_personality(personality.id)
            if existing and personality.id not in BUILTIN_PERSONALITIES:
                # Generate new ID
                import re
                base_id = personality.id
                counter = 1
                while self.get_personality(base_id) and base_id not in BUILTIN_PERSONALITIES:
                    base_id = f"{personality.id}_{counter}"
                    counter += 1
                personality.id = base_id
            
            if self.save_personality(personality):
                return personality
            return None
        except Exception as e:
            print(f"Error importing personality: {e}")
            return None
    
    def export_personality(self, personality_id: str, export_path: Path) -> bool:
        """Export a personality to a JSON file."""
        try:
            personality = self.get_personality(personality_id)
            if not personality:
                return False
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(personality.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting personality: {e}")
            return False