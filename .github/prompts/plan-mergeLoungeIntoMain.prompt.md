# Plan: Merge Lounge Chat into Main AkshoAI Without Editing Main

## Executive Summary

Integrate the fully-featured Lounge chat system (70% complete, 25+ services, Sonarcore v4.0, multi-provider AI) into the main AkshoAI application by isolating Lounge code in a dedicated feature module with database/auth adapters—avoiding modifications to existing main application code.

---

## Current State Analysis

### Main Application (akshoai/)
- **Version:** v3.36.2 (Production)
- **Tech Stack:** Next.js 16.1.4, React 19.2.3, TypeScript, Tailwind CSS
- **Database:** Neon PostgreSQL + Drizzle ORM 0.45.1
- **Auth:** Better-Auth 1.4.9 + SubscribeStar OAuth
- **Features:** Character Creator (Hangar), Image Generation (Atelier), Gamification System
- **Lounge Status:** Minimal stub (landing page only, ~3 components)

### Lounge Project (lounge/aksho-lounge-dev/)
- **Version:** v0.1.0 (Development, 70% complete)
- **Tech Stack:** Next.js 16.1.4, React 19.0.0, TypeScript, Tailwind CSS
- **Database:** SQLite + Prisma ORM 5.22.0
- **Auth:** Mock dev accounts (Alice, Bob, Charlie)
- **Features:** 
  - Multi-provider BYOK AI (Anthropic, OpenAI, DeepSeek, OpenRouter)
  - Aksho Mini free hosted model (50 msgs/24h)
  - Sonarcore v4.0 emotional context extraction (1600+ location keywords, ~2-3ms)
  - Picturize dynamic image generation
  - Dynamic avatars (static/gallery/emotional modes)
  - V2 character card spec with subcategorized descriptions
  - Message branching & editing
  - Lorebook (world info) support
  - Advanced prompt system with templates

---

## Critical Technical Challenges

### 1. Database ORM Conflict ⚠️ CRITICAL
- **Main:** Drizzle ORM + PostgreSQL
- **Lounge:** Prisma ORM + SQLite
- **Impact:** 11 Prisma models need conversion, 25+ service files affected
- **Estimated Effort:** 40-60 hours

### 2. Authentication Integration ⚠️ CRITICAL
- **Main:** Better-auth with production sessions
- **Lounge:** Mock dev accounts
- **Impact:** All Lounge API routes need userId injection
- **Estimated Effort:** 8-12 hours

### 3. Type System Conflicts ⚠️ MODERATE
- Both define `Character`, `SpeciesType`, `GenderType` with different shapes
- Main: Tag-focused (character creator), Lounge: Chat-focused (V2 spec)
- **Solution:** Namespace types (`HangarCharacter` vs `LoungeCharacter`)

### 4. State Management Isolation ⚠️ MODERATE
- Main: `aksho-store.ts` (2541 lines - character creator)
- Lounge: `lounge-store.ts` (2808 lines - chat state)
- **Solution:** Keep separate stores with clear naming

---

## Integration Strategy: Non-Destructive Module Pattern

### Architecture Principle
Place all Lounge code in isolated feature module at `/src/features/lounge/` with adapter layers for database and authentication. Zero modifications to existing main application code.

### Directory Structure
```
akshoai/src/
├── features/
│   └── lounge/                        # NEW: Isolated Lounge module
│       ├── components/                # 30+ chat UI components
│       ├── hooks/                     # Chat-specific hooks
│       ├── services/                  # 25+ services (AI, sonarcore, picturize)
│       ├── stores/
│       │   └── lounge-store.ts       # Chat state (2808 lines)
│       └── types/
│           └── lounge.ts              # Chat types (737 lines)
├── lib/
│   ├── adapters/
│   │   └── lounge-db-adapter.ts      # NEW: Prisma → Drizzle translator
│   └── bridges/
│       ├── hangar-lounge-bridge.ts   # NEW: Character creator → Chat
│       ├── atelier-picturize-bridge.ts # NEW: Image gen integration
│       └── lounge-gamification-bridge.ts # NEW: Chat → Achievements/Miles
├── middleware/
│   └── lounge-auth.ts                # NEW: Better-auth wrapper
└── app/
    └── lounge/                        # REPLACE: Full implementation
        ├── page.tsx                   # Landing/discovery
        ├── chat/[chatId]/page.tsx    # Chat interface
        └── swipy/page.tsx             # Character discovery
```

---

## Implementation Plan

### Phase 1: Database Migration (Week 1-2)

#### Step 1.1: Create Drizzle Schema for Lounge Models
Convert 11 Prisma models to Drizzle:
- `users` (already exists in main, extend if needed)
- `characters` (V2 spec: subcategorized descriptions, alternate intros)
- `lorebooks` + `lorebook_entries` (world info)
- `chats` (character snapshots, settings)
- `messages` (branching: parent_message_id, superseded_by_id)
- `chat_participants` (group chat support)
- `prompt_presets` (reusable templates)
- `api_keys` (encrypted BYOK keys)
- `analytics_events` (usage tracking)

**File:** `akshoai/src/lib/db/schema-lounge.ts`

#### Step 1.2: Build Database Adapter
Create abstraction layer maintaining Prisma function signatures:

