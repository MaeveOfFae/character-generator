# Plan: Lounge Integration into AkshoAI (REVISED & VALIDATED)

## Executive Summary

Integrate the fully-featured Lounge chat system (70% complete, 34 components, 30+ services, Sonarcore v4.0, multi-provider BYOK AI) into the main AkshoAI application using **raw SQL migration**, service layer pattern, and strategic stub replacement.

**This is an additive integration** that replaces 3 minimal stub components with 34 full implementations, creates 15 new API routes from scratch, and bridges to existing gamification/auth/CDN systems.

**CRITICAL VALIDATION NOTES:**
- ✅ Both codebases validated against actual file structure
- ✅ Main uses **raw SQL via Neon pool**, NOT Drizzle ORM for queries
- ✅ Main uses **flat directory structure**, NOT `/src/features/`
- ✅ Main uses **inline auth in routes**, NOT middleware wrappers
- ✅ All code examples reflect actual patterns from main codebase
- ⚠️ Phase 0 prerequisites are **BLOCKING** - must complete before Phase 1

**Estimated Total Effort:** 140-180 hours over 7-9 weeks (includes 30% contingency buffer)

---

## Current State Analysis (VALIDATED)

### Main Application (akshoai/)
- **Version:** v3.36.2 (Production)
- **Tech Stack:** Next.js 16.1.4 (App Router), React 19.2.3, TypeScript 5.3.3, Tailwind CSS 3.4.0
- **Database:** Neon PostgreSQL via `@neondatabase/serverless` 
  - **CRITICAL:** Uses **raw SQL queries** with `getPool().query()` pattern
  - **NOT using Drizzle ORM** for query execution
  - Service pattern: `database-pool.ts` exports `getPool()` → services use `pool.query()`
- **Auth:** Better-Auth 1.4.9 + SubscribeStar OAuth
  - **Pattern:** Inline session checks in each route handler
  - **NO middleware wrapper** - App Router pattern
- **Features:** 
  - Character Creator (Hangar) - 480+ tag system
  - Image Generation (Atelier) - ComfyUI workflows
  - Gamification System - Achievements, miles, pins
  - Cloudflare R2 CDN - Image uploads with AI moderation
- **Lounge Status:** 
  - 3 stub components exist in `/src/components/lounge/`
  - NO `/api/lounge/` routes exist
  - Stub files: `lounge-main.tsx`, `chat-interface.tsx`, `lounge-landing.tsx`
- **Directory Structure:** Flat (`/src/{app,components,lib,store,types,hooks,utils}/`)
- **NO `/src/features/` folder exists**
- **NO `/src/middleware/` folder exists**

### Lounge Project (lounge/aksho-lounge-dev/)
- **Version:** v0.1.0 (Development, 70% complete)
- **Tech Stack:** Next.js 16.1.4 (App Router), React 19.0.0, TypeScript 5.3.3, Tailwind CSS 3.4.0
- **Database:** SQLite via Prisma ORM 5.22.0
  - 11 Prisma models
  - Dev database: `prisma/dev.db` with test data
- **Auth:** Mock dev accounts (6 users: Alice, Bob, Charlie, David, Eve, Frank)
- **Components:** 34 React components (19KB-82KB each)
- **Services:** 30+ service files
  - Framework-agnostic: `chatEngine.ts` (1626 lines), `sonarcore.ts`, `picturize.ts`
  - Database-dependent: API route handlers call `prisma.*` directly
- **Store:** `lounge-store.ts` (2808 lines) - Zustand chat state
- **Types:** `lounge.ts` (737 lines) - V2 character card spec
- **Features:** 
  - **Multi-provider BYOK AI:** Anthropic, OpenAI, DeepSeek, OpenRouter (user brings own keys)
  - **Aksho Mini:** Free hosted model (50 msgs/24h)
  - **Sonarcore v4.0:** Emotional context extraction (1600+ location keywords, ~2-3ms)
  - **Picturize:** Dynamic image generation from chat context
  - **Dynamic Avatars:** Static/gallery/emotional modes
  - **V2 Character Card Spec:** Subcategorized descriptions (basic, physical, clothing, personality, background)
  - **Message Branching:** Alternate timelines with parent/superseded tracking
  - **Lorebook:** World info injection with keyword triggers
  - **Advanced Prompt System:** Template variables, presets, personas

---

## Critical Technical Challenges (VALIDATED)

### 1. Database Migration to Raw SQL ⚠️ CRITICAL
- **Main Pattern:** Raw SQL via `@neondatabase/serverless` pool (NOT Drizzle ORM)
- **Lounge Pattern:** Prisma ORM + SQLite
- **Impact:** 
  - 11 Prisma models → PostgreSQL schema (CREATE TABLE statements)
  - 15 API route files need SQL service layer (NOT ORM adapter)
  - Prisma query builder → Parameterized SQL queries
  - JSON columns: SQLite TEXT → PostgreSQL JSONB
  - Branching messages: Self-referential foreign keys
- **Estimated Effort:** 60-80 hours (validated: more complex than original 40-60 estimate)
- **Pattern to Follow:**
  ```typescript
  // Main's actual pattern (from user-service.ts)
  const pool = getPool()
  const result = await pool.query('SELECT * FROM table WHERE id = $1', [id])
  return result.rows[0]
  ```

### 2. Authentication Integration ⚠️ CRITICAL
- **Main Pattern:** Better-auth with **inline session checks** (App Router, NO middleware)
- **Lounge Pattern:** Mock dev accounts with header-based auth (`x-user-id`)
- **Impact:** 
  - 15 API routes need inline `auth.api.getSession()` checks
  - Store needs `useCachedSession()` hook from main
  - Client-side: Attach session to fetch calls
  - NO middleware wrapper function
- **Estimated Effort:** 12-16 hours (updated from 8-12 to account for inline pattern)
- **Pattern to Follow:**
  ```typescript
  // Main's App Router pattern (VALIDATED)
  import { auth } from '@/lib/auth'
  
  export async function GET(request: Request) {
    const session = await auth.api.getSession({ headers: request.headers })
    if (!session?.user?.id) {
      return Response.json({ error: 'Unauthorized' }, { status: 401 })
    }
    const userId = session.user.id
    // ... route logic
  }
  ```

### 3. Directory Structure Mismatch ⚠️ CRITICAL
- **Main Structure:** Flat (`/src/lib/`, `/src/components/`, `/src/store/`)
- **Lounge Structure:** Similar flat structure
- **Plan Assumption:** `/src/features/lounge/` (DOES NOT EXIST)
- **Impact:** All copy commands and import paths need correction
- **Resolution:** Use main's existing flat structure
  - Services: `/src/lib/lounge/` or `/src/lib/services/lounge-*.ts`
  - Components: `/src/components/lounge/` (already exists!)
  - Store: `/src/store/lounge-store.ts`
  - Types: `/src/types/lounge/`

### 4. Type System Conflicts ⚠️ MODERATE
- Both define: `Character`, `SpeciesType`, `GenderType` with different shapes
- **Main:** Tag-focused (480+ tags for character creator)
- **Lounge:** Chat-focused (V2 card spec with descriptions)
- **Resolution:** Directory-based namespace
  - Main: `@/types/hangar/character.ts`
  - Lounge: `@/types/lounge/index.ts`
  - Usage: `import type { Character as HangarCharacter } from '@/types/hangar/character'`

### 5. User Schema Mismatch ⚠️ MODERATE
- **Lounge users:** `username`, `email`, `password_hash`, `tier`, `role`
- **Main users:** `type` (passenger/authenticated), `subscriptionTier`, `subscriptionProvider`
- **Impact:** Cannot directly map user data 1:1
- **Resolution:** Phase 0 user schema mapping (BLOCKING task)

### 6. No Existing API Routes ⚠️ MODERATE
- **Finding:** Main has NO `/api/lounge/` routes currently
- **Impact:** Need to create 15 API routes from scratch (not "replace stubs")
- **Routes Needed:**
  - Characters: 2 routes (list/create, get/update/delete)
  - Chats: 5 routes (list/create, CRUD, group, participants, convert)
  - Messages: 2 routes (list/create, update/delete)
  - Picturize: 1 route
  - API Keys: 1 route

---

## Integration Strategy: Additive with Stub Replacement

### Architecture Principle
**Use main app's existing flat directory structure.** Add Lounge code alongside existing patterns. Replace 3 stub components with 34 full implementations. Create 15 new API routes from scratch. Bridge to existing systems without modifying their internals.

