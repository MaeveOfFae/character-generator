# Agent Chatbox Implementation

## Overview

A permanent, context-aware AI assistant chatbox has been added to the Blueprint UI application. The chatbox appears as a right sidebar and provides intelligent assistance based on the current screen and context.

## Features Implemented

### 1. **Permanent Sidebar**
- Located on the right side of the main window
- Resizable splitter (70% main content, 30% chatbox)
- Visible by default
- Three tabs: Chat, History, Settings

### 2. **Context Awareness**
The agent is aware of the current screen and its context:

**Screens with Context Providers:**
- **Home Screen**: Draft count, search query, selected draft
- **Compile Screen**: Seed input, template selection, output content
- **Review Screen**: Full character assets, metadata, current tab content
- Other screens: Basic screen name/title context

**Context Data Provided:**
- Screen name and title
- Screen-specific data (drafts, assets, metadata, etc.)
- User's current activity
- Related files and content

### 3. **Conversation Management**

**Storage:**
- Persistent JSON storage in `~/.config/bpui/conversations/`
- Organized into folders: `general`, `characters`, `projects`
- Searchable and sortable
- Exportable (JSON and TXT formats)

**Features:**
- Create new conversations
- Load previous conversations
- Rename conversations
- Move between folders
- Delete conversations
- Search by title and content
- Clear all conversations

### 4. **Personality System**

**Built-in Personalities:**
1. **Default Assistant** - Helpful, neutral, functional
2. **Creative Writer** - Imaginative and inspiring (temperature: 0.9)
3. **Technical Expert** - Precise and detail-oriented (temperature: 0.3)
4. **Storyteller** - Narrative-focused and immersive (temperature: 0.8)
5. **Character Analyst** - Analytical and insightful (temperature: 0.5)

**Custom Personalities:**
- Create custom personalities
- Edit custom personalities
- Set system prompts
- Configure temperature (0.0 - 2.0)
- Configure max tokens (256 - 32768)
- Persistent storage in `~/.config/bpui/agent_personalities/`

### 5. **LLM Integration**
- Streaming responses from LLM
- Supports all models via LiteLLM
- Context injection into prompts
- Message history management
- Error handling

### 6. **User Interface**

**Chat Tab:**
- Message history display
- Input field with send button
- Quick actions: Clear, Export, New Chat
- Status indicator
- Streaming response display

**History Tab:**
- Folder selection dropdown
- Search functionality
- Conversation list with metadata
- Actions: Rename, Move, Delete, Load

**Settings Tab:**
- Personality selection
- Edit/Create personalities
- Clear all conversations (danger zone)

## File Structure

### New Files Created

```
bpui/gui/
├── agent_chatbox.py          # Main chatbox widget with UI
├── agent_context.py          # Context management system
├── conversation_manager.py    # Conversation storage and retrieval
└── personality_manager.py    # Personality system

~/.config/bpui/
├── conversations/            # Conversation storage
│   ├── general/
│   ├── characters/
│   └── projects/
└── agent_personalities/     # Personality storage
    ├── default.json
    ├── creative.json
    ├── technical.json
    ├── storyteller.json
    └── analyst.json
```

### Modified Files

**bpui/gui/main_window.py:**
- Added QSplitter for layout
- Added AgentChatbox as sidebar
- Integrated AgentContextManager
- Added context updates for screen changes
- Registered context providers for screens

## Usage

### Starting a Conversation

1. Open Blueprint UI
2. The AI assistant chatbox is visible on the right
3. Type your question in the input field
4. Press Enter or click Send
5. Receive context-aware responses

### Switching Screens

When you switch screens:
- Context is automatically updated
- Current conversation context is saved
- Agent becomes aware of new screen data

### Managing Conversations

1. Click the "History" tab
2. Browse conversations by folder
3. Search for specific conversations
4. Load, rename, move, or delete conversations

### Customizing Personality

1. Click the "Settings" tab
2. Select from built-in personalities
3. Or click "Create New" to make a custom personality
4. Configure name, description, system prompt, temperature, and max tokens

### Exporting Conversations

1. In the Chat tab, click "Export"
2. Choose format: TXT or JSON
3. Save to desired location

## Context Examples

### Home Screen Context
```
Current Screen: Home Screen (home)
Context Data:
  - draft_count: 42
  - search_query: noir detective
  - selected_draft: noir_detective_20240112
```

### Review Screen Context
```
Current Screen: Character Review (review)
Context Data:
  - draft_id: 20240112_150000_abc123
  - seed: Noir detective with psychic abilities in 1940s Los Angeles...
  - mode: minimal
  - model: openai/gpt-4
  - tags: ['noir', 'detective', 'psychic']
  - genre: Mystery
  - favorite: true
  - current_asset: character_sheet
  - assets: {character_sheet: "...", system_prompt: "...", ...}
```

### Compile Screen Context
```
Current Screen: Character Compiler (compile)
Context Data:
  - seed: Fantasy warrior with magical sword
  - template: example_minimal
  - output: [Compilation output...]
```

## Configuration

Configuration is stored in the main config file:

```toml
[agent]
default_personality = "default"
conversations_dir = "~/.config/bpui/conversations"
personalities_dir = "~/.config/bpui/agent_personalities"
```

## Technical Details

### Context Flow

1. User navigates to a screen
2. MainWindow calls `show_*()` method
3. Method updates context via `context_manager.update_context()`
4. Context provider gathers screen-specific data
5. Agent accesses context when generating responses

### Message Flow

1. User types message and sends
2. Message added to conversation
3. Context gathered from current screen
4. Personality system prompt selected
5. Full prompt constructed: system + context + history
6. LLM generates streaming response
7. Chunks displayed in real-time
8. Conversation saved to disk

### Data Storage

**Conversation JSON:**
```json
{
  "id": "uuid",
  "title": "Conversation title",
  "folder": "general",
  "personality": "default",
  "context": {...},
  "messages": [
    {"role": "user", "content": "...", "timestamp": "..."},
    {"role": "assistant", "content": "...", "timestamp": "..."}
  ],
  "created_at": "ISO-8601",
  "modified_at": "ISO-8601"
}
```

**Personality JSON:**
```json
{
  "id": "personality_id",
  "name": "Personality Name",
  "description": "Description",
  "system_prompt": "...",
  "temperature": 0.7,
  "max_tokens": 4096
}
```

## Future Enhancements

Potential improvements:
1. Add more context providers for additional screens
2. Implement conversation sharing/export formats
3. Add keyboard shortcuts for chatbox
4. Support for multi-turn context across screens
5. Custom theme support for chatbox
6. Voice input support
7. Image/character preview in context
8. Conversation templates
9. Smart suggestions based on context
10. Integration with external tools/APIs

## Troubleshooting

### Chatbox not appearing
- Check main_window.py for splitter configuration
- Verify QSplitter sizes are set correctly

### Context not updating
- Ensure context provider is registered in main window
- Check screen change methods call `update_context()`

### LLM not responding
- Verify API key is configured
- Check model selection in settings
- Review error messages in status bar

### Conversations not saving
- Check write permissions for `~/.config/bpui/conversations/`
- Verify sufficient disk space
- Check for Python exceptions in console

## Credits

Implemented as part of Blueprint UI character generator.
Provides context-aware AI assistance for character creation and management.