```typescript
// akshoai/src/lib/adapters/lounge-db-adapter.ts
export class LoungeDbAdapter {
  // Characters
  async findManyCharacters(userId: string): Promise<LoungeCharacter[]>
  async createCharacter(data: CreateCharacterInput): Promise<LoungeCharacter>
  async updateCharacter(id: string, data: UpdateCharacterInput): Promise<LoungeCharacter>
  async deleteCharacter(id: string): Promise<void>
  
  // Chats
  async findManyChats(userId: string): Promise<Chat[]>
  async createChat(data: CreateChatInput): Promise<Chat>
  async updateChat(id: string, data: UpdateChatInput): Promise<Chat>
  
  // Messages (with branching support)
  async findMessagesInChat(chatId: string): Promise<Message[]>
  async createMessage(data: CreateMessageInput): Promise<Message>
  async updateMessage(id: string, data: UpdateMessageInput): Promise<Message>
  async getMessageLineage(messageId: string): Promise<Message[]>
  
  // Lorebooks
  async findLorebooks(characterId: string): Promise<Lorebook[]>
  async createLorebook(data: CreateLorebookInput): Promise<Lorebook>
  
  // API Keys (encrypted)
  async getApiKeys(userId: string): Promise<ApiKey[]>
  async upsertApiKey(data: UpsertApiKeyInput): Promise<ApiKey>
  
  // Prompt Presets
  async findPromptPresets(userId: string): Promise<PromptPreset[]>
  async createPromptPreset(data: CreatePresetInput): Promise<PromptPreset>
}
```

#### Step 1.3: Update All Lounge Services
Replace `prisma.*` calls with adapter calls in 25+ service files:
- `chatEngine.ts` (prompt assembly, context management)
- `ai-providers/*.ts` (Anthropic, OpenAI, DeepSeek, OpenRouter)
- `sonarcore.ts` (emotional context extraction)
- `picturize.ts` (image generation prompts)
- `characterCardImport.ts` (V2 card import/export)
- `promptPresets.ts`, `personas.ts`, `vault.ts`, etc.

---

### Phase 2: Authentication Integration (Week 2)

#### Step 2.1: Create Auth Middleware
```typescript
// akshoai/src/middleware/lounge-auth.ts
import { auth } from '@/lib/auth';

export async function withLoungeAuth(handler: Function) {
  return async (req: Request) => {
    const session = await auth.api.getSession({ headers: req.headers });
    
    if (!session?.user?.id) {
      return Response.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // Inject userId into request context
    return handler(req, { userId: session.user.id });
  };
}
```

#### Step 2.2: Wrap All Lounge API Routes
Apply middleware to:
- `/api/lounge/characters/*` (CRUD)
- `/api/lounge/chats/*` (CRUD)
- `/api/lounge/messages/*` (CRUD with branching)
- `/api/lounge/picturize` (image generation)
- `/api/lounge/api-keys/*` (BYOK management)

#### Step 2.3: Update Lounge Store
Replace mock auth with better-auth session:
```typescript
// src/features/lounge/stores/lounge-store.ts
import { useSession } from '@/lib/auth-client';

// Replace mock user state with:
const session = useSession();
const userId = session.data?.user?.id;
```

---

### Phase 3: Code Integration (Week 3)

#### Step 3.1: Copy Lounge Module
```bash
# Copy components (30+ files)
cp -r lounge/aksho-lounge-dev/src/components/lounge akshoai/src/features/lounge/components

# Copy services (25+ files)
cp -r lounge/aksho-lounge-dev/src/services/* akshoai/src/features/lounge/services/

# Copy store
cp lounge/aksho-lounge-dev/src/stores/lounge-store.ts akshoai/src/features/lounge/stores/

# Copy types
cp lounge/aksho-lounge-dev/src/types/lounge.ts akshoai/src/features/lounge/types/
```

#### Step 3.2: Update Import Paths
Update all relative imports in Lounge code to new structure:
- `@/components/lounge/*` → `@/features/lounge/components/*`
- `@/services/*` → `@/features/lounge/services/*`
- `@/stores/lounge-store` → `@/features/lounge/stores/lounge-store`
- `@/types/lounge` → `@/features/lounge/types/lounge`

#### Step 3.3: Replace Lounge Routes
Replace stub implementations:
- `/app/lounge/page.tsx` - Landing with discovery UI
- `/app/lounge/chat/[chatId]/page.tsx` - Full chat interface
- `/app/lounge/swipy/page.tsx` - Character discovery (Tinder-style)

Replace stub API routes:
- `/api/lounge/characters/*` - Full CRUD with V2 card support
- `/api/lounge/chats/*` - Full CRUD with character snapshots
- `/api/lounge/messages/*` - CRUD with branching (parent/superseded)
- `/api/lounge/picturize` - Image generation intent + prompting

#### Step 3.4: Update Dependencies
Merge `package.json` dependencies:
```json
{
  "dependencies": {
    "js-tiktoken": "^1.0.21",          // Token counting
    "react-markdown": "^10.1.0",        // Chat message rendering
    "rehype-highlight": "^7.0.2",       // Code syntax highlighting
    "remark-gfm": "^4.0.1"              // GitHub Flavored Markdown
  }
}
```

Note: Remove Prisma if using adapter approach, or keep both ORMs if using dual-ORM strategy.