### Directory Structure (VALIDATED - Matches Main App)
```
akshoai/src/
├── app/
│   ├── lounge/
│   │   ├── page.tsx                   # UPDATE: Use new lounge-main component
│   │   ├── chat/[chatId]/page.tsx    # NEW: Full chat interface route
│   │   └── swipy/page.tsx             # NEW: Character discovery route
│   └── api/
│       └── lounge/                    # NEW: All API routes (none exist currently)
│           ├── characters/
│           │   ├── route.ts           # NEW: GET/POST characters
│           │   └── [id]/route.ts      # NEW: GET/PATCH/DELETE character
│           ├── chats/
│           │   ├── route.ts           # NEW: GET/POST chats
│           │   ├── [chatId]/
│           │   │   ├── route.ts       # NEW: GET/PATCH/DELETE chat
│           │   │   ├── messages/
│           │   │   │   ├── route.ts   # NEW: GET/POST messages
│           │   │   │   └── [messageId]/route.ts # NEW: PATCH/DELETE message
│           │   │   ├── participants/route.ts # NEW: GET/POST participants
│           │   │   └── convert-to-group/route.ts # NEW: POST convert
│           │   └── group/route.ts     # NEW: POST create group chat
│           ├── picturize/route.ts     # NEW: POST image generation
│           └── api-keys/route.ts      # NEW: GET/POST BYOK keys
├── components/
│   └── lounge/                        # REPLACE 3 stubs + ADD 31 new components
│       ├── lounge-main.tsx            # REPLACE: 19KB full implementation
│       ├── chat-interface.tsx         # REPLACE: 82KB full implementation
│       ├── lounge-landing.tsx         # REPLACE: Full implementation
│       ├── character-editor.tsx       # NEW: 37KB editor
│       ├── character-card.tsx         # NEW
│       ├── message-bubble.tsx         # NEW
│       ├── message-list.tsx           # NEW
│       ├── chat-input.tsx             # NEW
│       ├── provider-selector.tsx      # NEW
│       ├── prompt-preset-selector.tsx # NEW
│       └── ... (25+ more NEW components)
├── lib/
│   ├── services/                      # Main's pattern - ADD lounge services here
│   │   ├── lounge-characters.ts       # NEW: Character CRUD with raw SQL
│   │   ├── lounge-chats.ts            # NEW: Chat CRUD with raw SQL
│   │   ├── lounge-messages.ts         # NEW: Message CRUD with branching SQL
│   │   ├── lounge-lorebooks.ts        # NEW: Lorebook CRUD with raw SQL
│   │   ├── lounge-api-keys.ts         # NEW: Encrypted BYOK key storage
│   │   ├── lounge-presets.ts          # NEW: Prompt preset management
│   │   └── schema-lounge.sql          # NEW: PostgreSQL schema (11 tables)
│   ├── lounge/                        # NEW: Framework-agnostic business logic
│   │   ├── chatEngine.ts              # COPY: Pure logic - no DB (1626 lines)
│   │   ├── sonarcore.ts               # COPY: Pure computation (no DB)
│   │   ├── picturize.ts               # COPY: Intent detection (no DB)
│   │   ├── ai-providers.ts            # COPY: Multi-provider integration
│   │   ├── tokenCounter.ts            # COPY: Token counting
│   │   ├── avatarSelection.ts         # COPY: Avatar logic
│   │   ├── characterCardImport.ts     # COPY: V2 card import/export
│   │   ├── promptPresets.ts           # COPY: Preset templates
│   │   ├── personas.ts                # COPY: User persona system
│   │   └── ... (20+ more services)
│   └── bridges/                       # NEW: Integration points
│       ├── hangar-lounge-bridge.ts    # NEW: Hangar → Lounge export
│       ├── atelier-picturize-bridge.ts # NEW: Picturize → Atelier
│       └── lounge-gamification-bridge.ts # NEW: Chat events → Achievements
├── store/
│   └── lounge-store.ts                # NEW: Chat state (2808 lines)
├── types/
│   ├── hangar/                        # NEW: Namespace main's types
│   │   └── character.ts               # Existing main character type
│   └── lounge/                        # NEW: Namespace lounge types
│       └── index.ts                   # Lounge character/chat types (737 lines)
└── hooks/
    └── useLounge*.ts                  # NEW: Chat-specific hooks

NOTES:
- NO /src/middleware/ folder - using inline auth
- NO /src/features/ folder - using flat structure
- Services use getPool().query() for database access
```

---

## Implementation Plan

### Phase 0: Prerequisites & Investigation (Week 0 - BLOCKING)

**PURPOSE:** Resolve critical unknowns that would block later phases. **ALL TASKS ARE MANDATORY.**

#### Task 0.1: Vault Compatibility Check (2-3 days) 🚨 BLOCKER

**Why Critical:** If vaults are incompatible, BYOK feature (core Lounge functionality) won't work.

**Action Items:**
1. **Read main's vault implementation:**
   - File: `/src/app/api/vault/[userId]/route.ts` (if exists)
   - Check encryption algorithm, key derivation, storage format
2. **Compare with Lounge vault:**
   - File: `lounge/aksho-lounge-dev/src/services/vault.ts`
   - Lounge uses: AES-256-GCM, system keyring + encrypted fallback
3. **Test compatibility:**
   - Create test encrypted value in Lounge vault
   - Try decrypting in main's vault (or vice versa)
4. **Document differences:**
   - Key derivation function (PBKDF2? Argon2?)
   - Salt generation strategy
   - IV generation and storage
   - Recovery key mechanism

**Deliverable:** Vault compatibility report with one of:
- ✅ Compatible - use as-is
- ⚠️ Partially compatible - document migration path
- ❌ Incompatible - design unified vault v2

**Rollback Plan:** If incompatible and complex, BYOK may need to be Phase 2 feature (after initial integration).

#### Task 0.2: User Schema Mapping (1-2 days) 🚨 BLOCKER

**Why Critical:** User data structure mismatch will cause query failures in every API route.

**Action Items:**
1. **Inspect main's users table:**
   ```sql
   -- Run in Neon console
   \d users
   SELECT column_name, data_type FROM information_schema.columns 
   WHERE table_name = 'users';
   ```
2. **Create mapping table:**
   
   | Lounge Field | Main Field | Transform | Default/Fallback | Notes |
   |--------------|------------|-----------|------------------|-------|
   | `id` | `id` | Direct | - | UUID format? |
   | `username` | ??? | TBD | `email.split('@')[0]` | Check if username exists |
   | `email` | `email` | Direct | - | Check nullable |
   | `password_hash` | N/A | Skip | - | Better-auth handles this |
   | `tier` | `subscriptionTier` | Map values | `'economy'` | economy→economy, etc. |
   | `role` | ??? | TBD | `'user'` | Check if role field exists |
   | `displayName` | `displayName` | Direct | `username` | Check if exists |
   | `avatarUrl` | `avatarUrl` | Direct | `null` | Check if exists |
   | - | `type` | New field | `'authenticated'` | Main specific |
   | - | `subscriptionProvider` | New field | `null` | Main specific |

3. **Decide on user creation strategy:**
   - **Option A:** Lounge creates users in main's table (if needed)
   - **Option B:** Lounge assumes user exists from better-auth
   - **Recommendation:** Option B - let better-auth handle user creation

4. **Test query:**
   ```sql
   -- Can we get Lounge fields from main's users?
   SELECT id, email, 
          COALESCE(username, split_part(email, '@', 1)) as username,
          COALESCE(display_name, 'User') as displayName,
          subscription_tier as tier
   FROM users 
   WHERE id = 'test-user-id';
   ```

**Deliverable:** User schema mapping document + SQL query examples for common operations.

#### Task 0.3: Environment Variables Setup (1 day)

**Action Items:**
1. **Check main's `.env` file** (or `.env.example` if it exists)
2. **Document Lounge-specific env vars:**
   ```env
   # Lounge BYOK Providers
   # Note: These are NOT server-side keys, just configuration
   # Users provide their own keys via vault
   
   # Aksho Mini (free hosted model)
   AKSHO_MINI_ENDPOINT=https://api.aksho.ai/v1/mini
   AKSHO_MINI_API_KEY=<server-side-key-for-aksho-mini>
   AKSHO_MINI_RATE_LIMIT=50  # messages per 24h
   
   # Optional: Provider defaults
   ANTHROPIC_DEFAULT_MODEL=claude-3-5-sonnet-20241022
   OPENAI_DEFAULT_MODEL=gpt-4-turbo-preview
   DEEPSEEK_DEFAULT_MODEL=deepseek-chat
   ```

3. **Check for conflicts** with existing main env vars
4. **Document in README** how to set up for local development

**Deliverable:** Environment variables documentation + `.env.example` updates

#### Task 0.4: Development Environment Setup (2 days)

**Action Items:**
1. **Create development branch:**
   ```bash
   cd akshoai/
   git checkout -b feature/lounge-integration
   git push -u origin feature/lounge-integration
   ```

2. **Provision test PostgreSQL database:**
   - **Option A:** Local PostgreSQL
     ```bash
     createdb aksho_lounge_test
     export DATABASE_URL="postgresql://localhost/aksho_lounge_test"
     ```
   - **Option B:** Neon test project (recommended)
     ```bash
     # Create new Neon project "aksho-lounge-dev"
     # Copy connection string to .env.development
     ```

3. **Set up test accounts:**
   - Create 3 test users in better-auth
   - Map to Lounge dev accounts:
     - Alice → test-alice@aksho.ai
     - Bob → test-bob@aksho.ai
     - Charlie → test-charlie@aksho.ai

4. **Document backup/rollback procedure:**
   ```bash
   # Before each phase:
   pg_dump $DATABASE_URL > backup-phase-N.sql
   
   # Rollback if needed:
   psql $DATABASE_URL < backup-phase-N.sql
   ```

**Deliverable:** 
- Development branch created
- Test database provisioned
- Test accounts created
- Rollback procedures documented

#### Task 0.5: React 19.2.3 Compatibility Testing (1-2 days)

**Why Important:** Lounge uses React 19.0.0, main uses 19.2.3. Breaking changes could cause runtime errors.

**Action Items:**
1. **Create test Next.js project:**
   ```bash
   npx create-next-app@latest lounge-react-test --typescript
   cd lounge-react-test
   npm install react@19.2.3 react-dom@19.2.3
   ```

2. **Test key Lounge components:**
   - Copy `chat-interface.tsx` (82KB, most complex)
   - Copy `character-editor.tsx` (37KB)
   - Copy `lounge-main.tsx` (19KB)
   - Copy any components using React 19-specific APIs

3. **Check for:**
   - Deprecated API warnings
   - Runtime errors
   - TypeScript type errors
   - Breaking changes in hooks (useTransition, useDeferredValue, etc.)

4. **Document fixes needed:**
   - List any components that need updates
   - Note breaking changes and solutions

**Deliverable:** Compatibility report with any required component updates

#### Task 0.6: Type Namespace Strategy (1 day)

**Decision Made:** Use directory-based namespacing

**Action Items:**
1. **Create type directory structure:**
   ```bash
   mkdir -p akshoai/src/types/hangar
   mkdir -p akshoai/src/types/lounge
   ```

