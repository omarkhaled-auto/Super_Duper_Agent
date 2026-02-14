# Real-Time Collaborative Drawing/CAD Architecture Research

**Date:** 2026-02-12
**Purpose:** Architecture decision support for collaborative drawing/CAD application

---

## Table of Contents

1. [Conflict Resolution Strategies](#1-conflict-resolution-strategies)
2. [CRDT Libraries & Managed Services](#2-crdt-libraries--managed-services)
3. [Real-Time Infrastructure](#3-real-time-infrastructure)
4. [Awareness Features](#4-awareness-features)
5. [Case Studies](#5-case-studies)
6. [Data Model for Collaborative Canvas](#6-data-model-for-collaborative-canvas)
7. [Architecture Recommendation](#7-architecture-recommendation)

---

## 1. Conflict Resolution Strategies

### 1.1 Operational Transformation (OT)

**How it works:** OT transforms operations against each other so that they can be applied in any order and still converge. When two users make concurrent edits, each operation is transformed against the other before application.

**Strengths:**
- Battle-tested in Google Docs for over 15 years
- Lower memory overhead than CRDTs (no metadata per character/element)
- Well-suited for linear text where position-based operations are natural

**Weaknesses:**
- Requires a central server to define the canonical operation order
- Combinatorial explosion of transform functions: for N operation types, you need N^2 transform pairs
- Extremely hard to implement correctly -- even academic proofs have been found to contain errors
- Google's own engineering team has described it as "notoriously difficult to implement"

**Applicability to Canvas/Drawing:** Poor fit. OT was designed for sequential text where operations have positions (insert at offset 5). Canvas objects are independent entities identified by ID, not position. The complexity of OT buys you nothing for this use case. **Figma explicitly rejected OT** for this reason: "OTs were unnecessarily complex for our problem space."

### 1.2 CRDTs (Conflict-free Replicated Data Types)

**How they work:** CRDTs are data structures with mathematically-guaranteed eventual consistency. Any two replicas that have received the same set of updates will converge to the same state, regardless of the order in which updates were received. This is achieved through commutative, associative, and idempotent merge operations.

**Key CRDT types relevant to canvas:**

| CRDT Type | Use Case in Canvas |
|-----------|-------------------|
| **Last-Writer-Wins Register (LWW)** | Individual shape properties (x, y, width, color) |
| **LWW Map** | Object property bags |
| **Grow-only Set (G-Set)** | Tracking created objects |
| **OR-Set (Observed-Remove Set)** | Object collection with add/delete |
| **RGA (Replicated Growable Array)** | Ordered sequences (layer ordering) |

**Strengths:**
- No central coordination required (works peer-to-peer)
- Mathematically proven convergence
- Handles offline editing naturally
- Well-suited for independent objects (each shape is its own entity)

**Weaknesses:**
- Memory overhead: metadata must be stored per element for conflict resolution
- Tombstones: deleted items often must be retained as markers
- Some operations (like concurrent reparenting) require careful design to avoid cycles

**Applicability to Canvas/Drawing:** Excellent fit. Each shape on the canvas can be modeled as an independent CRDT (LWW register for properties). Most edits affect different shapes, so conflicts are rare. When conflicts do occur (two users moving the same shape), LWW is an acceptable resolution.

### 1.3 Last-Writer-Wins (LWW)

**How it works:** Each value has a timestamp (or server-assigned sequence number). When two conflicting writes occur, the one with the later timestamp wins.

**When it is acceptable:**
- Shape property edits (color, position, size) -- if two users move the same shape simultaneously, the last position wins. This is intuitive and acceptable.
- Object creation/deletion -- the last action wins
- Non-text content where character-level merging is unnecessary

**When it is NOT acceptable:**
- Collaborative text editing (you need character-level merging, not whole-string LWW)
- Operations where both edits should be preserved (e.g., both users' annotations should appear)

**For canvas applications:** LWW at the property level is the dominant strategy. Figma, Excalidraw, and tldraw all use variants of this approach.

### 1.4 CRDT vs OT for Drawing Applications -- Verdict

| Criterion | CRDT | OT |
|-----------|------|-----|
| **Complexity** | Simpler for canvas (property-level LWW) | Overkill -- N^2 transform functions |
| **Offline support** | Native -- merge whenever reconnected | Requires server to sequence operations |
| **Server dependency** | Optional (can be pure P2P) | Required (central sequencer) |
| **Canvas suitability** | Excellent (independent objects) | Poor (designed for sequential text) |
| **Industry adoption** | Figma, Excalidraw, tldraw, Miro | Google Docs (text only) |
| **Memory overhead** | Higher (metadata per element) | Lower |
| **Implementation risk** | Low (well-studied for canvas) | High (combinatorial explosion) |

**Clear winner for canvas: CRDT-inspired approaches.** Even Figma, which uses a centralized server, chose CRDT-inspired data structures over OT. They use a simplified approach: true CRDTs are designed for decentralized systems, but a centralized server can simplify the implementation by removing some overhead while keeping the beneficial properties.

---

## 2. CRDT Libraries & Managed Services

### 2.1 Yjs

**Repository:** github.com/yjs/yjs
**License:** MIT
**Maturity:** Production-ready, widely deployed

**Architecture:**
- Core library exposes shared data types: `Y.Map`, `Y.Array`, `Y.Text`, `Y.XmlFragment`
- Network-agnostic: the core has no opinion about transport
- Providers handle networking, persistence, and awareness
- Modular: mix and match providers for different needs

**Key Shared Types for Canvas:**
```typescript
const ydoc = new Y.Doc()
const shapes = ydoc.getMap('shapes')        // Y.Map<string, Y.Map> for shape registry
const layers = ydoc.getArray('layers')      // Y.Array for layer ordering
const metadata = ydoc.getMap('metadata')    // Y.Map for document metadata
```

**Providers (Transport/Persistence):**

| Provider | Transport | Use Case |
|----------|-----------|----------|
| **y-websocket** | WebSocket | Standard client-server sync |
| **y-webrtc** | WebRTC | Peer-to-peer, end-to-end encrypted |
| **y-indexeddb** | IndexedDB | Client-side persistence (offline) |
| **y-redis** | Redis pub/sub | Horizontally scalable server |
| **Y-Sweet** (Jamsocket) | WebSocket + persistence | Managed hosting, easy deployment |
| **Liveblocks** | WebSocket | Fully managed, enterprise features |
| **Hocuspocus** (Tiptap) | WebSocket | Self-hosted, authentication built-in |

**Performance:**
- Fastest CRDT implementation by benchmarks (see github.com/dmonad/crdt-benchmarks)
- Handles documents with millions of operations
- Efficient binary encoding for network and storage
- Incremental updates: only changed data is transmitted

**How Excalidraw Uses Yjs:**
Excalidraw's earlier P2P version used Socket.IO with a custom merge approach (version numbers + nonce for tie-breaking). The current Excalidraw+ (commercial) uses Yjs for collaboration, where each `ExcalidrawElement` maps to entries in a Y.Map, with Yjs handling conflict resolution, versioning, and sync automatically.

**How tldraw Uses Yjs (Historical):**
tldraw previously used Yjs for its collaboration layer (and also used Replicache in an earlier iteration). As of 2025-2026, tldraw has moved to its own `tldraw sync` library built on `@tldraw/sync-core`, which is a custom sync solution using WebSocket rooms + SQLite/in-memory storage. However, tldraw still supports third-party Yjs integration via Liveblocks.

**Scaling Yjs (y-redis):**
The `y-redis` module enables horizontal scaling by using Redis pub/sub to distribute updates across multiple server instances. Each Yjs document can be handled by any server, and Redis ensures all servers stay in sync. This is critical for production deployments needing to handle thousands of concurrent rooms.

**Verdict on Yjs:** Best general-purpose CRDT library for canvas. Largest ecosystem, best performance, most providers. The modular architecture means you can start with `y-websocket` and upgrade to `y-redis` for scale or `Y-Sweet` for managed hosting without changing application code.

### 2.2 Automerge

**Repository:** github.com/automerge/automerge
**License:** MIT
**Core:** Written in Rust, JS bindings via WebAssembly

**Key Differences from Yjs:**

| Aspect | Yjs | Automerge |
|--------|-----|-----------|
| **Core language** | JavaScript | Rust + WASM |
| **Data model** | Custom shared types | JSON-like documents |
| **Text algorithm** | YATA (sequence CRDT) | RGA |
| **Performance** | Faster in benchmarks | Improved in v2, still slower |
| **Ecosystem** | Much larger (more providers, bindings) | Smaller, but multi-language |
| **API style** | Observable shared types | Functional (document snapshots) |
| **Bundle size** | Smaller | Larger (WASM) |
| **History/branching** | Limited | Git-like versioning built in |

**When to choose Automerge over Yjs:**
- You need multi-language support (Python, Rust native, Swift)
- You want built-in Git-like document history and branching
- Your data model is deeply nested JSON rather than flat key-value

**When to choose Yjs over Automerge:**
- Performance is critical (Yjs is consistently faster)
- You need the largest provider ecosystem
- Canvas/drawing applications (Yjs is the industry standard here)
- You want to minimize bundle size
- You need the most battle-tested solution

**Verdict on Automerge:** Good library, but Yjs is the better choice for canvas applications. Automerge's strengths (JSON model, multi-language, Git-like history) don't outweigh Yjs's advantages in performance and ecosystem for this use case.

### 2.3 Loro

**Repository:** github.com/loro-dev/loro
**License:** MIT
**Core:** Rust + WASM bindings
**Status:** Version 1.0 released, newer than Yjs/Automerge

**Key Differentiators:**
- Uses the Fugue CRDT algorithm (reduces text interleaving anomalies)
- Built-in tree structure CRDT (important for hierarchical canvas layers)
- Version history tracking similar to Git
- Support for Rust, JS/TS, Swift, and Dart (via WASM)
- Strong performance characteristics (claims to be competitive with Yjs)

**Downsides:** Newer, smaller ecosystem, fewer providers, fewer production deployments.

**Verdict:** Worth watching, but too new for a production architecture decision. Revisit in 12 months.

### 2.4 Liveblocks

**What it is:** Fully managed collaboration infrastructure (SaaS)
**Pricing model:** Per monthly active room (not per user)

| Plan | Price | Rooms | Key Features |
|------|-------|-------|-------------|
| Free | $0/mo | 500 rooms | Basic features, 256 MB storage |
| Pro | $30/mo + usage | 500 included, $0.03/room after | Remove branding, 8 GB storage |
| Team | $600/mo + usage | 500 included, $0.03/room after | SOC 2, SSO, HIPAA add-on ($350/mo) |
| Enterprise | Custom | Custom | Multi-region, management API, SCIM |

**Canvas-Specific Features:**
- **Presence:** Live avatar stack, live cursors, live selection -- all pre-built
- **Storage:** Two sync engines: Liveblocks Storage (their proprietary CRDT) and Yjs
- **Multiplayer undo/redo:** Built-in
- **Offline support:** Included
- **Comments:** Contextual comments with threads, reactions, mentions
- **Notifications:** In-app, email, Slack, Teams, web push
- **AI Agents:** AI as collaborator feature

**SDK Support:** React, Next.js, Vue, Svelte, SolidJS, vanilla JS
**Pre-built UI components:** Comments, presence indicators, cursors

**When to choose Liveblocks:**
- You want to ship collaboration fast (days, not months)
- You prefer managed infrastructure over self-hosting
- You need enterprise features (SOC 2, HIPAA, SSO)
- You need built-in presence, comments, and notifications

**When NOT to choose Liveblocks:**
- You need full control over your sync infrastructure
- You need offline-first (Liveblocks is online-first with caching)
- You need self-hosted data sovereignty
- Budget is very tight (costs scale with room count)

**Verdict:** Excellent for rapid development and startups. The pricing is room-based (not per-user), which is favorable for canvas apps where users share rooms. The Yjs integration means you can migrate away later if needed. Consider for MVP, but understand the vendor lock-in tradeoffs.

### 2.5 PartyKit

**What it is:** Serverless real-time infrastructure on Cloudflare Workers
**Pricing:** Free tier available, pay-per-use scaling
**Key technology:** Cloudflare Durable Objects for per-room state

**Architecture:**
```
Client <--WebSocket--> Cloudflare Edge <--Durable Object--> Room State
```

Each "party" (room) gets its own Durable Object with:
- Persistent storage (SQLite or KV)
- WebSocket connections
- Custom server-side logic (JavaScript/TypeScript)

**Notable users:** tldraw (powers their collaborative whiteboard), BlockNote, Stately

**Strengths:**
- Edge computing: rooms run close to users globally
- Simple programming model ("just JavaScript")
- Automatic scaling (tens to thousands of users)
- Works with Yjs (can run y-websocket provider on PartyKit)
- No infrastructure to manage

**Weaknesses:**
- Tied to Cloudflare ecosystem
- Durable Objects have eventual consistency limitations
- Less mature than dedicated Yjs server solutions
- Debugging distributed edge functions is harder

**Verdict:** Good option if you're already on Cloudflare or want edge-deployed rooms. The fact that tldraw uses it in production is a strong signal. Pairs well with Yjs.

### 2.6 Replicache / Zero

**Status:** Replicache is in maintenance mode (open-sourced). Its successor is **Zero** by Rocicorp.

**Replicache Architecture:**
- Client-side sync framework (not a CRDT library)
- Downloads data to client, reads/writes locally, syncs in background
- Uses **server reconciliation** (server is authoritative, client predicts)
- Works with any backend (BYOB -- Bring Your Own Backend)

**Zero (Successor):**
- Query-driven sync engine
- Client-side store of recently used rows
- Queries run against client first (instant), then validated against server
- Uses ZQL (custom streaming query engine)
- Works with Postgres databases
- Pricing: Hobby $30/mo (10GB), Professional $300/mo (100GB), BYOC $1000/mo

**Key Difference from CRDTs:**
Replicache/Zero uses server reconciliation, not CRDTs. The server is always authoritative. Conflicts are resolved by replaying mutations on the server (similar to multiplayer game netcode). This gives you full control over conflict resolution logic.

**When to choose Replicache/Zero over Yjs:**
- You have complex business logic that needs server-side validation
- You want instant UI without CRDTs
- Your data model is more traditional (Postgres tables, not CRDT shared types)
- You need fine-grained permissions that the server enforces

**When NOT to choose:**
- You need true P2P/offline-first (server is required)
- You want a simple, well-understood CRDT model
- Replicache is in maintenance mode; Zero is newer

**Verdict:** Interesting alternative architecture. The server-reconciliation model is simpler to reason about for business logic but requires more server work. For a pure collaborative canvas, Yjs is simpler. For a canvas embedded in a larger data-heavy application, Zero's Postgres integration could be valuable.

### 2.7 Velt

**What it is:** Complete collaboration SDK (SaaS)
**Distinguisher:** Highest-level abstraction -- provides pre-built UI components for every collaboration feature

**Features:** Comments, notifications, recording, live cursors, presence, follow mode, live selection, huddle (voice/video), multiplayer editing, single editor mode, live state sync

**Uses Yjs behind the scenes** for CRDT sync.

**Verdict:** Highest-level option. If you want to add collaboration features to an existing app in days rather than weeks, Velt is the fastest path. But you sacrifice control and are fully dependent on their service.

---

## 3. Real-Time Infrastructure

### 3.1 WebSocket Server Design for Collaborative Canvas

**The Standard Architecture (used by Figma, tldraw, and most production systems):**

```
                    +-----------+
                    | Load      |
   Clients ------->| Balancer  |------> Server Cluster
   (WebSocket)     | (sticky)  |        (one process per room)
                    +-----------+

Per-Room Server Process:
+-----------------------------------+
| Room "abc123"                      |
| +-------------------------------+ |
| | Authoritative Document State  | |
| | (in-memory Y.Doc or custom)   | |
| +-------------------------------+ |
| | Connected Clients:            | |
| |   - User A (WebSocket)       | |
| |   - User B (WebSocket)       | |
| |   - User C (WebSocket)       | |
| +-------------------------------+ |
| | Persistence: SQLite / Redis   | |
| +-------------------------------+ |
+-----------------------------------+
```

**Key Design Decisions:**

1. **Sticky sessions:** Each room must be served by a single server process to maintain consistency. Use sticky sessions (session affinity) at the load balancer, or use Cloudflare Durable Objects (one object per room).

2. **Message format:** Binary encoding (Yjs uses a compact binary format). Avoid JSON for high-frequency updates -- the serialization overhead matters at 60fps cursor updates.

3. **Batching:** Aggregate multiple property changes into a single WebSocket message. Debounce at 16-50ms intervals for shape property updates, but send cursor positions immediately.

4. **Persistence strategy:**
   - In-memory: Keep authoritative state in RAM for speed
   - Write-behind: Persist to database on a timer (every 1-5 seconds) or on significant changes
   - Snapshot + incremental: Store full snapshots periodically, with incremental updates between

5. **Connection lifecycle:**
   ```
   Client connects -> Download full document snapshot
   Client edits -> Send incremental update via WebSocket
   Server receives -> Apply to authoritative state -> Broadcast to other clients
   Client disconnects -> State preserved server-side
   Client reconnects -> Download fresh snapshot, reapply any offline edits
   ```

### 3.2 Cursor Positions and Presence

**Architecture for presence data:**

Presence data (cursors, selections, viewport) is **ephemeral** -- it does not need to be persisted. It should flow through a separate, lightweight channel.

```typescript
// Yjs awareness protocol
const awareness = wsProvider.awareness

// Set local state
awareness.setLocalStateField('cursor', {
  x: 150,
  y: 300,
  tool: 'select',
  timestamp: Date.now()
})

awareness.setLocalStateField('user', {
  name: 'Omar',
  color: '#FF5733',
  avatar: '/avatars/omar.png'
})

// Listen for remote awareness changes
awareness.on('change', ({ added, updated, removed }) => {
  // Update cursor positions for other users
  const states = awareness.getStates()
  states.forEach((state, clientId) => {
    renderRemoteCursor(state.cursor, state.user)
  })
})
```

**Update frequency:**
- Cursor position: 30-60fps (throttle to ~30 for network efficiency)
- Selection state: On change only
- Viewport position: On scroll/zoom end (debounced 100ms)
- User status: On change only

**Bandwidth optimization:**
- Only send deltas when possible
- Compress cursor trails (send waypoints, interpolate on client)
- Use presence channels separate from document sync
- Drop stale presence data (timeout after 30s of no updates)

### 3.3 Conflict Resolution for Shape Operations

**Move operation:** LWW at property level. If two users move the same shape simultaneously, the last position wins. This is intuitive because the shape ends up where the last person put it.

**Resize operation:** LWW per property (width, height independently). If user A changes width while user B changes height, both changes are preserved because they affect different properties.

**Delete operation:** Tombstoning. Mark shapes as `isDeleted: true` rather than removing them. This prevents the "ghost shape" problem where a deleted shape reappears because another user's stale state is re-synced. Clean up tombstones periodically.

**Simultaneous creation:** No conflict -- each user generates a unique ID (clientId + sequence number), so objects never collide.

**Reparenting (moving between layers/groups):**
- Store parent reference on the child (not child list on the parent)
- Prevents one object from having multiple parents
- Server validates: reject parent changes that would create cycles
- Use fractional indexing for z-order within a parent

### 3.4 Offline / Reconnection

**Strategy (Figma model):**
1. Client goes offline
2. Client continues editing locally (all changes buffered)
3. Client reconnects
4. Client downloads fresh snapshot from server
5. Client reapplies offline edits on top of fresh snapshot
6. Client resumes normal sync

**Yjs offline approach:**
1. Client uses `y-indexeddb` to persist Y.Doc to IndexedDB
2. Changes accumulate in IndexedDB while offline
3. On reconnect, Yjs's sync protocol automatically sends accumulated updates
4. CRDT merge guarantees consistency regardless of how long offline

**Key consideration for canvas:** Offline conflicts on the same shape are resolved by LWW, which means one user's edits may be silently overwritten. For engineering drawings where this is unacceptable, implement explicit locking (see Section 6.4).

### 3.5 Scaling to 50+ Simultaneous Users on One Canvas

**Challenges at 50+ users:**
- WebSocket fan-out: each update must be broadcast to 49 other users
- Cursor rendering: 50 cursors updating at 30fps = 1500 updates/second
- Network bandwidth: significant even with binary encoding
- Rendering performance: client must process and render all incoming changes

**Strategies:**

1. **Cursor throttling:** Reduce cursor update frequency to 15-20fps for rooms with >20 users. Interpolate positions client-side.

2. **Viewport-based filtering:** Only send updates for objects visible in the user's viewport. If user A is zoomed into the top-left corner, don't send them updates about shapes in the bottom-right. This requires server-side spatial indexing.

3. **Presence aggregation:** For >20 users, show a user count badge instead of individual cursors for users outside the current viewport.

4. **Update batching:** Aggregate all changes in a 16ms window into a single broadcast message. This reduces WebSocket message count significantly.

5. **Server architecture:**
   - Use `y-redis` for horizontal scaling across server instances
   - Each room still needs a single authoritative process, but Redis pub/sub distributes awareness data
   - For very large rooms, consider sharding by canvas region

6. **Figma's approach:** One Rust process per document. Rust is used specifically for the multiplayer server because of its performance characteristics. The WebSocket server is separate from the web application server.

7. **tldraw's approach:** Cloudflare Durable Objects. One Durable Object per room, with WebSocket connections to the edge. SQLite for persistence within the Durable Object.

**Practical limits:**
- 50 users: Achievable with standard WebSocket fan-out + throttling
- 100 users: Needs viewport filtering and cursor aggregation
- 500+ users: Needs regional sharding and read-only spectator mode for most users

---

## 4. Awareness Features

### 4.1 Live Cursors

**Implementation:**

```typescript
// Send cursor position (throttled to 30fps)
canvas.addEventListener('pointermove', throttle((e) => {
  const canvasPos = screenToCanvas(e.clientX, e.clientY)
  awareness.setLocalStateField('cursor', {
    x: canvasPos.x,
    y: canvasPos.y,
    tool: currentTool, // 'select', 'draw', 'text', etc.
    pressure: e.pressure, // for pen input
  })
}, 33)) // 30fps

// Render remote cursors
function renderRemoteCursors(states: Map<number, AwarenessState>) {
  for (const [clientId, state] of states) {
    if (clientId === ownClientId) continue
    const cursor = state.cursor
    const user = state.user

    // Interpolate position for smooth movement
    const renderedPos = interpolate(lastPosition[clientId], cursor, 0.3)

    drawCursor(renderedPos.x, renderedPos.y, {
      color: user.color,
      name: user.name,
      tool: cursor.tool,
      avatar: user.avatar,
    })
  }
}
```

**Visual design patterns:**
- Color-coded cursor with user name label
- Cursor shape changes based on active tool
- Fade out after 5s of inactivity
- Show cursor trail for pen/draw tools
- Position label offset to avoid overlapping with native cursor

### 4.2 Selection Awareness

**Two approaches:**

**A. Visual-only awareness (recommended for drawing):**
- Show colored outlines around shapes other users have selected
- No locking -- users CAN edit the same shape simultaneously
- Visual cue discourages concurrent edits but doesn't prevent them
- Used by: Excalidraw, Miro

**B. Soft locks (recommended for engineering/CAD):**
- When a user selects a shape, broadcast a "lock intent"
- Other users see the lock indicator and are discouraged from editing
- Lock expires after 30 seconds of inactivity
- Lock can be forcefully taken over with a "steal lock" action
- Used by: Drawboard, some CAD tools

```typescript
// Selection awareness via Yjs
awareness.setLocalStateField('selection', {
  shapeIds: ['shape-1', 'shape-3'],
  mode: 'moving', // 'idle', 'moving', 'resizing', 'editing'
})

// Render selection indicators
function renderSelectionAwareness(states) {
  const occupiedShapes = new Map() // shapeId -> user

  for (const [clientId, state] of states) {
    if (clientId === ownClientId) continue
    for (const shapeId of state.selection?.shapeIds ?? []) {
      occupiedShapes.set(shapeId, state.user)
    }
  }

  for (const [shapeId, user] of occupiedShapes) {
    drawSelectionOutline(shapeId, user.color, user.name)
  }
}
```

### 4.3 User Presence Indicators

**Components:**
1. **Avatar stack:** Show who is currently in the room (top-right corner)
2. **Status indicators:** Active (editing), Idle (viewing), Away (tab unfocused)
3. **User list panel:** Expandable list with user names, roles, and connection status

**Detecting user status:**
```typescript
// Track visibility
document.addEventListener('visibilitychange', () => {
  awareness.setLocalStateField('status',
    document.hidden ? 'away' : 'active'
  )
})

// Track idle (no mouse/keyboard for 60s)
let idleTimer: NodeJS.Timeout
function resetIdleTimer() {
  clearTimeout(idleTimer)
  awareness.setLocalStateField('status', 'active')
  idleTimer = setTimeout(() => {
    awareness.setLocalStateField('status', 'idle')
  }, 60000)
}
window.addEventListener('mousemove', resetIdleTimer)
window.addEventListener('keydown', resetIdleTimer)
```

### 4.4 Follow Mode

**"Follow mode" lets you watch what another user is doing in real-time.**

**Implementation:**
```typescript
// Leader broadcasts viewport
awareness.setLocalStateField('viewport', {
  centerX: viewport.centerX,
  centerY: viewport.centerY,
  zoom: viewport.zoom,
})

// Follower subscribes to leader's viewport
function followUser(targetClientId: number) {
  following = targetClientId
  awareness.on('change', () => {
    if (!following) return
    const targetState = awareness.getStates().get(following)
    if (!targetState?.viewport) return

    animateViewportTo({
      centerX: targetState.viewport.centerX,
      centerY: targetState.viewport.centerY,
      zoom: targetState.viewport.zoom,
    })
  })
}
```

**tldraw provides this out of the box** with their `sdk-features/user-following` API.

**UX considerations:**
- Smooth viewport interpolation (don't teleport)
- "Following [User]" banner at top of screen
- Click anywhere or start editing to break follow mode
- Show the followed user's cursor more prominently

### 4.5 Comments/Annotations Tied to Canvas Positions

**Data model for positioned comments:**
```typescript
interface CanvasComment {
  id: string
  threadId: string
  author: User
  body: string
  timestamp: Date

  // Canvas-specific positioning
  anchor: {
    type: 'point' | 'shape' | 'region'
    // For 'point': absolute canvas coordinates
    x?: number
    y?: number
    // For 'shape': relative to shape
    shapeId?: string
    offsetX?: number  // relative offset within shape
    offsetY?: number
    // For 'region': bounding box
    bounds?: { x: number, y: number, width: number, height: number }
  }

  resolved: boolean
}
```

**Key design decisions:**
- Comments anchored to shapes should move with the shape
- Comments at absolute positions stay fixed on the canvas
- Use a separate data store for comments (not the CRDT document) -- Figma does this with Postgres
- Liveblocks provides pre-built comments with threading, reactions, and mentions

---

## 5. Case Studies

### 5.1 Figma

**Architecture Source:** "How Figma's multiplayer technology works" (2019) by Evan Wallace, CTO

**Key Architecture Decisions:**

1. **CRDT-inspired, not true CRDT:** Figma uses a client/server architecture where the server is the central authority. They took inspiration from CRDTs (LWW registers, sets) but simplified by having the server define operation order. This eliminates the overhead of decentralized consensus.

2. **Document structure:** Tree of objects (like HTML DOM). Each object has an ID and a collection of properties with values. Conceptually: `Map<ObjectID, Map<Property, Value>>`.

3. **Property-level LWW:** Conflicts are resolved at the property level. Two users changing different properties on the same object do NOT conflict. Two users changing the same property on the same object resolve via last-writer-wins.

4. **No text merging:** Simultaneous edits to the same text value result in one winning, not a merge. "That's ok with us because Figma is a design tool, not a text editor."

5. **Fractional indexing for z-order:** Objects are ordered within their parent using fractional positions (numbers between 0 and 1). Inserting between two objects = averaging their positions. Parent link and position are stored as a single atomic property.

6. **Reparenting:** Parent link stored on child (not children list on parent). Server rejects parent changes that would create cycles. Temporary cycle detection on client shows objects as "detached" until resolved.

7. **Object creation:** Client generates unique IDs (clientId + sequence). No server round-trip needed.

8. **Undo/redo in multiplayer:** "If you undo a lot, copy something, and redo back to the present, the document should not change." Undo modifies redo history, redo modifies undo history.

9. **Server tech:** Rust for multiplayer servers (performance), separate process per document, WebSocket connections.

10. **Reconnection:** Download fresh snapshot on reconnect, reapply offline edits on top.

### 5.2 Excalidraw

**Architecture Source:** "Building Excalidraw's P2P Collaboration Feature" (2020)

**Key Architecture Decisions:**

1. **Data model:** Array of `ExcalidrawElement` objects in z-index order. Each element has: id, type, dimensions, visual properties.

2. **Collaboration approach:** Pseudo-P2P (central server relays encrypted messages, no centralized coordination). End-to-end encrypted.

3. **Conflict resolution (custom, CRDT-inspired):**
   - **New elements:** Merge by taking the union of all element IDs from local + remote state
   - **Deletions:** Tombstoning (`isDeleted: true` flag). Filtered out at render time. Cleaned up when saving to persistent storage.
   - **Concurrent edits:** Version number on each element. Incremented on every edit. Merge keeps the highest version.
   - **Tie-breaking:** `versionNonce` (random integer). When two elements have the same version, the lower nonce wins deterministically.

4. **Limitations acknowledged:**
   - No multiplayer undo/redo (undo stack cleared on receiving remote updates)
   - Version-based merge is element-level, not property-level (less granular than Figma)

5. **Evolution:** Current Excalidraw+ uses Yjs for more robust collaboration, but the open-source version's custom approach demonstrates how simple CRDT-inspired techniques can work for canvas.

### 5.3 tldraw

**Architecture Source:** tldraw docs (tldraw.dev)

**Key Architecture Decisions:**

1. **Custom sync engine (`tldraw sync`):** Built on `@tldraw/sync-core`. Not Yjs-based, but achieves similar goals. Used in production on tldraw.com.

2. **`TLSocketRoom`:** Server-side class that manages one room. Stores authoritative in-memory document state, manages WebSocket connections, persists to storage.

3. **Cloudflare deployment (recommended):**
   - Durable Objects: one per room (guarantees single process per document)
   - R2 or SQLite: persistence (migrating from R2 to SQLite)
   - Global edge deployment

4. **Storage options:**
   - `InMemorySyncStorage`: Simple, data lost on restart (good for prototyping)
   - `SQLiteSyncStorage`: Persistent, survives restarts (recommended for production)

5. **Three collaboration concerns:**
   - Data sync: `useSync` hook for WebSocket connection
   - User presence: Cursor positions, selections, viewports
   - Collaboration UI: `CollaboratorCursor`, `CollaboratorBrush`, `SharePanel` components

6. **User following:** Built-in viewport following API

7. **Integration with third parties:** Works with Liveblocks for those who prefer managed infrastructure.

### 5.4 Miro

**Public architecture details are limited.** From industry analysis:

- Miro uses a centralized server architecture with WebSocket connections
- Document state is stored server-side, with client-side caching for performance
- They handle millions of concurrent boards with microservice architecture
- Real-time presence (cursors, avatars) is handled separately from document state
- Supports up to hundreds of simultaneous users per board with performance optimizations (viewport culling, LOD rendering)

### 5.5 Google Jamboard (Discontinued)

Google Jamboard was discontinued in 2024. It used Google's internal real-time sync infrastructure (same foundation as Google Docs, but adapted for canvas). Being discontinued, it's not architecturally relevant for new projects.

---

## 6. Data Model for Collaborative Canvas

### 6.1 Structuring Drawing Elements for CRDT

**Recommended data model (Yjs-based):**

```typescript
// Root Y.Doc structure
const ydoc = new Y.Doc()

// Shape registry: Y.Map of Y.Maps
// Key: shapeId, Value: Y.Map of properties
const shapes = ydoc.getMap('shapes')

// Layer ordering: Y.Array of shapeIds
// (or use fractional indexing on each shape)
const layerOrder = ydoc.getArray('layerOrder')

// Document metadata
const meta = ydoc.getMap('meta')

// Example: Creating a rectangle
ydoc.transact(() => {
  const shape = new Y.Map()
  shape.set('id', 'rect-001')
  shape.set('type', 'rectangle')
  shape.set('x', 100)
  shape.set('y', 200)
  shape.set('width', 300)
  shape.set('height', 150)
  shape.set('fill', '#3B82F6')
  shape.set('stroke', '#1D4ED8')
  shape.set('strokeWidth', 2)
  shape.set('rotation', 0)
  shape.set('opacity', 1)
  shape.set('locked', false)
  shape.set('parentId', 'page-1')  // parent reference
  shape.set('sortIndex', 'a0')     // fractional index for ordering
  shape.set('createdBy', 'user-omar')
  shape.set('createdAt', Date.now())
  shape.set('isDeleted', false)    // tombstone flag

  shapes.set('rect-001', shape)
})
```

**Why Y.Map of Y.Maps (not Y.Array):**
- Property-level conflict resolution: two users editing different properties of the same shape merge cleanly
- O(1) access by shape ID
- No position-based conflicts (unlike arrays where insert positions can conflict)
- Adding new properties to a shape is always safe

**Alternative: Flat key-value approach (Figma-style):**
```typescript
// Each property is a separate entry: (objectId, property) -> value
const props = ydoc.getMap('props')
props.set('rect-001:x', 100)
props.set('rect-001:y', 200)
props.set('rect-001:width', 300)
// Maximum granularity -- even properties on the same shape never conflict
```

### 6.2 Handling Layers, Groups, and Hierarchical Objects

**Tree structure approach (Figma model):**

```
Document
  +-- Page 1
  |     +-- Group A
  |     |     +-- Rectangle 1
  |     |     +-- Circle 1
  |     +-- Line 1
  |     +-- Text Block 1
  +-- Page 2
        +-- ...
```

**Implementation with parent references:**

Each shape stores:
- `parentId`: reference to parent (group, page, or document root)
- `sortIndex`: fractional index for ordering within parent

**Fractional indexing for ordering:**
```
Item A: sortIndex = 'a'      // position 0.5
Item B: sortIndex = 'n'      // position 0.87
Insert between: sortIndex = 'g'  // position 0.69

// Use a library like 'fractional-indexing' for generating keys
import { generateKeyBetween } from 'fractional-indexing'

const newIndex = generateKeyBetween('a', 'n') // Returns a key between 'a' and 'n'
```

**Why parent references (not child lists):**
- A shape can only have ONE parent (enforced by data model)
- Concurrent reparenting: two users moving the same shape to different groups results in one winning (LWW), not the shape appearing in both groups
- No "orphan" problem: if a group is deleted, children's parentId still points to the (now-deleted) group, and you can reparent them to the grandparent

**Cycle prevention:**
- Server validates: before accepting a parentId change, walk up the tree to ensure no cycle
- Client shows temporary "detached" state if a cycle is detected locally

### 6.3 Z-Index Management with Multiple Users

**Problem:** Two users simultaneously moving shapes to the front/back.

**Solution: Fractional indexing (used by Figma and tldraw)**

```
Before:
  Shape A: zIndex = 'a'   (bottom)
  Shape B: zIndex = 'h'   (middle)
  Shape C: zIndex = 'p'   (top)

User 1 moves D to front (above C):
  Shape D: zIndex = generateKeyBetween('p', null) = 'u'

User 2 simultaneously moves E to front:
  Shape E: zIndex = generateKeyBetween('p', null) = 'u' (or 'v')

Result: Both D and E are above C. Their relative order depends on
the fractional index values. No conflict, no data loss.
```

**Why this works:**
- Each zIndex is a string that can be compared lexicographically
- Inserting between two values always produces a valid intermediate value
- No integer overflow or collision issues
- LWW on the zIndex property means concurrent reordering of the SAME shape resolves cleanly

**Alternative: Integer z-index with reindexing:**
- Simpler to understand but requires reindexing all shapes when one moves
- Reindexing touches many shapes, creating more CRDT operations
- Not recommended for collaborative scenarios

### 6.4 Lock Mechanisms for Engineering Drawings

For engineering/CAD applications where data integrity is critical, implement explicit locking:

**Soft locking (recommended):**
```typescript
interface Lock {
  shapeId: string
  lockedBy: string       // user ID
  lockedAt: number       // timestamp
  expiresAt: number      // auto-expire after 5 minutes
  lockType: 'edit' | 'exclusive'
}

// Store locks in a Y.Map
const locks = ydoc.getMap('locks')

function acquireLock(shapeId: string): boolean {
  const existing = locks.get(shapeId) as Lock | undefined

  if (existing && existing.lockedBy !== currentUserId) {
    if (existing.expiresAt > Date.now()) {
      return false // Shape is locked by another user
    }
    // Lock expired, can take over
  }

  locks.set(shapeId, {
    shapeId,
    lockedBy: currentUserId,
    lockedAt: Date.now(),
    expiresAt: Date.now() + 5 * 60 * 1000, // 5 minute expiry
    lockType: 'edit',
  })
  return true
}

function releaseLock(shapeId: string) {
  const existing = locks.get(shapeId) as Lock | undefined
  if (existing?.lockedBy === currentUserId) {
    locks.delete(shapeId)
  }
}
```

**Hard locking (for critical engineering data):**
- Server-enforced: the server rejects edits to locked shapes
- Requires a database-backed lock table (not just CRDT)
- Lock with checkout/checkin semantics (like version control)
- Admin can force-release locks

**Visual indicators:**
- Locked shapes show a padlock icon with the locking user's name
- Locked shapes are non-interactive (cursor changes to "not allowed")
- Lock status shown in properties panel

---

## 7. Architecture Recommendation

### 7.1 Decision Matrix

| Factor | Weight | Yjs (self-hosted) | tldraw sync | Liveblocks | PartyKit + Yjs |
|--------|--------|-------------------|-------------|------------|----------------|
| **Time to ship** | 25% | Medium (3-6 weeks) | Fast (1-2 weeks if using tldraw) | Fastest (days) | Medium (2-4 weeks) |
| **Control** | 20% | Full | High | Low | Medium |
| **Scalability** | 15% | High (y-redis) | High (Cloudflare) | High (managed) | High (Cloudflare) |
| **Offline support** | 10% | Excellent | Good | Partial | Good |
| **Cost at scale** | 15% | Low (self-hosted) | Medium | High ($0.03/room) | Medium |
| **Canvas features** | 10% | Build yourself | Full tldraw SDK | Build yourself | Build yourself |
| **Vendor lock-in** | 5% | None | Low (OSS) | High | Medium (Cloudflare) |

### 7.2 Recommended Architecture for a Collaborative Drawing/CAD App

**Tier 1 - If building a custom canvas (not using tldraw/Excalidraw):**

```
Recommended stack:
- Sync: Yjs (Y.Doc with Y.Map per shape)
- Transport: y-websocket (start) -> y-redis (scale)
- Persistence: y-indexeddb (client) + PostgreSQL/SQLite (server)
- Awareness: Yjs awareness protocol
- Presence UI: Custom (React components)
- Hosting: Your own servers or Cloudflare Workers

Why: Maximum control, no vendor lock-in, proven at scale,
best performance, largest ecosystem.
```

**Tier 2 - If building on top of tldraw:**

```
Recommended stack:
- Canvas: tldraw SDK (@tldraw/tldraw)
- Sync: tldraw sync (@tldraw/sync)
- Hosting: Cloudflare (Durable Objects + R2/SQLite)
- Presence: Built into tldraw
- Cursors: Built into tldraw
- Following: Built into tldraw

Why: Fastest path to a full-featured collaborative whiteboard.
tldraw is battle-tested and provides all canvas + collaboration
features out of the box.
```

**Tier 3 - If you need to ship collaboration in days (MVP/startup):**

```
Recommended stack:
- Sync: Liveblocks (Yjs provider)
- Canvas: Your own or tldraw
- Presence: Liveblocks pre-built components
- Comments: Liveblocks comments
- Hosting: Liveblocks managed

Why: Fastest time-to-market. Switch to Yjs self-hosted later
if costs become prohibitive (since Liveblocks uses Yjs
underneath, migration path exists).
```

### 7.3 Key Takeaways

1. **Use CRDT-inspired approaches, not OT.** Every major collaborative canvas product has chosen CRDTs (or CRDT-inspired systems) over OT. The case is settled for canvas applications.

2. **Property-level LWW is sufficient.** You don't need character-level text CRDTs for a canvas. Shape properties (x, y, width, color) resolve naturally with last-writer-wins at the property granularity.

3. **Yjs is the de facto standard.** Whether you use it directly or through Liveblocks/Velt, Yjs underpins most collaborative canvas implementations. Starting with Yjs gives you the largest ecosystem and clearest upgrade path.

4. **Separate presence from persistence.** Cursor positions and selection state are ephemeral and should not be persisted to the document. Use Yjs awareness protocol or a separate WebSocket channel.

5. **Fractional indexing for z-order.** Don't use integer z-indices in a collaborative setting. Fractional indexing (strings) provides conflict-free ordering.

6. **Parent references, not child lists.** Store the parent ID on the child shape. This prevents a shape from appearing in multiple groups after concurrent reparenting.

7. **Plan for scale from the start.** Even if you start with a simple y-websocket server, architect your system so you can swap in y-redis or Cloudflare Durable Objects later without rewriting your client code.

8. **For engineering/CAD: add locking.** Soft locks with auto-expiry are sufficient for most cases. Hard server-enforced locks are needed only for safety-critical engineering data.

---

## Sources

**Primary Sources (directly scraped):**
- Figma: "How Figma's multiplayer technology works" -- figma.com/blog/how-figmas-multiplayer-technology-works/
- Excalidraw: "Building Excalidraw's P2P Collaboration Feature" -- plus.excalidraw.com/blog/building-excalidraw-p2p-collaboration-feature
- Yjs Documentation -- docs.yjs.dev
- tldraw Collaboration Docs -- tldraw.dev/docs/collaboration
- tldraw Sync Docs -- tldraw.dev/docs/sync
- PartyKit Documentation -- docs.partykit.io
- Liveblocks Documentation -- liveblocks.io/docs
- Liveblocks Pricing -- liveblocks.io/pricing
- Replicache -- replicache.dev
- Zero (Rocicorp) -- zero.rocicorp.dev
- Velt CRDT Library Comparison -- velt.dev/blog/best-crdt-libraries-real-time-data-sync

**Search-based sources:**
- 15 firecrawl search queries across CRDT comparisons, library architectures, case studies, and implementation patterns