---

### Phase 4: Feature Bridges (Week 4)

#### Bridge 4.1: Hangar → Lounge Character Export
```typescript
// akshoai/src/lib/bridges/hangar-lounge-bridge.ts

export async function exportHangarToLounge(
  hangarCharacter: HangarCharacter,
  userId: string
): Promise<LoungeCharacter> {
  const adapter = new LoungeDbAdapter();
  
  // Convert 480+ tag system to V2 character card
  const v2Character = {
    name: hangarCharacter.name,
    species: hangarCharacter.species,
    gender: hangarCharacter.gender,
    description: {
      basic: generateBasicDescription(hangarCharacter.tags),
      physical: generatePhysicalDescription(hangarCharacter.tags),
      clothing: generateClothingDescription(hangarCharacter.tags),
      personality: generatePersonalityDescription(hangarCharacter.tags),
      background: generateBackgroundDescription(hangarCharacter.tags)
    },
    systemPrompt: generateSystemPrompt(hangarCharacter.tags),
    // ... more V2 spec fields
  };
  
  return await adapter.createCharacter({
    userId,
    ...v2Character
  });
}
```

Add button to Hangar UI:
```typescript
// In src/components/hangar/character-actions.tsx
<Button onClick={() => exportToLounge(character)}>
  Chat with Character
</Button>
```

#### Bridge 4.2: Lounge Picturize → Atelier API
```typescript
// akshoai/src/lib/bridges/atelier-picturize-bridge.ts

export async function generateChatImage(
  character: LoungeCharacter,
  sonarcore: SonarcoreData,
  intent: PicturizeIntent
): Promise<string> {
  // Build prompt from character appearance + sonarcore context
  const prompt = buildPicturizePrompt({
    character: {
      species: character.species,
      gender: character.gender,
      appearance: character.description.physical,
      clothing: character.description.clothing
    },
    context: {
      location: sonarcore.location,
      timeOfDay: sonarcore.timeOfDay,
      emotion: sonarcore.emotion,
      activity: intent.activity
    }
  });
  
  // Call existing Atelier API
  const response = await fetch('/api/atelier/generate', {
    method: 'POST',
    body: JSON.stringify({
      workflow: 'character-selfie',
      prompt,
      // ... other params
    })
  });
  
  const { imageUrl } = await response.json();
  return imageUrl;
}
```

#### Bridge 4.3: Lounge → Gamification System
```typescript
// akshoai/src/lib/bridges/lounge-gamification-bridge.ts
import { grantAchievement, addMiles } from '@/lib/services/gamification-service';

export async function onChatEvent(
  event: 'first_visit' | 'first_chat' | 'message_sent',
  userId: string
) {
  switch (event) {
    case 'first_visit':
      await grantAchievement(userId, 'LOUNGE');
      break;
    
    case 'first_chat':
      await grantAchievement(userId, 'FIRST_CHAT');
      await addMiles(userId, 10, 'First chat created');
      break;
    
    case 'message_sent':
      // Grant 1 mile per message (max 20/day)
      await addMiles(userId, 1, 'Chat message sent');
      break;
  }
}
```

Hook into chat store:
```typescript
// In lounge-store.ts sendMessage action
const result = await sendMessageAPI(content);
await onChatEvent('message_sent', userId);
return result;
```

---

### Phase 5: Testing & Polish (Week 5)

#### Test 5.1: Integration Testing
- ✅ Create character in Hangar → Export to Lounge
- ✅ Start chat with Lounge character
- ✅ Send messages with all BYOK providers (Anthropic, OpenAI, DeepSeek, OpenRouter)
- ✅ Test "Aksho Mini" free hosted model
- ✅ Test Sonarcore extraction accuracy
- ✅ Test message branching (create alternate timeline)
- ✅ Test Picturize image generation
- ✅ Test dynamic avatar modes (static/gallery/emotional)
- ✅ Verify achievements granted (LOUNGE, FIRST_CHAT)
- ✅ Verify miles awarded (message sent)

#### Test 5.2: Authentication Flow
- ✅ Logged-out users redirected to auth
- ✅ Logged-in users see their characters/chats
- ✅ User isolation (can't access other users' data)
- ✅ SubscribeStar tier affects Aksho Mini limits

#### Test 5.3: Performance Validation
- ✅ Bundle size impact (lazy load Lounge if needed)
- ✅ SSR compatibility (no client-only dependencies breaking)
- ✅ Sonarcore execution time (<5ms for 5 messages)
- ✅ Message list virtualization for long chats
- ✅ Database query performance (PostgreSQL vs SQLite)

#### Test 5.4: Edge Cases
- ✅ Long chat history (1000+ messages)
- ✅ Branching message tree navigation
- ✅ Character with no avatar (fallback)
- ✅ API key encryption/decryption
- ✅ Token limit handling (truncate context)
- ✅ Rate limiting (50 msgs/24h for Aksho Mini)

---

## Configuration Changes

### package.json Updates
```json
{
  "dependencies": {
    "js-tiktoken": "^1.0.21",
    "react-markdown": "^10.1.0",
    "rehype-highlight": "^7.0.2",
    "remark-gfm": "^4.0.1"
  }
}
```

### tsconfig.json Path Aliases (if needed)
```json
{
  "compilerOptions": {
    "paths": {
      "@/features/*": ["./src/features/*"]
    }
  }
}
```