2. **Move existing main types:**
   ```bash
   # If main has character types in /src/types/character.ts
   mv akshoai/src/types/character.ts akshoai/src/types/hangar/character.ts
   ```

3. **Update tsconfig.json paths:**
   ```json
   {
     "compilerOptions": {
       "paths": {
         "@/types/hangar/*": ["./src/types/hangar/*"],
         "@/types/lounge/*": ["./src/types/lounge/*"]
       }
     }
   }
   ```

4. **Document import pattern:**
   ```typescript
   // CORRECT: Explicit namespace
   import type { Character as HangarCharacter } from '@/types/hangar/character'
   import type { Character as LoungeCharacter } from '@/types/lounge'
   
   // WRONG: Ambiguous
   import type { Character } from '@/types/character'
   ```

**Deliverable:** Type namespace guide with import examples

#### Task 0.7: CDN Upload Investigation (1 day)

**Action Items:**
1. **Review main's upload implementation:**
   - File: `/src/app/api/upload/route.ts` (or similar)
   - Check: R2 bucket config, AI moderation, signed URLs

2. **Review Lounge's upload needs:**
   - Character avatar uploads
   - Gallery image uploads (for gallery mode avatars)
   - Picturize generated images

3. **Verify compatibility:**
   - Can Lounge use same R2 bucket?
   - Same upload API endpoint?
   - Same AI moderation flow?

4. **Document upload flow:**
   ```
   Client → /api/upload → R2 → AI Moderation → CDN URL returned
   ```

**Deliverable:** CDN integration plan for Lounge uploads

---

### Phase 1: Database Migration & Service Layer (Weeks 1-3)

**DEPENDENCIES:** Phase 0 must be completed first.

#### Step 1.1: Create PostgreSQL Schema (Week 1)

**File:** `/src/lib/services/schema-lounge.sql`

**Create SQL schema for 11 Lounge models:**

```sql
-- ============================================
-- LOUNGE DATABASE SCHEMA
-- PostgreSQL version of Prisma SQLite models
-- ============================================

-- 1. Lounge Characters (V2 Card Spec)
CREATE TABLE lounge_characters (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  species TEXT DEFAULT 'human', -- human|monster|furry
  gender TEXT, -- male|female|futa
  tagline TEXT,
  
  -- V2 Card Spec: Subcategorized descriptions
  description_basic_info TEXT,
  description_physical TEXT,
  description_clothing TEXT,
  description_personality TEXT,
  description_background TEXT,
  legacy_description TEXT, -- For imported v1 cards
  
  -- Messages
  first_message TEXT,
  first_message_scenario TEXT,
  alternate_intros JSONB, -- [{ message, scenario }]
  
  -- Prompts
  system_prompt TEXT,
  post_history_instructions TEXT,
  
  -- Avatars
  avatar_url TEXT NOT NULL,
  avatar_mode TEXT DEFAULT 'static', -- static|gallery|emotional
  avatar_rating TEXT DEFAULT 'sfw',
  avatar_static_url TEXT, -- For static mode
  avatar_gallery_urls JSONB, -- Array of URLs for gallery mode
  avatar_emotional_mapping JSONB, -- { emotion: url } for emotional mode
  
  -- Ratings
  rating TEXT DEFAULT 'sfw',
  sumi_scale TEXT DEFAULT 'SFW',
  content_rating TEXT DEFAULT 'sfw',
  
  -- Metadata
  tags JSONB DEFAULT '[]',
  creator_id TEXT, -- References users(id) from main app
  creator_name TEXT,
  is_public BOOLEAN DEFAULT FALSE,
  is_featured BOOLEAN DEFAULT FALSE,
  published_at TIMESTAMP,
  engagement_count INTEGER DEFAULT 0,
  
  -- Configuration
  prompt_preset_id TEXT,
  content_mode TEXT,
  custom_variables JSONB,
  character_version TEXT,
  parent_character_id TEXT REFERENCES lounge_characters(id),
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_lounge_characters_creator ON lounge_characters(creator_id);
CREATE INDEX idx_lounge_characters_public ON lounge_characters(is_public);
CREATE INDEX idx_lounge_characters_featured ON lounge_characters(is_featured);
CREATE INDEX idx_lounge_characters_rating ON lounge_characters(rating);

-- 2. Lounge Chats
CREATE TABLE lounge_chats (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL, -- References users(id) from main app
  character_id TEXT REFERENCES lounge_characters(id) ON DELETE CASCADE,
  title TEXT,
  
  -- Character snapshot (frozen at chat creation)
  character_snapshot JSONB,
  
  -- Gallery mode state
  avatar_cycle_index INTEGER DEFAULT 0,
  
  -- Sonarcore tracked state
  host_state JSONB, -- { location, timeOfDay, emotion, etc. }
  
  -- Encryption
  encryption_key_hash TEXT,
  is_encrypted BOOLEAN DEFAULT FALSE,
  
  -- Sync & versioning
  version INTEGER DEFAULT 1,
  last_synced_at TIMESTAMP,
  
  -- Group chat support
  is_group BOOLEAN DEFAULT FALSE,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_lounge_chats_user ON lounge_chats(user_id);
CREATE INDEX idx_lounge_chats_character ON lounge_chats(character_id);
CREATE INDEX idx_lounge_chats_updated ON lounge_chats(updated_at DESC);
CREATE INDEX idx_lounge_chats_group ON lounge_chats(is_group);

-- 3. Lounge Messages (with branching support)
CREATE TABLE lounge_messages (
  id TEXT PRIMARY KEY,
  chat_id TEXT NOT NULL REFERENCES lounge_chats(id) ON DELETE CASCADE,
  role TEXT NOT NULL, -- user|assistant|system
  content TEXT NOT NULL,
  character_id TEXT, -- For multi-character chats
  
  -- Token tracking
  token_count INTEGER,
  model TEXT, -- Which AI model was used
  
  -- Sonarcore extracted data
  sonarcore_data JSONB, -- { location, emotion, sfx, etc. }
  
  -- Branching & editing
  parent_message_id TEXT REFERENCES lounge_messages(id),
  superseded_by_message_id TEXT REFERENCES lounge_messages(id),
  branch_index INTEGER DEFAULT 0,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_lounge_messages_chat ON lounge_messages(chat_id);
CREATE INDEX idx_lounge_messages_parent ON lounge_messages(parent_message_id);
CREATE INDEX idx_lounge_messages_created ON lounge_messages(created_at);
CREATE INDEX idx_lounge_messages_character ON lounge_messages(character_id);

-- 4. Chat Participants (for group chats)
CREATE TABLE lounge_chat_participants (
  id TEXT PRIMARY KEY,
  chat_id TEXT NOT NULL REFERENCES lounge_chats(id) ON DELETE CASCADE,
  character_id TEXT NOT NULL REFERENCES lounge_characters(id) ON DELETE CASCADE,
  participant_snapshot JSONB, -- Frozen character state
  joined_at TIMESTAMP DEFAULT NOW(),
  display_order INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  UNIQUE(chat_id, character_id)
);

CREATE INDEX idx_lounge_participants_chat ON lounge_chat_participants(chat_id);
CREATE INDEX idx_lounge_participants_character ON lounge_chat_participants(character_id);

-- 5. Lorebooks
CREATE TABLE lounge_lorebooks (
  id TEXT PRIMARY KEY,
  character_id TEXT NOT NULL REFERENCES lounge_characters(id) ON DELETE CASCADE,
  name TEXT,
  description TEXT,
  
  -- Configuration
  scan_depth INTEGER DEFAULT 100,
  token_budget INTEGER DEFAULT 2048,
  recursive_scanning BOOLEAN DEFAULT FALSE,
  
  -- Extensions
  extensions JSONB,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_lounge_lorebooks_character ON lounge_lorebooks(character_id);

-- 6. Lorebook Entries
CREATE TABLE lounge_lorebook_entries (
  id TEXT PRIMARY KEY,
  lorebook_id TEXT NOT NULL REFERENCES lounge_lorebooks(id) ON DELETE CASCADE,
  
  -- Triggers
  keys TEXT NOT NULL, -- Comma-separated trigger keywords
  secondary_keys TEXT,
  
  -- Content
  content TEXT NOT NULL,
  
  -- Behavior
  enabled BOOLEAN DEFAULT TRUE,
  case_sensitive BOOLEAN DEFAULT FALSE,
  insertion_order INTEGER DEFAULT 0,
  priority INTEGER DEFAULT 0,
  position TEXT DEFAULT 'before_char', -- before_char|after_char
  selective BOOLEAN DEFAULT FALSE,
  constant BOOLEAN DEFAULT FALSE, -- Always inject
  
  -- Metadata
  name TEXT,
  comment TEXT,
  extensions JSONB,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_lounge_lorebook_entries_lorebook ON lounge_lorebook_entries(lorebook_id);

-- 7. Prompt Presets
CREATE TABLE lounge_prompt_presets (
  id TEXT PRIMARY KEY,
  user_id TEXT, -- NULL = global preset
  name TEXT NOT NULL,
  
  -- Prompts
  main_prompt TEXT NOT NULL,
  jailbreak_prompt TEXT,
  assistant_prefill TEXT,
  impersonation_prompt TEXT,
  
  -- Generation parameters
  temperature DECIMAL(4,2), -- e.g., 0.70
  top_p DECIMAL(4,2),
  top_k INTEGER,
  max_tokens INTEGER,
  min_tokens INTEGER,
  frequency_penalty DECIMAL(4,2),
  presence_penalty DECIMAL(4,2),
  repetition_penalty DECIMAL(4,2),
  
  -- Visibility
  is_global BOOLEAN DEFAULT FALSE,
  is_public BOOLEAN DEFAULT FALSE,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_lounge_presets_user ON lounge_prompt_presets(user_id);
CREATE INDEX idx_lounge_presets_global ON lounge_prompt_presets(is_global);

-- 8. API Keys (encrypted BYOK)
CREATE TABLE lounge_api_keys (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  provider TEXT NOT NULL, -- anthropic|openai|deepseek|openrouter
  encrypted_key TEXT NOT NULL,
  key_salt TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, provider)
);

CREATE INDEX idx_lounge_api_keys_user ON lounge_api_keys(user_id);

-- 9. User Settings (Lounge-specific)
CREATE TABLE lounge_user_settings (
  user_id TEXT PRIMARY KEY,
  
  -- Provider settings
  active_provider TEXT,
  provider_configs JSONB, -- Per-provider settings
  
  -- UI settings
  theme TEXT DEFAULT 'dark',
  font_size INTEGER DEFAULT 14,
  chat_bubble_style TEXT,
  message_timestamps BOOLEAN DEFAULT TRUE,
  
  -- Privacy
  analytics_enabled BOOLEAN DEFAULT TRUE,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 10. Analytics Events
CREATE TABLE lounge_analytics_events (
  id TEXT PRIMARY KEY,
  user_id TEXT,
  event_type TEXT NOT NULL,
  event_data JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_lounge_analytics_created ON lounge_analytics_events(created_at DESC);
CREATE INDEX idx_lounge_analytics_type ON lounge_analytics_events(event_type);
CREATE INDEX idx_lounge_analytics_user ON lounge_analytics_events(user_id);

-- 11. Rate Limits
CREATE TABLE lounge_rate_limits (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  provider TEXT NOT NULL,
  window_start TIMESTAMP NOT NULL,
  request_count INTEGER DEFAULT 0,
  UNIQUE(user_id, provider, window_start)
);

CREATE INDEX idx_lounge_rate_limits_user_provider ON lounge_rate_limits(user_id, provider);
CREATE INDEX idx_lounge_rate_limits_window ON lounge_rate_limits(window_start);

-- ============================================
-- INITIAL DATA
-- ============================================

-- Insert global prompt presets
INSERT INTO lounge_prompt_presets (id, user_id, name, main_prompt, is_global, is_public) VALUES
('preset_default', NULL, 'Default', 'You are {{char}}, a character created by the user. Engage naturally in conversation.', TRUE, TRUE),
('preset_creative', NULL, 'Creative', 'You are {{char}}. Be creative, expressive, and engaging. Use vivid descriptions and emotional depth.', TRUE, TRUE);
```