### tailwind.config.ts (Already Compatible)
Both projects use Aksho color system. Main's config is more comprehensive, no merge needed.

---

## Dependency Migration Summary

### Add to Main
- `js-tiktoken` - Token counting for context management
- `react-markdown` - Render markdown in chat messages
- `rehype-highlight` - Syntax highlighting for code blocks
- `remark-gfm` - GitHub Flavored Markdown support

### Already in Main (No Duplicates)
- Next.js 16.1.4
- React 19+ (main has 19.2.3, lounge has 19.0.0 - use main's)
- TypeScript 5.3.3
- Tailwind CSS 3.4.0
- Zustand 4.4.7

### Database Decision Point
**Option A: Adapter Pattern (Recommended)**
- Keep Drizzle as main ORM
- Remove Prisma from dependencies
- Build adapter layer translating Prisma → Drizzle
- Pro: Single ORM, cleaner architecture
- Con: 40-60 hours adapter development

**Option B: Dual-ORM**
- Add Prisma to main dependencies
- Keep both ORMs running
- Pro: Faster integration (8-12 hours)
- Con: Increased complexity, two ORMs to maintain

---

## Risk Assessment

### High Risk
1. **Database adapter bugs** - Complex branching message queries
   - Mitigation: Extensive unit testing, gradual rollout
   
2. **Auth middleware edge cases** - Session expiry during chat
   - Mitigation: Graceful error handling, auto-refresh tokens

3. **Type system conflicts** - Same names, different shapes
   - Mitigation: Namespace all Lounge types, use `import type { ... as ... }`

### Medium Risk
1. **Bundle size increase** - 25+ services, large store
   - Mitigation: Lazy load Lounge, code splitting per route
   
2. **State management collisions** - Two large Zustand stores
   - Mitigation: Clear naming (`useHangarStore`, `useLoungeStore`)

3. **Performance regression** - PostgreSQL vs SQLite queries
   - Mitigation: Add database indices, optimize N+1 queries

### Low Risk
1. **UI/UX inconsistencies** - Different design patterns
   - Mitigation: Both use Aksho design system, should be consistent
   
2. **API route conflicts** - Same paths, different implementations
   - Mitigation: Lounge routes are superior, clean replacement

---

## Success Metrics

### Functional Requirements
- ✅ All Lounge features working in main app
- ✅ Zero modifications to existing main code
- ✅ Hangar characters can be chatted with
- ✅ BYOK API keys work with all providers
- ✅ Sonarcore extracts context accurately
- ✅ Message branching maintains lineage
- ✅ Gamification hooks award achievements/miles

### Technical Requirements
- ✅ Single database (PostgreSQL + Drizzle)
- ✅ Unified auth (better-auth)
- ✅ Bundle size increase <500KB
- ✅ No SSR breaking changes
- ✅ Type safety maintained
- ✅ All tests passing

### Quality Requirements
- ✅ No regressions in existing features
- ✅ Performance meets expectations
- ✅ User data properly isolated
- ✅ Error handling graceful
- ✅ Loading states smooth

---

## Timeline Estimate

| Phase | Duration | Effort | Dependencies |
|-------|----------|--------|--------------|
| **Phase 1:** Database Migration | 1-2 weeks | 40-60 hrs | None |
| **Phase 2:** Auth Integration | 3-4 days | 8-12 hrs | Phase 1 |
| **Phase 3:** Code Integration | 4-5 days | 12-16 hrs | Phase 2 |
| **Phase 4:** Feature Bridges | 4-5 days | 12-16 hrs | Phase 3 |
| **Phase 5:** Testing & Polish | 5-7 days | 40+ hrs | Phase 4 |
| **Total** | **5-6 weeks** | **120-150 hrs** | Sequential |

**Recommended Team:**
- 1 Backend Engineer (database adapter)
- 1 Frontend Engineer (UI integration)
- 1 Full-Stack Engineer (bridges & testing)

---

## Open Questions for Refinement

### Q1: Database Strategy Choice
**Question:** Use adapter pattern (Prisma → Drizzle) or dual-ORM approach?

**Context:** 
- Adapter: Cleaner, single ORM, but 40-60 hours development
- Dual-ORM: Faster (8-12 hours), but two ORMs to maintain

**Recommendation:** Adapter pattern for long-term maintainability

---

### Q2: Type Namespace Strategy
**Question:** How to handle type name conflicts (`Character`, `SpeciesType`, `GenderType`)?

**Options:**
- A) Rename Lounge types: `ChatCharacter`, `ChatSpeciesType`
- B) Namespace imports: `import type { Character as LoungeCharacter }`
- C) Directory namespacing: `@/types/hangar/*` vs `@/types/lounge/*`

**Recommendation:** Option C - Directory namespacing for clarity

---

### Q3: Encrypted API Key Compatibility
**Question:** Are Lounge `vault.ts` and main `/api/vault` endpoints compatible?

**Context:**
- Lounge: AES-256-GCM encryption, system keyring + encrypted fallback
- Main: Has vault endpoints but implementation unclear

**Action Required:** Review main's vault implementation, merge if incompatible

---

### Q4: Sonarcore Performance on PostgreSQL
**Question:** Will Sonarcore maintain <5ms performance on PostgreSQL vs SQLite?