**Run Migration:**
```bash
# Test database
psql $TEST_DATABASE_URL -f src/lib/services/schema-lounge.sql

# Production (later)
psql $DATABASE_URL -f src/lib/services/schema-lounge.sql
```

#### Step 1.2: Create Service Layer Following Main's Pattern (Week 2)

**CRITICAL:** Main uses raw SQL via `getPool()`, NOT ORM. Follow this pattern exactly.

**File:** `/src/lib/services/lounge-characters.ts`

```typescript
/**
 * Lounge Characters Service
 * CRUD operations using raw SQL (main's pattern)
 */

import { getPool } from './database-pool'
import type { Character } from '@/types/lounge'

// ============================================
// TYPES
// ============================================

export interface CreateCharacterInput {
  userId: string
  name: string
  species?: 'human' | 'monster' | 'furry'
  gender?: 'male' | 'female' | 'futa'
  tagline?: string
  descriptionBasicInfo?: string
  descriptionPhysical?: string
  descriptionClothing?: string
  descriptionPersonality?: string
  descriptionBackground?: string
  firstMessage?: string
  firstMessageScenario?: string
  alternateIntros?: Array<{ message: string; scenario?: string }>
  systemPrompt?: string
  postHistoryInstructions?: string
  avatarUrl: string
  avatarMode?: 'static' | 'gallery' | 'emotional'
  avatarRating?: 'sfw' | 'nsfw' | 'nsfl'
  avatarStaticUrl?: string
  avatarGalleryUrls?: string[]
  avatarEmotionalMapping?: Record<string, string>
  rating?: 'sfw' | 'nsfw' | 'nsfl'
  tags?: string[]
  isPublic?: boolean
  promptPresetId?: string
}

export interface UpdateCharacterInput {
  name?: string
  species?: 'human' | 'monster' | 'furry'
  gender?: 'male' | 'female' | 'futa'
  tagline?: string
  descriptionBasicInfo?: string
  descriptionPhysical?: string
  descriptionClothing?: string
  descriptionPersonality?: string
  descriptionBackground?: string
  firstMessage?: string
  firstMessageScenario?: string
  alternateIntros?: Array<{ message: string; scenario?: string }>
  systemPrompt?: string
  postHistoryInstructions?: string
  avatarUrl?: string
  avatarMode?: 'static' | 'gallery' | 'emotional'
  avatarRating?: 'sfw' | 'nsfw' | 'nsfl'
  avatarStaticUrl?: string
  avatarGalleryUrls?: string[]
  avatarEmotionalMapping?: Record<string, string>
  rating?: 'sfw' | 'nsfw' | 'nsfl'
  tags?: string[]
  isPublic?: boolean
  promptPresetId?: string
}

// ============================================
// HELPER: Row to Character
// ============================================

function rowToCharacter(row: any): Character {
  return {
    id: row.id,
    name: row.name,
    species: row.species,
    gender: row.gender,
    tagline: row.tagline,
    description: {
      basic: row.description_basic_info,
      physical: row.description_physical,
      clothing: row.description_clothing,
      personality: row.description_personality,
      background: row.description_background,
    },
    firstMessage: row.first_message,
    firstMessageScenario: row.first_message_scenario,
    alternateIntros: row.alternate_intros || [],
    systemPrompt: row.system_prompt,
    postHistoryInstructions: row.post_history_instructions,
    avatarUrl: row.avatar_url,
    avatarMode: row.avatar_mode,
    avatarRating: row.avatar_rating,
    avatarStaticUrl: row.avatar_static_url,
    avatarGalleryUrls: row.avatar_gallery_urls || [],
    avatarEmotionalMapping: row.avatar_emotional_mapping || {},
    rating: row.rating,
    tags: row.tags || [],
    creatorId: row.creator_id,
    creatorName: row.creator_name,
    isPublic: row.is_public,
    isFeatured: row.is_featured,
    publishedAt: row.published_at,
    engagementCount: row.engagement_count,
    promptPresetId: row.prompt_preset_id,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  }
}

// ============================================
// CRUD OPERATIONS
// ============================================

/**
 * Get all characters for a user
 */
export async function getCharacters(userId: string): Promise<Character[]> {
  const pool = getPool()
  const result = await pool.query(
    `SELECT * FROM lounge_characters 
     WHERE creator_id = $1 
     ORDER BY updated_at DESC`,
    [userId]
  )
  return result.rows.map(rowToCharacter)
}

/**
 * Get a single character by ID
 */
export async function getCharacterById(
  id: string,
  userId: string
): Promise<Character | null> {
  const pool = getPool()
  const result = await pool.query(
    `SELECT * FROM lounge_characters 
     WHERE id = $1 AND creator_id = $2`,
    [id, userId]
  )
  return result.rows[0] ? rowToCharacter(result.rows[0]) : null
}

/**
 * Create a new character
 */
export async function createCharacter(
  data: CreateCharacterInput
): Promise<Character> {
  const pool = getPool()
  const id = `char_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
  
  const result = await pool.query(
    `INSERT INTO lounge_characters (
      id, name, species, gender, tagline,
      description_basic_info, description_physical, description_clothing,
      description_personality, description_background,
      first_message, first_message_scenario, alternate_intros,
      system_prompt, post_history_instructions,
      avatar_url, avatar_mode, avatar_rating,
      avatar_static_url, avatar_gallery_urls, avatar_emotional_mapping,
      rating, tags, creator_id, is_public, prompt_preset_id,
      updated_at
    ) VALUES (
      $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
      $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, NOW()
    ) RETURNING *`,
    [
      id,
      data.name,
      data.species || 'human',
      data.gender,
      data.tagline,
      data.descriptionBasicInfo,
      data.descriptionPhysical,
      data.descriptionClothing,
      data.descriptionPersonality,
      data.descriptionBackground,
      data.firstMessage,
      data.firstMessageScenario,
      data.alternateIntros ? JSON.stringify(data.alternateIntros) : null,
      data.systemPrompt,
      data.postHistoryInstructions,
      data.avatarUrl,
      data.avatarMode || 'static',
      data.avatarRating || 'sfw',
      data.avatarStaticUrl,
      data.avatarGalleryUrls ? JSON.stringify(data.avatarGalleryUrls) : null,
      data.avatarEmotionalMapping ? JSON.stringify(data.avatarEmotionalMapping) : null,
      data.rating || 'sfw',
      JSON.stringify(data.tags || []),
      data.userId,
      data.isPublic || false,
      data.promptPresetId,
    ]
  )
  
  return rowToCharacter(result.rows[0])
}

/**
 * Update a character
 */
export async function updateCharacter(
  id: string,
  userId: string,
  updates: UpdateCharacterInput
): Promise<Character | null> {
  const pool = getPool()
  
  // Build dynamic UPDATE query
  const fields: string[] = []
  const values: any[] = []
  let paramCount = 1
  
  if (updates.name !== undefined) {
    fields.push(`name = $${paramCount++}`)
    values.push(updates.name)
  }
  if (updates.species !== undefined) {
    fields.push(`species = $${paramCount++}`)
    values.push(updates.species)
  }
  if (updates.gender !== undefined) {
    fields.push(`gender = $${paramCount++}`)
    values.push(updates.gender)
  }
  if (updates.tagline !== undefined) {
    fields.push(`tagline = $${paramCount++}`)
    values.push(updates.tagline)
  }
  if (updates.descriptionBasicInfo !== undefined) {
    fields.push(`description_basic_info = $${paramCount++}`)
    values.push(updates.descriptionBasicInfo)
  }
  if (updates.descriptionPhysical !== undefined) {
    fields.push(`description_physical = $${paramCount++}`)
    values.push(updates.descriptionPhysical)
  }
  if (updates.descriptionClothing !== undefined) {
    fields.push(`description_clothing = $${paramCount++}`)
    values.push(updates.descriptionClothing)
  }
  if (updates.descriptionPersonality !== undefined) {
    fields.push(`description_personality = $${paramCount++}`)
    values.push(updates.descriptionPersonality)
  }
  if (updates.descriptionBackground !== undefined) {
    fields.push(`description_background = $${paramCount++}`)
    values.push(updates.descriptionBackground)
  }
  if (updates.firstMessage !== undefined) {
    fields.push(`first_message = $${paramCount++}`)
    values.push(updates.firstMessage)
  }
  if (updates.avatarUrl !== undefined) {
    fields.push(`avatar_url = $${paramCount++}`)
    values.push(updates.avatarUrl)
  }
  if (updates.rating !== undefined) {
    fields.push(`rating = $${paramCount++}`)
    values.push(updates.rating)
  }
  if (updates.tags !== undefined) {
    fields.push(`tags = $${paramCount++}`)
    values.push(JSON.stringify(updates.tags))
  }
  if (updates.isPublic !== undefined) {
    fields.push(`is_public = $${paramCount++}`)
    values.push(updates.isPublic)
  }
  
  // Always update timestamp
  fields.push(`updated_at = NOW()`)
  
  if (fields.length === 1) {
    // Only timestamp updated, no actual changes
    return getCharacterById(id, userId)
  }
  
  // Add WHERE clause parameters
  values.push(id, userId)
  
  const result = await pool.query(
    `UPDATE lounge_characters 
     SET ${fields.join(', ')}
     WHERE id = $${paramCount++} AND creator_id = $${paramCount++}
     RETURNING *`,
    values
  )
  
  return result.rows[0] ? rowToCharacter(result.rows[0]) : null
}

/**
 * Delete a character
 */
export async function deleteCharacter(
  id: string,
  userId: string
): Promise<boolean> {
  const pool = getPool()
  const result = await pool.query(
    `DELETE FROM lounge_characters 
     WHERE id = $1 AND creator_id = $2`,
    [id, userId]
  )
  return (result.rowCount ?? 0) > 0
}

/**
 * Get public/featured characters (for discovery)
 */
export async function getFeaturedCharacters(limit = 20): Promise<Character[]> {
  const pool = getPool()
  const result = await pool.query(
    `SELECT * FROM lounge_characters 
     WHERE is_public = TRUE AND is_featured = TRUE
     ORDER BY engagement_count DESC, updated_at DESC
     LIMIT $1`,
    [limit]
  )
  return result.rows.map(rowToCharacter)
}
```

**Similar services to create:**

1. **`/src/lib/services/lounge-chats.ts`** - Chat CRUD with character snapshots
2. **`/src/lib/services/lounge-messages.ts`** - Message CRUD with branching support
3. **`/src/lib/services/lounge-lorebooks.ts`** - Lorebook & entry CRUD
4. **`/src/lib/services/lounge-api-keys.ts`** - Encrypted BYOK key storage
5. **`/src/lib/services/lounge-presets.ts`** - Prompt preset management

**Pattern for all services:**
- Use `getPool()` from `./database-pool`
- Use parameterized queries (`$1`, `$2`, etc.)
- Parse JSON columns when returning data
- Stringify JSON when inserting/updating
- Include `userId` in all queries for security
- Return null/empty array instead of throwing on not found

#### Step 1.3: Data Migration Script (Week 2-3)

**File:** `/scripts/migrate-lounge-data.ts`

```typescript
/**
 * Migrate Lounge dev data from SQLite to PostgreSQL
 * Run: tsx scripts/migrate-lounge-data.ts
 */

import Database from 'better-sqlite3'
import { getPool } from '../src/lib/services/database-pool'
import * as loungeCharacters from '../src/lib/services/lounge-characters'
import * as loungeChats from '../src/lib/services/lounge-chats'
import * as loungeMessages from '../src/lib/services/lounge-messages'

const SQLITE_PATH = 'lounge/aksho-lounge-dev/prisma/dev.db'

async function main() {
  console.log('🚀 Starting Lounge data migration...')
  
  // 1. Open SQLite database
  const sqlite = new Database(SQLITE_PATH, { readonly: true })
  
  try {
    // 2. Migrate users (map to main's users)
    console.log('\n📦 Migrating users...')
    const users = sqlite.prepare('SELECT * FROM users').all()
    console.log(`Found ${users.length} users`)
    
    // Map dev users to real user IDs (from Phase 0 setup)
    const userMap = new Map([
      ['alice-id', 'real-alice-user-id'],
      ['bob-id', 'real-bob-user-id'],
      ['charlie-id', 'real-charlie-user-id'],
    ])
    
    // 3. Migrate characters
    console.log('\n📦 Migrating characters...')
    const characters = sqlite.prepare('SELECT * FROM characters').all()
    console.log(`Found ${characters.length} characters`)
    
    for (const char of characters) {
      const realUserId = userMap.get(char.creator_id) || char.creator_id
      
      try {
        await loungeCharacters.createCharacter({
          userId: realUserId,
          name: char.name,
          species: char.species,
          gender: char.gender,
          tagline: char.tagline,
          descriptionBasicInfo: char.description_basic_info,
          descriptionPhysical: char.description_physical,
          descriptionClothing: char.description_clothing,
          descriptionPersonality: char.description_personality,
          descriptionBackground: char.description_background,
          firstMessage: char.first_message,
          firstMessageScenario: char.first_message_scenario,
          alternateIntros: char.alternate_intros ? JSON.parse(char.alternate_intros) : undefined,
          systemPrompt: char.system_prompt,
          postHistoryInstructions: char.post_history_instructions,
          avatarUrl: char.avatar_url,
          avatarMode: char.avatar_mode,
          avatarRating: char.avatar_rating,
          rating: char.rating,
          tags: char.tags ? JSON.parse(char.tags) : [],
          isPublic: char.is_public,
        })
        console.log(`✅ Migrated character: ${char.name}`)
      } catch (error) {
        console.error(`❌ Failed to migrate character ${char.name}:`, error)
      }
    }
    
    // 4. Migrate chats
    console.log('\n📦 Migrating chats...')
    const chats = sqlite.prepare('SELECT * FROM chats').all()
    console.log(`Found ${chats.length} chats`)
    
    for (const chat of chats) {
      const realUserId = userMap.get(chat.user_id) || chat.user_id
      
      try {
        await loungeChats.createChat({
          userId: realUserId,
          characterId: chat.character_id,
          title: chat.title,
          characterSnapshot: chat.character_snapshot ? JSON.parse(chat.character_snapshot) : undefined,
          isGroup: chat.is_group,
        })
        console.log(`✅ Migrated chat: ${chat.title || chat.id}`)
      } catch (error) {
        console.error(`❌ Failed to migrate chat ${chat.id}:`, error)
      }
    }
    
    // 5. Migrate messages (handle branching carefully)
    console.log('\n📦 Migrating messages...')
    const messages = sqlite.prepare('SELECT * FROM messages ORDER BY created_at ASC').all()
    console.log(`Found ${messages.length} messages`)
    
    for (const msg of messages) {
      try {
        await loungeMessages.createMessage({
          chatId: msg.chat_id,
          role: msg.role,
          content: msg.content,
          characterId: msg.character_id,
          tokenCount: msg.token_count,
          model: msg.model,
          sonarcoreData: msg.sonarcore_data ? JSON.parse(msg.sonarcore_data) : undefined,
          parentMessageId: msg.parent_message_id,
          supersededByMessageId: msg.superseded_by_message_id,
          branchIndex: msg.branch_index,
        })
      } catch (error) {
        console.error(`❌ Failed to migrate message ${msg.id}:`, error)
      }
    }
    console.log(`✅ Migrated ${messages.length} messages`)
    
    console.log('\n✅ Migration complete!')
    
  } catch (error) {
    console.error('❌ Migration failed:', error)
    throw error
  } finally {
    sqlite.close()
  }
}

main().catch(console.error)
```

**Run Migration:**
```bash
# Install dependencies
npm install better-sqlite3 tsx

# Run migration
tsx scripts/migrate-lounge-data.ts
```

---

### Phase 2: API Routes with Inline Auth (Week 4)

**DEPENDENCIES:** Phase 1 must be completed first.

**Create 15 API route handlers following main's App Router pattern.**

#### Example: Characters API

**File:** `/src/app/api/lounge/characters/route.ts`

```typescript
/**
 * Lounge Characters API
 * GET/POST /api/lounge/characters
 */

import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@/lib/auth'
import * as loungeCharacters from '@/lib/services/lounge-characters'

// ============================================
// GET /api/lounge/characters
// List user's characters
// ============================================

export async function GET(request: NextRequest) {
  try {
    // Auth check (inline - main's pattern)
    const session = await auth.api.getSession({ headers: request.headers })
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    const userId = session.user.id
    
    // Get characters
    const characters = await loungeCharacters.getCharacters(userId)
    
    return NextResponse.json({
      characters,
      count: characters.length,
    })
  } catch (error) {
    console.error('GET /api/lounge/characters error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch characters' },
      { status: 500 }
    )
  }
}

// ============================================
// POST /api/lounge/characters
// Create new character
// ============================================