**Context:**
- Current: 2-3ms for 5 messages on SQLite
- PostgreSQL is network-based (Neon), may add latency

**Mitigation:** Cache sonarcore data in Redis if performance degrades

---

### Q5: Message Branching UI in Main App
**Question:** Does main app's design system support branching message visualization?

**Context:**
- Lounge has tree navigation for alternate timelines
- Main app UI patterns unclear

**Action Required:** Review main's chat UI components, ensure compatibility

---

## Next Steps

1. **Review and approve this plan** - Stakeholder sign-off
2. **Choose database strategy** - Adapter vs Dual-ORM
3. **Set up development branch** - `feature/lounge-integration`
4. **Phase 1: Start database adapter** - Highest priority, longest duration
5. **Create progress tracking** - GitHub project board with milestones

---

## Appendix: File Migration Checklist

### Components (30+ files)
- [ ] `character-card.tsx`
- [ ] `chat-interface.tsx`
- [ ] `message-bubble.tsx`
- [ ] `message-list.tsx`
- [ ] `chat-input.tsx`
- [ ] `character-avatar.tsx`
- [ ] `provider-selector.tsx`
- [ ] `prompt-preset-selector.tsx`
- [ ] `lorebook-editor.tsx`
- [ ] `swipy-card.tsx`
- [ ] ... (20+ more)

### Services (25+ files)
- [ ] `chatEngine.ts` (1626 lines)
- [ ] `sonarcore.ts` (emotional context)
- [ ] `picturize.ts` (image generation)
- [ ] `ai-providers/anthropic.ts`
- [ ] `ai-providers/openai.ts`
- [ ] `ai-providers/deepseek.ts`
- [ ] `ai-providers/openrouter.ts`
- [ ] `characterCardImport.ts`
- [ ] `promptPresets.ts`
- [ ] `personas.ts`
- [ ] `vault.ts`
- [ ] `keyStorage.ts`
- [ ] `encryption.ts`
- [ ] ... (10+ more)

### Store & Types
- [ ] `lounge-store.ts` (2808 lines)
- [ ] `types/lounge.ts` (737 lines)

### API Routes
- [ ] `/api/lounge/characters/*` (5 endpoints)
- [ ] `/api/lounge/chats/*` (5 endpoints)
- [ ] `/api/lounge/messages/*` (6 endpoints)
- [ ] `/api/lounge/picturize`
- [ ] `/api/lounge/api-keys/*`

### Pages
- [ ] `/lounge/page.tsx`
- [ ] `/lounge/chat/[chatId]/page.tsx`
- [ ] `/lounge/swipy/page.tsx`

---

## CRITICAL ISSUES & REVISION NOTES

### 🚨 FUNDAMENTAL CONTRADICTIONS

#### 1. "Without Editing Main" is Misleading
**Problem:** The plan title says "Without Editing Main Application" but Phase 3 explicitly involves:
- Replacing entire route implementations (`/app/lounge/*`)
- Adding buttons to Hangar UI (`character-actions.tsx`)
- Hooking into existing stores
- Replacing stub API routes

**Reality:** This IS editing the main application extensively. The approach is actually "additive with strategic replacements."

**Recommendation:** Rename to "Merge Lounge into Main via Feature Module Pattern" and clarify that we're:
- Adding new code in isolated `/features/lounge/`
- Replacing minimal stubs with full implementations
- Bridging to existing systems (not modifying their internals)

---

#### 2. Directory Structure Doesn't Exist
**Problem:** Plan shows `/src/features/` directory structure, but main app has:
```
src/
├── app/
├── components/
├── hooks/
├── lib/
├── store/
├── types/
└── utils/
```

**No `features/` folder exists.**

**Impact:** All copy commands and import paths will fail. Code examples assume non-existent structure.

**Recommendation:** Either:
- A) Keep flat structure: `/src/components/lounge/`, `/src/services/lounge/`, `/src/stores/lounge-store.ts`
- B) Create features folder first as setup step
- C) Use existing patterns: `/src/lib/lounge/` for services

---

#### 3. Middleware Doesn't Exist in Main App
**Problem:** Plan references `/src/middleware/lounge-auth.ts` but file search shows no middleware folder exists.

**Impact:** Next.js 13+ App Router uses different auth patterns. The `withLoungeAuth` wrapper function signature is incorrect for App Router.

**Correct Pattern for App Router:**
```typescript
// Should be in route files themselves or use route handlers
import { auth } from '@/lib/auth'

export async function GET(req: Request) {
  const session = await auth.api.getSession({ headers: req.headers })
  if (!session?.user?.id) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }
  // ... route logic
}
```

**Recommendation:** Remove middleware concept, document auth pattern to use in each API route.

---

### 🔴 DATABASE MIGRATION CRITICAL GAPS

#### 4. Missing Drizzle Schema Definition
**Problem:** Plan mentions creating `schema-lounge.ts` but provides NO concrete Drizzle schema code.

**Current State:**
- Lounge has 11 Prisma models with specific SQLite features
- Main uses Drizzle with different patterns (see `user-service.ts`)
- No conversion examples provided