export async function POST(request: NextRequest) {
  try {
    // Auth check
    const session = await auth.api.getSession({ headers: request.headers })
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    const userId = session.user.id
    
    // Parse body
    const body = await request.json()
    
    // Validation
    if (!body.name || !body.avatarUrl) {
      return NextResponse.json(
        { error: 'Name and avatarUrl are required' },
        { status: 400 }
      )
    }
    
    // Create character
    const character = await loungeCharacters.createCharacter({
      userId,
      ...body,
    })
    
    // Gamification hook (Phase 4)
    // await onCharacterEvent('created', userId, character.id)
    
    return NextResponse.json(character, { status: 201 })
  } catch (error) {
    console.error('POST /api/lounge/characters error:', error)
    return NextResponse.json(
      { error: 'Failed to create character' },
      { status: 500 }
    )
  }
}
```

**File:** `/src/app/api/lounge/characters/[id]/route.ts`

```typescript
/**
 * Lounge Character Detail API
 * GET/PATCH/DELETE /api/lounge/characters/[id]
 */

import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@/lib/auth'
import * as loungeCharacters from '@/lib/services/lounge-characters'

// ============================================
// GET /api/lounge/characters/[id]
// ============================================

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await auth.api.getSession({ headers: request.headers })
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    const userId = session.user.id
    const { id } = params
    
    const character = await loungeCharacters.getCharacterById(id, userId)
    
    if (!character) {
      return NextResponse.json(
        { error: 'Character not found' },
        { status: 404 }
      )
    }
    
    return NextResponse.json(character)
  } catch (error) {
    console.error('GET /api/lounge/characters/[id] error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch character' },
      { status: 500 }
    )
  }
}

// ============================================
// PATCH /api/lounge/characters/[id]
// ============================================

export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await auth.api.getSession({ headers: request.headers })
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    const userId = session.user.id
    const { id } = params
    
    const body = await request.json()
    
    const character = await loungeCharacters.updateCharacter(id, userId, body)
    
    if (!character) {
      return NextResponse.json(
        { error: 'Character not found' },
        { status: 404 }
      )
    }
    
    return NextResponse.json(character)
  } catch (error) {
    console.error('PATCH /api/lounge/characters/[id] error:', error)
    return NextResponse.json(
      { error: 'Failed to update character' },
      { status: 500 }
    )
  }
}

// ============================================
// DELETE /api/lounge/characters/[id]
// ============================================

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await auth.api.getSession({ headers: request.headers })
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    const userId = session.user.id
    const { id } = params
    
    const deleted = await loungeCharacters.deleteCharacter(id, userId)
    
    if (!deleted) {
      return NextResponse.json(
        { error: 'Character not found' },
        { status: 404 }
      )
    }
    
    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('DELETE /api/lounge/characters/[id] error:', error)
    return NextResponse.json(
      { error: 'Failed to delete character' },
      { status: 500 }
    )
  }
}
```

**Complete list of routes to create:**

1. ✅ `GET/POST /api/lounge/characters`
2. ✅ `GET/PATCH/DELETE /api/lounge/characters/[id]`
3. ⬜ `GET/POST /api/lounge/chats`
4. ⬜ `GET/PATCH/DELETE /api/lounge/chats/[chatId]`
5. ⬜ `GET/POST /api/lounge/chats/[chatId]/messages`
6. ⬜ `PATCH/DELETE /api/lounge/chats/[chatId]/messages/[messageId]`
7. ⬜ `POST /api/lounge/chats/group` (create group chat)
8. ⬜ `GET/POST /api/lounge/chats/[chatId]/participants`
9. ⬜ `POST /api/lounge/chats/[chatId]/convert-to-group`
10. ⬜ `POST /api/lounge/picturize`
11. ⬜ `GET/POST /api/lounge/api-keys`
12. ⬜ `GET /api/lounge/presets` (prompt presets)

**Pattern for all routes:**
- Start with inline auth check
- Use service layer for database operations
- Return proper HTTP status codes
- Catch and log errors
- Validate input when needed

---

### Phase 3: Code Integration (Weeks 5-6)

**DEPENDENCIES:** Phase 2 must be completed first.

#### Step 3.1: Copy Framework-Agnostic Services (Week 5)

**These services have NO database dependencies** - copy as-is:

**Source → Destination:**
```bash
# Business logic services (no DB calls)
cp lounge/aksho-lounge-dev/src/services/chatEngine.ts akshoai/src/lib/lounge/
cp lounge/aksho-lounge-dev/src/services/picturize.ts akshoai/src/lib/lounge/
cp lounge/aksho-lounge-dev/src/services/ai-providers.ts akshoai/src/lib/lounge/
cp lounge/aksho-lounge-dev/src/services/sonarcoreComputation.ts akshoai/src/lib/lounge/
cp lounge/aksho-lounge-dev/src/services/tokenCounter.ts akshoai/src/lib/lounge/
cp lounge/aksho-lounge-dev/src/services/avatarSelection.ts akshoai/src/lib/lounge/
cp lounge/aksho-lounge-dev/src/services/characterCardImport.ts akshoai/src/lib/lounge/
cp lounge/aksho-lounge-dev/src/services/promptPresets.ts akshoai/src/lib/lounge/
cp lounge/aksho-lounge-dev/src/services/personas.ts akshoai/src/lib/lounge/
cp lounge/aksho-lounge-dev/src/services/encryption.ts akshoai/src/lib/lounge/
# ... copy all services without DB dependencies
```

**Update imports in copied files:**
```typescript
// Before (Lounge)
import type { Character } from '@/types/lounge'

// After (Main)
import type { Character } from '@/types/lounge'  // Same!
```

**Most services won't need changes** - they're pure business logic.

#### Step 3.2: Copy & Adapt Components (Week 5-6)

**Replace 3 stubs + add 31 new components:**

```bash
# Replace existing stubs
cp lounge/aksho-lounge-dev/src/components/lounge/lounge-main.tsx akshoai/src/components/lounge/
cp lounge/aksho-lounge-dev/src/components/lounge/chat-interface.tsx akshoai/src/components/lounge/
cp lounge/aksho-lounge-dev/src/components/lounge/lounge-landing.tsx akshoai/src/components/lounge/

# Add new components
cp lounge/aksho-lounge-dev/src/components/lounge/character-editor.tsx akshoai/src/components/lounge/
cp lounge/aksho-lounge-dev/src/components/lounge/character-card.tsx akshoai/src/components/lounge/
cp lounge/aksho-lounge-dev/src/components/lounge/message-bubble.tsx akshoai/src/components/lounge/
cp lounge/aksho-lounge-dev/src/components/lounge/message-list.tsx akshoai/src/components/lounge/
cp lounge/aksho-lounge-dev/src/components/lounge/chat-input.tsx akshoai/src/components/lounge/
cp lounge/aksho-lounge-dev/src/components/lounge/provider-selector.tsx akshoai/src/components/lounge/
# ... copy all 34 components
```

**Required updates in components:**

1. **Remove dev-auth imports:**
   ```typescript
   // Before (Lounge)
   import { useCachedSession } from '@/lib/dev-auth'
   
   // After (Main)
   import { useCachedSession } from '@/lib/auth-client' // Main's hook
   ```

2. **Update API endpoint paths:**
   ```typescript
   // All API calls should use /api/lounge/ prefix
   fetch('/api/lounge/characters')  // Correct
   fetch('/api/characters')          // Wrong
   ```

3. **Update service imports:**
   ```typescript
   // Before
   import { chatEngine } from '@/services/chatEngine'
   
   // After
   import { chatEngine } from '@/lib/lounge/chatEngine'
   ```

4. **Update type imports:**
   ```typescript
   // Before
   import type { Character } from '@/types/lounge'
   
   // After
   import type { Character } from '@/types/lounge' // Same path!
   ```

#### Step 3.3: Copy Store (Week 6)

**File:** Copy `lounge-store.ts` to `/src/store/lounge-store.ts`

**Critical updates needed:**

```typescript
// Before (Lounge - dev auth)
import { useCachedSession } from '@/lib/dev-auth'

// After (Main - real auth)
import { useCachedSession } from '@/lib/auth-client'

// Before (API calls)
fetch('/api/characters')

// After (API calls with /lounge/ prefix)
fetch('/api/lounge/characters')
```

**Store structure remains same** - Zustand patterns are compatible.

#### Step 3.4: Copy Types (Week 6)

**Create directory:** `/src/types/lounge/`

```bash
mkdir -p akshoai/src/types/lounge
cp lounge/aksho-lounge-dev/src/types/lounge.ts akshoai/src/types/lounge/index.ts
```

**No changes needed** - types are framework-agnostic.

#### Step 3.5: Update Dependencies

**File:** `/akshoai/package.json`

**Add to dependencies:**
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

**Remove (no longer needed):**
- **DO NOT add Prisma** - we migrated to raw SQL

**Install:**
```bash
cd akshoai
npm install
```

#### Step 3.6: Update Page Routes

**File:** `/src/app/lounge/page.tsx`

```typescript
'use client'

import { useEffect, useRef } from 'react'
import { LoungeMain } from '@/components/lounge/lounge-main' // Use new component
import { useAchievements, ACHIEVEMENTS } from '@/hooks/useAchievements'

export default function LoungePage() {
  const { grantAchievement } = useAchievements()
  const hasTriggered = useRef(false)

  useEffect(() => {
    if (!hasTriggered.current) {
      hasTriggered.current = true
      grantAchievement(ACHIEVEMENTS.LOUNGE)
    }
  }, [grantAchievement])

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-purple-950 via-blue-950 to-black">
      <main className="flex-1 pt-24 pb-20">
        <LoungeMain />
      </main>
    </div>
  )
}
```

**Create:** `/src/app/lounge/chat/[chatId]/page.tsx`

```typescript
'use client'

import { ChatInterface } from '@/components/lounge/chat-interface'

export default function ChatPage({ params }: { params: { chatId: string } }) {
  return (
    <div className="h-screen flex flex-col">
      <ChatInterface chatId={params.chatId} />
    </div>
  )
}
```

**Create:** `/src/app/lounge/swipy/page.tsx`

```typescript
'use client'

import { SwipyInterface } from '@/components/lounge/swipy-interface'