**Critical Questions Unanswered:**
- How to handle Prisma's `@relation` vs Drizzle relations?
- How to convert `Decimal` types (not native to PostgreSQL via Drizzle)?
- How to handle recursive relations (`messages` → `parent_message_id` self-reference)?
- How to maintain JSON column compatibility (SQLite TEXT vs PostgreSQL JSON)?

**Example Missing:**
```typescript
// Prisma
model messages {
  parent_message_id String?
  messages messages? @relation("messagesTomessages", fields: [parent_message_id], references: [id])
  other_messages messages[] @relation("messagesTomessages")
}

// Drizzle equivalent? NOT SHOWN IN PLAN
```

**Recommendation:** Add complete Drizzle schema example for at least 3 complex models (messages, characters, chats).

---

#### 5. Adapter Pattern Underspecified
**Problem:** `LoungeDbAdapter` class is shown with function signatures only, no implementation details.

**Critical Issues:**
- Plan says "maintains Prisma function signatures" but Prisma uses query builder pattern
- No explanation of how to get database connection (Drizzle uses `getPool()` in main)
- No transaction handling strategy
- No error handling pattern
- No pagination/cursor strategy

**Example:**
```typescript
// Plan shows:
async findManyCharacters(userId: string): Promise<LoungeCharacter[]>

// But HOW? Main app uses this pattern:
const pool = getPool()
const result = await pool.query('SELECT * FROM characters WHERE user_id = $1', [userId])
// vs Drizzle ORM? vs direct SQL?
```

**Recommendation:** Provide at least 2 complete adapter method implementations with proper Drizzle patterns.

---

#### 6. Service File Updates Vastly Underestimated
**Problem:** Plan says "Replace `prisma.*` calls in 25+ service files."

**Reality Check:**
- `chatEngine.ts` is 1626 lines and imports types from Prisma
- Services don't just call `prisma.*` directly - they use complex queries with includes, nested relations
- Token counting, prompt construction, etc. have no DB calls

**Search Results Show:**
- API routes call `prisma.characters.create()`, `prisma.chats.findMany()`, etc.
- NOT centralized in service layer
- Need to update 16+ API route files, not just services

**Recommendation:** 
- Audit which files actually use Prisma (hint: API routes, not services)
- Separate "database layer" from "business logic layer"
- Plan says 40-60 hours but may be 80-100 hours

---

### ⚠️ AUTHENTICATION ISSUES

#### 7. Auth Pattern Mismatch
**Problem:** Lounge uses header-based auth (`x-user-id`), Main uses better-auth sessions.

**Current Lounge Pattern:**
```typescript
const userId = request.headers.get('x-user-id') || 'anonymous'
```

**Main App Pattern:**
```typescript
// From user-service.ts, better-auth likely similar
const session = await validateSession(sessionId)
```

**Gap:** Plan doesn't explain:
- Where/how to inject session into requests (client-side)
- How to handle SSR vs client-side auth
- How to handle auth in server actions vs API routes

**Recommendation:** Document complete auth flow:
1. Client-side: How to attach session to fetch calls
2. Server-side: How each route type gets session
3. Error handling: Redirect vs 401 response

---

#### 8. User Model Mismatch
**Problem:** 
- **Lounge users table:** Has `username`, `email`, `password_hash`, `tier`, `role`
- **Main users table:** Has `type` (passenger/authenticated), `subscriptionTier`, `subscriptionProvider`

**Critical Conflict:** Different schemas mean adapter can't just map 1:1.

**Questions:**
- Map Lounge `tier` → Main `subscriptionTier`?
- What about Lounge `role` (user/admin)?
- What about Lounge `password_hash` (Main uses better-auth)?
- What about Lounge `username` (Main might not have it)?

**Recommendation:** Define user schema mapping table and handle missing fields.

---

### 🟡 TYPE SYSTEM ISSUES

#### 9. Type Namespace Strategy Not Implemented
**Problem:** Plan recommends "Option C: Directory namespacing" but all code examples use conflicting names.

**Conflicts Found:**
```typescript
// Plan shows both:
import type { Character } from '@/types/character' // Main
import type { Character } from '@/features/lounge/types/lounge' // Lounge

// Bridge code uses:
LoungeCharacter // Not defined anywhere
HangarCharacter // Not defined anywhere
```

**Impact:** TypeScript will error on ambiguous imports.

**Recommendation:** 
- Decide on ONE namespace strategy and apply everywhere
- Update all code examples to use chosen strategy
- Consider: `@/types/hangar/character.ts` vs `@/types/lounge/character.ts`

---

#### 10. Missing Type Definitions
**Problem:** Plan references types that don't exist:
- `CreateCharacterInput` (in adapter, but not in types)
- `UpdateCharacterInput` (similar)
- `CreateChatInput`, `CreateMessageInput`, etc.

**These are Prisma-generated types** that won't exist after migration.

**Recommendation:** Document strategy for type generation:
- Option A: Manually define all input/output types
- Option B: Use Drizzle's type inference
- Option C: Create type generator script

---

### 🟠 INTEGRATION GAPS

#### 11. Environment Variables Not Addressed
**Problem:** Lounge uses AI provider API keys, Main doesn't.

**Lounge Likely Has:**
```env
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
DEEPSEEK_API_KEY=
OPENROUTER_API_KEY=
AKSHO_MINI_ENDPOINT=
```

**Main Has:** (unknown, .env.example doesn't exist)

**Impact:** 
- BYOK features need env var setup
- "Aksho Mini" free model needs endpoint configuration
- No migration plan for these

**Recommendation:** 
- Add env var setup section
- Document BYOK vs hosted model architecture
- Explain where API keys are stored (vault? env? both?)

---

#### 12. Vault Compatibility Question Left Open
**Problem:** "Q3: Encrypted API Key Compatibility" is listed as "Action Required: Review main's vault implementation, merge if incompatible."

**This is a BLOCKER** but treated as optional.

**Impact:**
- Lounge vault: AES-256-GCM, system keyring + fallback
- Main vault: Unknown implementation
- If incompatible, BYOK feature won't work

**Recommendation:** 
- Move this to Phase 0: Investigation
- Must be resolved before Phase 1 starts
- Add vault compatibility to "Prerequisites" section

---

#### 13. CDN Integration Unclear
**Problem:** Plan mentions:
- "Main has cdn.akshoai.com integration"
- "Ensure Lounge uses same CDN"

**But:** Lounge character creation uploads avatars - WHERE? HOW?

**Questions:**
- Does Lounge have existing upload service?
- Does it use Cloudflare R2? S3?
- Is it in `/api/characters` route?
- How to migrate to main's CDN?

**Recommendation:** Add CDN migration sub-section with upload flow diagram.

---

### 🔵 MISSING CRITICAL SECTIONS

#### 14. No Database Migration Strategy
**Problem:** Plan focuses on ORM conversion but ignores data migration.

**Questions:**
- Are there existing Lounge characters to migrate?
- Test data from dev accounts (Alice, Bob, Charlie)?
- Migration scripts for SQLite → PostgreSQL?
- Data validation after migration?

**Recommendation:** Add "Phase 0: Data Migration" section with:
1. Export existing SQLite data
2. Transform to PostgreSQL format
3. Import via Drizzle
4. Validation queries

---

#### 15. No Testing Strategy
**Problem:** Phase 5 has testing checklist but no HOW.

**Missing:**
- Test environment setup (separate DB? test users?)
- How to run tests (Jest? Playwright? manual?)
- How to populate test data
- Rollback strategy if tests fail

**Recommendation:** Add testing architecture section before Phase 5.

---

#### 16. No Rollback Plan
**Problem:** If integration fails at Phase 3, how to recover?

**Risks:**
- Merged code breaking main app
- Database schema changes irreversible
- Production dependencies added

**Recommendation:** Add rollback strategy for each phase.

---

#### 17. No Development Workflow
**Problem:** How to work on Lounge features while main app is running?

**Questions:**
- Separate branch? Feature flag?
- How to test Lounge in isolation?
- How to run both apps during development?

**Recommendation:** Add "Development Setup" section with:
- Branch strategy
- Local dev environment setup
- How to test incrementally

---

### 📊 EFFORT ESTIMATES QUESTIONABLE

#### 18. Timeline Seems Optimistic
**Problem:** 
- Database migration: 40-60 hours (plan says 1-2 weeks)
- Auth integration: 8-12 hours (3-4 days)
- Code integration: 12-16 hours (4-5 days)

**Reality Check:**
- 1 week = 40 hours (assuming full-time)
- Database migration alone is 40-60 hours = 1-1.5 weeks AT BEST
- 8-12 hours = 1-1.5 days, NOT 3-4 days

**Inconsistency:** Hours don't match day estimates.

**Recommendation:** 
- Choose one unit (hours OR days)
- Add buffer time (multiply by 1.5x)
- Account for debugging, which is often 50% of development

---

#### 19. No Contingency Planning
**Problem:** All estimates assume smooth execution.

**What if:**
- Database adapter bugs take 2x time?
- Auth integration breaks existing features?
- Type conflicts require major refactoring?

**Recommendation:** Add 25-50% contingency buffer to each phase.

---

### 🎯 DEPENDENCY ISSUES

#### 20. React Version Conflict Unresolved
**Problem:** Main has React 19.2.3, Lounge has 19.0.0. Plan says "use main's" but doesn't address potential breaking changes.

**Questions:**
- Are Lounge components compatible with 19.2.3?
- Any deprecated APIs in Lounge code?
- Need to test all components after upgrade?

**Recommendation:** Add compatibility testing task.

---

#### 21. Prisma Removal Strategy Missing
**Problem:** Plan recommends "Remove Prisma if using adapter approach" but doesn't explain HOW.

**Impact:**
- Prisma is in devDependencies and dependencies
- Prisma client generated files in node_modules
- Import statements throughout Lounge code

**Recommendation:** Add clean-up steps:
1. Remove all Prisma imports
2. Remove from package.json
3. Delete prisma/ directory
4. Remove Prisma types from tsconfig

---

### 🏗️ ARCHITECTURAL CONCERNS

#### 22. Dual-ORM Option Underexplored
**Problem:** Plan dismisses dual-ORM as "increased complexity" but might be more practical.

**Dual-ORM Advantages:**
- Faster integration (8-12 hours vs 40-60)
- Lower risk (keep Lounge code working as-is)
- Easier rollback
- Can migrate gradually

**Dual-ORM Disadvantages:**
- Two DB connections (Neon PostgreSQL + ???) 
- Wait, Lounge uses SQLite, can't use that in production
- This doesn't actually work

**Revelation:** Dual-ORM is NOT viable because Lounge uses SQLite (file-based), must migrate to PostgreSQL regardless.

**Recommendation:** Remove dual-ORM option entirely, it's not realistic.

---

#### 23. Service Pattern Mismatch
**Problem:** 
- Main app uses service layer pattern (`user-service.ts`, `gamification-service.ts`)
- Lounge uses repository pattern (Prisma calls in API routes)

**Impact:** Adapter layer doesn't fit cleanly because services aren't consistently used.

**Recommendation:** 
- Refactor Lounge API routes to use service pattern FIRST
- Then build adapter layer in services
- Update plan to reflect this pre-work

---

### 📝 DOCUMENTATION GAPS

#### 24. No API Documentation Updates
**Problem:** Adding 16+ new API routes but no plan to document them.

**Questions:**
- Update API docs?
- Add OpenAPI/Swagger specs?
- Document for frontend developers?

**Recommendation:** Add API documentation task to Phase 5.

---

#### 25. No User-Facing Documentation
**Problem:** Adding major new feature (Lounge) but no user guide.

**Questions:**
- How do users access Lounge?
- Tutorial for BYOK setup?
- Character creation guide?

**Recommendation:** Add user documentation deliverable.

---

### ✅ PREREQUISITE CHECKLIST MISSING

**What Should Be Done BEFORE Phase 1:**

1. ✅ Stakeholder approval of plan
2. ✅ Vault implementation compatibility confirmed
3. ✅ CDN upload strategy decided
4. ✅ User schema mapping defined
5. ✅ Type namespace strategy chosen
6. ✅ Test environment provisioned
7. ✅ Development branch created
8. ✅ Backup strategy established
9. ✅ Communication plan for team
10. ✅ Success criteria defined

**Recommendation:** Add "Phase 0: Prerequisites & Investigation" before current Phase 1.

---

## RECOMMENDED PLAN REVISIONS

### Immediate Changes Needed:

1. **Rename Plan** → "Lounge Integration via Feature Module & Database Migration"

2. **Add Phase 0: Investigation & Prerequisites** (Week 0)
   - Vault compatibility check
   - CDN upload investigation  
   - User schema mapping
   - Test environment setup
   - Development branch strategy

3. **Fix Directory Structure** 
   - Use `/src/lib/lounge/services/` instead of `/src/features/`
   - Or document features/ folder creation as Step 0

4. **Remove Middleware Concept**
   - Document inline auth pattern for App Router

5. **Add Complete Drizzle Schema Example**
   - At least messages, characters, chats models
   - Show complex relations

6. **Add Adapter Implementation Examples**
   - 2-3 complete methods with error handling

7. **Clarify Auth Flow**
   - Client-side session attachment
   - Server-side session validation
   - Both API routes and Server Components

8. **Add Type Namespace Implementation**
   - Update all code examples
   - Show import patterns

9. **Add Environment Variables Section**
   - Required env vars
   - BYOK configuration
   - Aksho Mini endpoint

10. **Add Data Migration Section**
    - Export/transform/import strategy
    - Validation steps

11. **Add Testing Architecture**
    - Test environment setup
    - Test data population
    - Testing approach (unit/integration/e2e)

12. **Adjust Timeline**
    - Fix hours vs days inconsistency
    - Add 30% contingency buffer
    - Phase 0: 1 week
    - Phase 1: 2-3 weeks (not 1-2)
    - Total: 7-9 weeks (not 5-6)

13. **Remove Dual-ORM Option**
    - Not viable with SQLite → PostgreSQL migration

14. **Add Rollback Strategy**
    - Per-phase rollback plan
    - Git branch strategy
    - Database backup/restore

15. **Add Success Criteria**
    - Measurable goals for each phase
    - Acceptance testing checklist

---

## SEVERITY SUMMARY

| Issue Type | Count | Severity |
|------------|-------|----------|
| 🚨 Fundamental Contradictions | 3 | **CRITICAL** |
| 🔴 Database Migration Gaps | 3 | **CRITICAL** |
| ⚠️ Authentication Issues | 2 | **HIGH** |
| 🟡 Type System Issues | 2 | **MEDIUM** |
| 🟠 Integration Gaps | 3 | **MEDIUM** |
| 🔵 Missing Sections | 4 | **HIGH** |
| 📊 Effort Estimate Issues | 2 | **MEDIUM** |
| 🎯 Dependency Issues | 2 | **MEDIUM** |
| 🏗️ Architectural Concerns | 2 | **HIGH** |
| 📝 Documentation Gaps | 2 | **LOW** |
| **Total Issues** | **25** | - |

---

## CONCLUSION

This plan is **NOT READY FOR EXECUTION** in its current form. Major gaps in database migration strategy, authentication patterns, and directory structure would cause immediate failures.

**Estimated Revision Effort:** 20-30 hours to address all issues and create executable plan.

**Recommended Next Steps:**
1. Address all CRITICAL and HIGH severity issues
2. Create Phase 0 investigation tasks
3. Build proof-of-concept for database adapter (2-3 models)
4. Test auth integration in isolation
5. Re-estimate timeline with realistic buffers
6. Get stakeholder review of revised plan

---

**End of Plan + Critical Issues Analysis**