export default function SwipyPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-950 via-blue-950 to-black">
      <SwipyInterface />
    </div>
  )
}
```

---

### Phase 4: Feature Bridges (Week 6-7)

**DEPENDENCIES:** Phase 3 must be completed first.

#### Bridge 4.1: Hangar → Lounge Character Export

**File:** `/src/lib/bridges/hangar-lounge-bridge.ts`

```typescript
import * as loungeCharacters from '@/lib/services/lounge-characters'
import type { Character as HangarCharacter } from '@/types/hangar/character'
import type { Character as LoungeCharacter } from '@/types/lounge'

/**
 * Convert Hangar tag system to Lounge V2 character card
 */
export async function exportHangarToLounge(
  hangarCharacter: HangarCharacter,
  userId: string
): Promise<LoungeCharacter> {
  // Generate descriptions from 480+ tags
  const descriptions = {
    basic: generateBasicFromTags(hangarCharacter.tags),
    physical: generatePhysicalFromTags(hangarCharacter.tags),
    clothing: generateClothingFromTags(hangarCharacter.tags),
    personality: generatePersonalityFromTags(hangarCharacter.tags),
    background: generateBackgroundFromTags(hangarCharacter.tags),
  }
  
  // Create in Lounge
  const loungeChar = await loungeCharacters.createCharacter({
    userId,
    name: hangarCharacter.name,
    species: hangarCharacter.species,
    gender: hangarCharacter.gender,
    descriptionBasicInfo: descriptions.basic,
    descriptionPhysical: descriptions.physical,
    descriptionClothing: descriptions.clothing,
    descriptionPersonality: descriptions.personality,
    descriptionBackground: descriptions.background,
    avatarUrl: hangarCharacter.avatarUrl,
    rating: hangarCharacter.rating,
    tags: hangarCharacter.tags.map(t => t.name),
  })
  
  return loungeChar
}

function generateBasicFromTags(tags: any[]): string {
  // Parse occupation, age, etc. from tags
  const occupation = tags.find(t => t.category === 'occupation')?.name
  const age = tags.find(t => t.category === 'age')?.name
  
  return `${occupation ? `Works as ${occupation}.` : ''} ${age ? `${age} years old.` : ''}`.trim()
}

function generatePhysicalFromTags(tags: any[]): string {
  const bodyType = tags.find(t => t.category === 'body_type')?.name
  const height = tags.find(t => t.category === 'height')?.name
  const hairColor = tags.find(t => t.category === 'hair_color')?.name
  const eyeColor = tags.find(t => t.category === 'eye_color')?.name
  
  const parts = []
  if (height) parts.push(`${height} height`)
  if (bodyType) parts.push(`${bodyType} build`)
  if (hairColor) parts.push(`${hairColor} hair`)
  if (eyeColor) parts.push(`${eyeColor} eyes`)
  
  return parts.join(', ') + '.'
}

// ... similar functions for clothing, personality, background
```

**Add button to Hangar UI:**

**File:** `/src/components/hangar/character-actions.tsx` (if exists, or add to character display)

```typescript
import { exportHangarToLounge } from '@/lib/bridges/hangar-lounge-bridge'
import { useRouter } from 'next/navigation'

export function CharacterActions({ character }: { character: HangarCharacter }) {
  const router = useRouter()
  
  async function handleExportToLounge() {
    try {
      const loungeChar = await exportHangarToLounge(character, userId)
      router.push(`/lounge/chat/new?characterId=${loungeChar.id}`)
    } catch (error) {
      console.error('Failed to export to Lounge:', error)
    }
  }
  
  return (
    <button
      onClick={handleExportToLounge}
      className="btn-primary"
    >
      💬 Chat with Character
    </button>
  )
}
```

#### Bridge 4.2: Lounge Picturize → Atelier API

**File:** `/src/lib/bridges/atelier-picturize-bridge.ts`

```typescript
import type { Character } from '@/types/lounge'
import type { SonarcoreData } from '@/lib/lounge/sonarcore'
import type { PicturizeIntent } from '@/lib/lounge/picturize'

/**
 * Generate image for chat via Atelier
 */
export async function generateChatImage(
  character: Character,
  sonarcore: SonarcoreData,
  intent: PicturizeIntent
): Promise<string> {
  // Build prompt from character + context
  const prompt = buildPrompt(character, sonarcore, intent)
  
  // Call Atelier API
  const response = await fetch('/api/atelier/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      workflow: 'character-selfie',
      prompt,
      negativePrompt: 'low quality, blurry',
      steps: 30,
      cfg: 7,
      // ... other Atelier params
    }),
  })
  
  if (!response.ok) {
    throw new Error('Image generation failed')
  }
  
  const { imageUrl } = await response.json()
  return imageUrl
}

function buildPrompt(
  character: Character,
  sonarcore: SonarcoreData,
  intent: PicturizeIntent
): string {
  const parts = [
    // Character appearance
    character.description.physical,
    character.description.clothing,
    
    // Context from sonarcore
    sonarcore.location && `in ${sonarcore.location}`,
    sonarcore.timeOfDay && `${sonarcore.timeOfDay}`,
    sonarcore.emotion && `${sonarcore.emotion} expression`,
    
    // Intent
    intent.activity && `${intent.activity}`,
    intent.pose && `${intent.pose}`,
  ]
  
  return parts.filter(Boolean).join(', ')
}
```

**Hook into Lounge picturize service:**

**File:** `/src/lib/lounge/picturize.ts` (update existing)

```typescript
// Add import
import { generateChatImage } from '@/lib/bridges/atelier-picturize-bridge'

// In picturize function:
export async function handlePicturizeRequest(
  message: string,
  character: Character,
  sonarcore: SonarcoreData
): Promise<string | null> {
  const intent = detectIntent(message)
  if (!intent) return null
  
  // Call Atelier via bridge
  const imageUrl = await generateChatImage(character, sonarcore, intent)
  return imageUrl
}
```

#### Bridge 4.3: Lounge → Gamification System

**File:** `/src/lib/bridges/lounge-gamification-bridge.ts`

```typescript
import { achievementService } from '@/lib/services/achievement-service'
import { addMiles } from '@/lib/services/miles-service'

/**
 * Hook Lounge events into gamification system
 */
export async function onLoungeEvent(
  event: 'first_visit' | 'first_chat' | 'message_sent' | 'character_created',
  userId: string,
  metadata?: Record<string, any>
) {
  switch (event) {
    case 'first_visit':
      await achievementService.emit(userId, 'page_visit', {
        page: '/lounge',
      })
      break
    
    case 'first_chat':
      await achievementService.emit(userId, 'action', {
        action: 'first_chat',
        characterId: metadata?.characterId,
      })
      await addMiles(userId, 10, 'First chat created')
      break
    
    case 'message_sent':
      await achievementService.emit(userId, 'action', {
        action: 'chat_message',
      })
      // Grant 1 mile per message (service handles daily limit)
      await addMiles(userId, 1, 'Chat message sent')
      break
    
    case 'character_created':
      await achievementService.emit(userId, 'action', {
        action: 'character_created',
        characterId: metadata?.characterId,
      })
      await addMiles(userId, 5, 'Character created')
      break
  }
}
```

**Hook into Lounge store actions:**

**File:** `/src/store/lounge-store.ts` (update)

```typescript
import { onLoungeEvent } from '@/lib/bridges/lounge-gamification-bridge'

// In sendMessage action:
async sendMessage(content: string) {
  // ... existing logic
  
  const result = await sendMessageAPI(content)
  
  // Gamification hook
  await onLoungeEvent('message_sent', userId)
  
  return result
}

// In createChat action:
async createChat(characterId: string) {
  // ... existing logic
  
  const chat = await createChatAPI(characterId)
  
  // Gamification hook
  await onLoungeEvent('first_chat', userId, { characterId })
  
  return chat
}
```

---

### Phase 5: Testing & Polish (Week 7-8)

**DEPENDENCIES:** Phase 4 must be completed first.

#### Test 5.1: Integration Testing

**Manual Test Checklist:**

**Character Creation & Export:**
- [ ] Create character in Hangar
- [ ] Export to Lounge via "Chat with Character" button
- [ ] Verify character appears in Lounge
- [ ] Verify tags converted to descriptions correctly

**Chat Functionality:**
- [ ] Start new chat with character
- [ ] Send user message
- [ ] Receive AI response (BYOK provider)
- [ ] Test all providers: Anthropic, OpenAI, DeepSeek, OpenRouter
- [ ] Test Aksho Mini free model
- [ ] Verify token counting accurate
- [ ] Verify rate limiting (50 msgs/24h for Aksho Mini)

**Message Branching:**
- [ ] Send message
- [ ] Create alternate timeline (branch)
- [ ] Navigate between branches
- [ ] Verify message lineage preserved

**Sonarcore:**
- [ ] Send messages with location mentions
- [ ] Verify location extracted correctly
- [ ] Send messages with emotions
- [ ] Verify emotion detected
- [ ] Check performance (<5ms for 5 messages)

**Picturize:**
- [ ] Send "send me a selfie" message
- [ ] Verify image generation triggered
- [ ] Check image prompt quality
- [ ] Verify image appears in chat

**Dynamic Avatars:**
- [ ] Test static mode
- [ ] Test gallery mode (avatar cycles on replies)
- [ ] Test emotional mode (avatar changes with emotion)

**Gamification:**
- [ ] Visit /lounge for first time
- [ ] Verify "LOUNGE" achievement granted
- [ ] Create first chat
- [ ] Verify "FIRST_CHAT" achievement granted
- [ ] Verify 10 miles awarded
- [ ] Send chat message
- [ ] Verify 1 mile awarded

**Authentication:**
- [ ] Log out
- [ ] Try accessing /lounge
- [ ] Verify redirect to auth
- [ ] Log in
- [ ] Verify can access Lounge
- [ ] Verify only own characters/chats visible

#### Test 5.2: Performance Validation

**Bundle Size Check:**
```bash
# Build production
npm run build

# Check bundle size
ls -lh .next/static/chunks/

# Verify Lounge impact <500KB
```

**SSR Compatibility:**
```bash
# Test build
npm run build

# Test start
npm run start

# Navigate to /lounge
# Check for hydration errors in console
```

**Database Performance:**
```sql
-- Check query performance
EXPLAIN ANALYZE SELECT * FROM lounge_characters WHERE creator_id = 'user-id';
EXPLAIN ANALYZE SELECT * FROM lounge_messages WHERE chat_id = 'chat-id' ORDER BY created_at;

-- Verify indices used
```

**Sonarcore Performance:**
```typescript
// Add timing to sonarcore computation
console.time('sonarcore')
const data = await computeSonarcore(messages)
console.timeEnd('sonarcore')
// Should be <5ms for 5 messages
```

#### Test 5.3: Edge Cases

**Long Chat History:**
- [ ] Create chat with 1000+ messages
- [ ] Verify pagination works
- [ ] Verify virtualization (no lag scrolling)
- [ ] Verify token context truncation

**Message Branching:**
- [ ] Create 10+ branches
- [ ] Navigate all branches
- [ ] Verify no orphaned messages

**API Key Encryption:**
- [ ] Add API key
- [ ] Restart browser
- [ ] Verify key persists (encrypted)
- [ ] Delete key
- [ ] Verify removed

**Character with No Avatar:**
- [ ] Create character with missing avatarUrl
- [ ] Verify fallback avatar shown

**Rate Limiting:**
- [ ] Send 50 messages with Aksho Mini
- [ ] Verify 51st blocked
- [ ] Wait 24 hours (or adjust timestamp in DB)
- [ ] Verify reset

#### Test 5.4: Rollback Testing

**Test rollback procedure for each phase:**

```bash
# Rollback Phase 5 (if testing fails)
git reset --hard origin/main
psql $DATABASE_URL < backup-phase-4.sql

# Rollback Phase 4 (if bridge integration fails)
git reset --hard <phase-3-commit>
# No DB changes in Phase 4, only code

# Rollback Phase 3 (if code integration fails)
git reset --hard <phase-2-commit>
# No DB changes in Phase 3, only code

# Rollback Phase 2 (if API routes fail)
git reset --hard <phase-1-commit>
# No DB changes in Phase 2, only code

# Rollback Phase 1 (if DB migration fails)
psql $DATABASE_URL < backup-phase-0.sql
git reset --hard origin/main
```

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
  },
  "devDependencies": {
    "better-sqlite3": "^9.0.0",
    "tsx": "^4.21.0"
  }
}
```

### tsconfig.json Path Aliases
```json
{
  "compilerOptions": {
    "paths": {
      "@/types/hangar/*": ["./src/types/hangar/*"],
      "@/types/lounge/*": ["./src/types/lounge/*"],
      "@/lib/lounge/*": ["./src/lib/lounge/*"]
    }
  }
}
```

### Environment Variables
```env
# Add to .env

# Aksho Mini (free hosted model)
AKSHO_MINI_ENDPOINT=https://api.aksho.ai/v1/mini
AKSHO_MINI_API_KEY=<server-side-key>
AKSHO_MINI_RATE_LIMIT=50

# Optional: Default models
ANTHROPIC_DEFAULT_MODEL=claude-3-5-sonnet-20241022
OPENAI_DEFAULT_MODEL=gpt-4-turbo-preview
DEEPSEEK_DEFAULT_MODEL=deepseek-chat
```

---

## Risk Assessment (UPDATED)

### High Risk
1. **SQL Migration Complexity** - 11 models, branching messages, JSON columns
   - **Mitigation:** Extensive testing in Phase 1, backup before each phase
   
2. **User Schema Mismatch** - Different field names, types
   - **Mitigation:** Phase 0 mapping document, test queries before Phase 1

3. **Type System Conflicts** - Same names, different shapes
   - **Mitigation:** Directory namespace (completed in Phase 0)

### Medium Risk
1. **Auth Integration** - Inline pattern in 15 routes
   - **Mitigation:** Test 1-2 routes first, then replicate pattern

2. **Component Compatibility** - React 19.0.0 → 19.2.3
   - **Mitigation:** Phase 0 compatibility testing

3. **Bundle Size** - 34 components + 30 services
   - **Mitigation:** Lazy loading, code splitting, verify in Phase 5

### Low Risk
1. **UI/UX** - Both use Aksho design system
   - **Mitigation:** Visual review in Phase 5

2. **Service Migration** - Framework-agnostic code
   - **Mitigation:** Copy as-is, minimal changes needed

---

## Success Metrics

### Functional Requirements
- ✅ All 34 Lounge components integrated
- ✅ All 15 API routes working with better-auth
- ✅ Hangar characters can be exported and chatted with
- ✅ BYOK API keys work with all 4 providers
- ✅ Aksho Mini free model works (50 msgs/24h limit)
- ✅ Sonarcore extracts context accurately
- ✅ Message branching maintains lineage
- ✅ Picturize generates images from context
- ✅ Gamification hooks award achievements/miles

### Technical Requirements
- ✅ Single database (PostgreSQL with raw SQL)
- ✅ Unified auth (better-auth inline pattern)
- ✅ Bundle size increase <500KB
- ✅ No SSR breaking changes
- ✅ Type safety maintained (namespaced types)
- ✅ All tests passing

### Quality Requirements
- ✅ No regressions in existing features (Hangar, Atelier, gamification)
- ✅ Performance meets expectations (Sonarcore <5ms, DB queries <50ms)
- ✅ User data properly isolated (userId in all queries)
- ✅ Error handling graceful (try/catch in all routes)
- ✅ Loading states smooth (optimistic updates in store)

---

## Timeline Estimate (REVISED)

| Phase | Duration | Effort | Dependencies |
|-------|----------|--------|--------------|
| **Phase 0:** Prerequisites | 1 week | 24-32 hrs | None (BLOCKING) |
| **Phase 1:** Database + Services | 2-3 weeks | 60-80 hrs | Phase 0 |
| **Phase 2:** API Routes | 1 week | 16-20 hrs | Phase 1 |
| **Phase 3:** Code Integration | 1-2 weeks | 20-28 hrs | Phase 2 |
| **Phase 4:** Feature Bridges | 3-5 days | 12-16 hrs | Phase 3 |
| **Phase 5:** Testing & Polish | 1-2 weeks | 16-24 hrs | Phase 4 |
| **TOTAL** | **7-9 weeks** | **148-200 hrs** | Sequential |

**WITH 30% CONTINGENCY BUFFER:** 9-12 weeks, 192-260 hours

**Recommended Team:**
- 1 Backend Engineer (database migration, API routes)
- 1 Frontend Engineer (components, store)
- 1 Full-Stack Engineer (bridges, testing)

**Critical Path:**
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 (all sequential)

---

## Rollback Strategy

### Per-Phase Rollback

**Before Each Phase:**
```bash
# Create backup
pg_dump $DATABASE_URL > backup-phase-N.sql
git commit -m "Pre-phase N checkpoint"
git tag phase-N-start
```

**Rollback Procedure:**
```bash
# Code rollback
git reset --hard phase-N-start
git clean -fd

# Database rollback
psql $DATABASE_URL < backup-phase-N.sql
```

### Emergency Rollback (Production)

**If critical bug found in production:**

```bash
# 1. Revert deployment
vercel rollback

# 2. Database rollback (if schema changed)
psql $PROD_DATABASE_URL < backup-pre-lounge.sql

# 3. Git revert
git revert <lounge-merge-commit>
git push origin main

# 4. Redeploy
vercel --prod
```

**Estimated Downtime:** <5 minutes (code), <30 minutes (with DB rollback)

---

## Next Steps

1. **✅ Review and approve this revised plan** - Stakeholder sign-off
2. **✅ Phase 0 Task Assignment** - Assign each prerequisite task
3. **🚨 Phase 0 Execution** - MUST complete before Phase 1
4. **📋 Create tracking board** - GitHub project with milestones
5. **🎯 Phase 1 Kickoff** - Start database migration after Phase 0 complete

---

## Appendix: Validation Summary

### What Was Validated

✅ **Main app database pattern:** Raw SQL via `@neondatabase/serverless`, NOT Drizzle ORM  
✅ **Directory structure:** Flat `/src/{lib,components,store}/`, NOT `/src/features/`  
✅ **Auth pattern:** Inline `auth.api.getSession()` in routes, NOT middleware  
✅ **Existing Lounge stubs:** 3 components in `/src/components/lounge/`, NO API routes  
✅ **React versions:** Main 19.2.3, Lounge 19.0.0 (compatibility testing needed)  
✅ **Service pattern:** `getPool().query()` with parameterized SQL  
✅ **Component count:** 34 Lounge components (not 30+)  
✅ **Service count:** 30+ service files (20+ framework-agnostic)  

### What Was Corrected

❌ **Removed:** All Drizzle ORM references and adapter layer concept  
❌ **Removed:** `/src/features/` directory structure  
❌ **Removed:** Middleware wrapper pattern  
❌ **Removed:** Dual-ORM option (not viable)  
✅ **Added:** Phase 0 prerequisites (BLOCKING tasks)  
✅ **Added:** Complete PostgreSQL schema (all 11 tables)  
✅ **Added:** Service layer examples with raw SQL  
✅ **Added:** API route examples with inline auth  
✅ **Updated:** Timeline from 5-6 weeks to 7-9 weeks  
✅ **Updated:** Effort from 120-150 hours to 140-180 hours (+ 30% buffer)  

---

**END OF REVISED PLAN**

**STATUS:** ✅ Ready for Phase 0 execution after stakeholder approval

**LAST UPDATED:** January 29, 2026