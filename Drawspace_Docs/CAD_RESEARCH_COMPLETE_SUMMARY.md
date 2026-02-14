# Complete CAD & Collaborative Drawing Research Summary
**Date:** 2026-02-12
**Scope:** Professional web-based CAD applications — rendering, collaboration, architecture, and implementation patterns

---

## EXECUTIVE SUMMARY

This research synthesizes three comprehensive reports analyzing web-based CAD and drawing applications, identifying industry patterns and providing a clear technology roadmap.

**Key Findings:**
- **Rendering:** Canvas 2D sufficient for <5K objects; WebGL mandatory for CAD-scale (10K+); Figma's migration to WebGPU represents the frontier
- **Collaboration:** Yjs CRDT + tldraw canvas engine is the optimal foundation for professional CAD
- **Stack:** React + tldraw + Yjs + Cloudflare Durable Objects (or Node.js + Redis)
- **Timeline:** 6-12 months MVP, 18-24 months production-grade

---

## PART 1: PRODUCT LANDSCAPE & FEATURE MATRIX

### 1.1 Industry Leaders Analysis

#### Figma (Gold Standard — Design Tool)
- **Rendering:** C++ → WebAssembly → WebGPU (with WebGL fallback)
- **Performance:** Custom tile-based rendering, no GC pauses, anti-aliased
- **Collaboration:** CRDT-inspired (simplified due to server authority), last-writer-wins per property, fractional indexing
- **Scale:** Handles millions of objects, 100+ concurrent users
- **Key Innovation:** Same C++ codebase compiles to WASM (browser) + native x64/arm64 (server rendering)
- **Lessons:** Don't build from scratch unless you have $20M+ and 4-5 years

#### Onshape (Full 3D CAD in Browser)
- **Architecture:** Microservices, geometry servers do all math (Parasolid kernel + D-Cubed solver)
- **Rendering:** Client receives triangles, renders via WebGL; no file save (database-backed)
- **Collaboration:** Increments (change log) designed to apply to any document state; enables seamless merge
- **PDM:** Version management built into storage model, not a separate system
- **Lesson:** Cloud-native CAD requires server-side geometry computation; PDM must be fundamental to architecture

#### AutoCAD Web
- **Tech:** C/C++ → WASM via Emscripten + WebGL
- **Validation:** Confirms WASM + WebGL is correct approach for professional CAD
- **Limitation:** DWG parsing is proprietary advantage; not replicable without ODA SDK

#### Excalidraw (Open Source — Whiteboard)
- **Tech:** React + TypeScript, Canvas 2D + Rough.js
- **Collaboration:** Pseudo-P2P, end-to-end encrypted, Socket.IO relay
- **Performance:** Lags at ~15K elements
- **Not for CAD:** Hand-drawn aesthetic, no precision tooling, no hierarchy

#### tldraw (Modern Canvas SDK)
- **Rendering:** Canvas 2D with custom optimization
- **State:** Signals-based reactive store, record-centric (tldraw records)
- **Collaboration:** Custom sync engine (not Yjs), supports 50 concurrent users
- **Features:** Built-in undo/redo, extensible shapes/tools, geometry system for hit-testing
- **Strength:** Best open-source canvas framework for extensibility

#### Penpot (Open Source Design Tool)
- **Frontend:** ClojureScript + React
- **Rendering:** SVG-based
- **Collaboration:** WebSocket per file, presence events
- **Strength:** Works with open standards (SVG, CSS, HTML)

#### draw.io / diagrams.net
- **Tech:** Pure JavaScript, mxGraph-based, SVG rendering
- **Limit:** Does NOT support real-time collaborative editing
- **Strength:** Completely free, mature (886 releases)

#### Miro (Collaborative Whiteboard)
- **Rendering:** Canvas-based with AI features
- **Collaboration:** WebSocket-based real-time sync
- **Scale:** Large teams (100+)
- **Limitation:** Proprietary, limited public architecture details

### 1.2 Feature Matrix (All Products)

| Feature | Figma | Onshape | tldraw | Excalidraw | Penpot | draw.io |
|---------|-------|---------|--------|-----------|--------|---------|
| Rendering | WebGPU/WASM | WebGL | Canvas2D | Canvas2D | SVG | SVG |
| Max Objects | Millions | Unlimited (cloud) | ~5K | ~15K | Multiple | 5K |
| Collaboration | CRDT-inspired | Incremental | Custom sync | Pseudo-P2P | WebSocket | None |
| Concurrent Users | 100s | Multiple | 50 | Dozens | Multiple | 1 |
| Export | PNG, SVG, PDF | STEP, IGES, DWG, PDF | SVG, PNG | SVG, PNG, JSON | SVG, PNG, PDF | PNG, SVG, PDF |
| Offline | Partial | No | Yes (local-first) | Yes (PWA) | Partial | Yes |
| Mobile | Responsive web | Native iOS/Android | Responsive | Responsive | Responsive | Responsive |
| License | Proprietary | Proprietary | Source-available | MIT | MPL 2.0 | Apache 2.0 |
| Cloud Required | No | Yes | No | No | No | No |
| Custom Shapes | Limited | N/A | Full ShapeUtil | Limited | Limited | Limited |

---

## PART 2: RENDERING TECHNOLOGY DEEP DIVE

### 2.1 Rendering Stack Selection Guide

| Technology | GPU Accelerated | Best For | Object Limit | Learning Curve |
|-----------|----------------|---------|-------------|---------------|
| **SVG** | Partial | <1,000 objects, accessibility | ~1,000-5,000 | Easy |
| **Canvas 2D** | Partial (browser-dependent) | 1,000-10,000 objects | ~10,000-50,000 | Easy |
| **WebGL** | Yes (full GPU) | 10,000+ objects, effects | ~100,000+ | Steep |
| **WebGPU** | Yes (next-gen GPU API) | Compute shaders, max perf | ~1,000,000+ | Very Steep |
| **WASM + WebGL/WebGPU** | Yes | Maximum performance, CAD | Millions | Expert |

**Decision Logic:**
- **<1,000 objects, need CSS styling:** SVG (Penpot, draw.io)
- **1,000-10,000 objects, 2D drawing:** Canvas 2D (Excalidraw, tldraw)
- **10,000+ objects, precision CAD:** WebGL (custom or PixiJS)
- **Maximum performance, compute shaders:** WebGPU (Figma's 2025 direction)

### 2.2 Canvas 2D vs WebGL Benchmarks

From canvas-engines-comparison (8,000 moving rectangles, MacBook Pro 2019):

| Library | Chrome FPS | Firefox FPS | Safari FPS | Backend |
|---------|-----------|------------|------------|---------|
| **PixiJS (WebGL)** | **60** | **48** | 24 | WebGL |
| Konva.js | 23 | 7 | 19 | Canvas2D |
| **Raw Canvas2D** | 19 | 19 | 39 | Canvas2D |
| Fabric.js | 9 | 4 | 9 | Canvas2D |
| Paper.js | 16 | 6 | 16 | Canvas2D |
| Three.js | 8 | 7 | 4 | WebGL |

**Insight:** Pure WebGL achieves **60-120 FPS for 1,000,000 boxes** via GPU compute.

### 2.3 Figma's Rendering Evolution

```
2015: C++ -> asm.js -> WebGL (custom tile-based renderer)
2017: C++ -> WebAssembly -> WebGL (3x faster load time)
2025: C++ -> WebAssembly -> WebGPU (with WebGL fallback)
```

**Key Innovation:** Same C++ rendering engine, only compilation target changed. Enables:
- Near-native performance (no GC pauses)
- 32-bit memory layout instead of JS 64-bit doubles
- Reusable C++ codebase: browser (WASM) + server (native) rendering

### 2.4 Custom Renderer Components (What "Custom Renderer" Means)

Figma's renderer includes:
- **Custom DOM** — tree of design objects (not HTML)
- **Custom compositor** — layering, opacity, blend modes
- **Custom text layout engine** — consistent across browsers
- **Tile-based rendering** — only visible tiles re-rendered
- **Custom hit detection** — WebGL has no DOM events on pixels
- **Custom cursor management** — fixed browser inconsistencies

---

## PART 3: COLLABORATION ARCHITECTURE

### 3.1 Three Main Approaches

| Approach | Used By | Complexity | Centralized | Best For |
|----------|---------|-----------|-------------|---------|
| **OT (Operational Transform)** | Google Docs | Very High | Usually | Text editing |
| **CRDT (Conflict-free Replicated Data Types)** | Yjs, Automerge | High | No (P2P) | Decentralized systems |
| **CRDT-Inspired (simplified)** | Figma | Medium | Yes (server) | Design tools |
| **LWW + Version Numbers** | Excalidraw | Low | Relay only | Simple shared state |
| **Incremental Recording** | Onshape | Medium | Yes | CAD with full history |

### 3.2 Figma's CRDT-Inspired Approach (Recommended for Server-Centric CAD)

**Why not pure CRDT:** CRDTs add overhead for decentralized systems. Figma's centralized server allows simplification.

**How it works:**
1. Document = tree of objects with properties
2. **Last-writer-wins per PROPERTY** (not object) — conflicts only when two clients edit same property
3. **Fractional indexing** for ordering — position is fraction between 0 and 1; insert by averaging
4. **Parent link on child** — prevents multiple parents
5. **Server rejects cycles** — maintains tree validity
6. **Unique object IDs include client ID** — enables offline creation
7. **Flicker prevention** — discard incoming server changes that conflict with unacknowledged local changes

**Multiplayer undo innovation:**
- Undo modifies redo history at time of undo
- Redo modifies undo history at time of redo
- Prevents overwriting others' changes

### 3.3 Excalidraw's Approach (Simplest Viable)

1. Flat array of elements
2. **Union merge** — on receiving update, union all element IDs
3. **Tombstoning** — `isDeleted: true` instead of removing
4. **Version numbers** — each edit increments; merge keeps highest version
5. **versionNonce** — random integer breaks ties deterministically
6. E2E encrypted — server is just a relay

**Known limitation:** Undo/redo stack cleared on receiving updates from new peer.

### 3.4 Yjs Deep Dive (Recommended for Full-Featured CAD)

Yjs is a CRDT library that decouples data model from transport.

**Core Data Types:**
- **Y.Doc** — root container, holds all shared types
- **Y.Map** — key-value store (optimal for shape properties)
- **Y.Array** — ordered sequences (z-ordering, layer lists)
- **Y.Text** — rich text with inline formatting

**Key Operations:**
```javascript
const doc = new Y.Doc()
const shapes = doc.getMap('shapes')  // Nested Y.Maps for shape data
const layerOrder = doc.getArray('layerOrder')  // Ordered z-indices

// Atomic updates
doc.transact(() => {
  shapes.set('shape-001', shapeData)
  layerOrder.push('shape-001')
})  // Single update emitted, single undo step

// UndoManager for collaborative undo
const undoManager = new Y.UndoManager([shapes, layerOrder], {
  captureTimeout: 500  // Group changes within 500ms
})
undoManager.undo()  // Only undoes local changes
```

**Providers (Transport Layer):**
- **y-websocket** — central server relay (production standard)
- **y-webrtc** — peer-to-peer via WebRTC (no server, limits ~20 peers)
- **y-indexeddb** — offline persistence (browser IndexedDB)
- **y-redis** — scalable server using Redis + persistent storage

**Sub-documents** (critical for large CAD projects):
```javascript
const rootDoc = new Y.Doc()
const pages = rootDoc.getMap('pages')

// Each page is a sub-document loaded on demand
const page1Doc = new Y.Doc({ guid: 'page-1' })
pages.set('page-1', page1Doc)

rootDoc.on('subdocs', ({ loaded }) => {
  loaded.forEach(subdoc => {
    new WebsocketProvider('wss://server.com', subdoc.guid, subdoc)
  })
})
```

**Performance:**
- 100,000 text insertions encode to ~30KB (10-30x smaller than JSON)
- State vectors enable efficient differential sync
- Update merging compacts multiple messages

---

## PART 4: CANVAS LIBRARY COMPARISON

### 4.1 Top Contenders for CAD

#### Konva.js (Tier 1: Best for MVP CAD)
- **Architecture:** Scene graph with multi-layer support
- **Performance:** 5-10K objects at 60 FPS with optimization
- **Strengths:**
  - Excellent layer system (each layer = separate canvas)
  - Native React integration (`react-konva`)
  - Coordinate transformation utilities for zoom/pan
  - Good TypeScript support
- **Limitations:** Canvas2D ceiling, no SVG export, no undo/redo
- **Stars:** 11.5K, 700K npm downloads/week
- **License:** MIT

#### PixiJS (Tier 1: Best for Performance)
- **Architecture:** WebGL 2D renderer with scene graph
- **Performance:** 10,000-60,000+ objects at 60 FPS
- **Strengths:**
  - Pure rendering horsepower (60-120 FPS for 1M objects)
  - Batch rendering, texture atlases, GPU optimization
  - Modular plugin architecture
- **Limitations:**
  - Zero CAD abstractions (must build everything)
  - No state management, serialization, or undo
  - No vector export
- **Stars:** 44K, 1M+ npm downloads/week
- **License:** MIT
- **Best Use:** Performance-critical hot paths in hybrid architecture

#### tldraw SDK (Tier 1: Best for Features)
- **Architecture:** Custom reactive store + extensible canvas system
- **Performance:** Whiteboard-scale (~5K shapes)
- **Strengths:**
  - Built-in undo/redo with collaboration awareness
  - Extensible ShapeUtil system (custom shapes)
  - Custom tool system (StateNode)
  - Full geometry system for hit-testing
  - Signals-based reactivity (fine-grained updates)
  - Schema migrations
- **Limitations:**
  - Canvas2D ceiling (not WebGL)
  - Not designed for 10K+ precision elements
  - Requires understanding of custom shapes/tools
- **Stars:** 45K, 125K npm downloads/week
- **License:** Source-available (free non-commercial, commercial license for business)
- **Backed by:** $5M+ investment, production use (tldraw.com, ClickUp, Padlet)

#### Fabric.js (Tier 2: Good for Simple Apps)
- **Performance:** 200-500 interactive objects max
- **Best for:** Design tools, poster makers (not CAD)
- **Stars:** 29K, 250K npm downloads/week

#### Paper.js (Tier 2: Best Vector Math)
- **Strength:** Best path operations (boolean, intersection, offset)
- **Limitation:** Performance at scale, stagnating maintenance
- **Use Case:** Reference for vector math algorithms, not primary engine

#### Three.js 2D Mode (Not Recommended for Pure 2D)
- **Limitation:** Overkill for 2D, carries 3D pipeline overhead
- **Use Case:** Only if app needs 2D/3D hybrid (architectural walkthroughs)

### 4.2 Technology Selection Matrix

| Criteria | Fabric.js | Konva.js | PixiJS | Paper.js | tldraw |
|----------|-----------|----------|--------|----------|--------|
| Max Objects (60fps) | ~500 | ~5K | ~60K | ~1K | ~5K |
| Precise Measurements | None | None | None | Excellent | Basic |
| Snapping | None | None | None | None | Built-in |
| Layer System | Basic | Excellent | Basic | Good | Minimal |
| Undo/Redo | None | None | None | None | **Excellent** |
| Plugin System | Moderate | Good | Strong | Basic | **Excellent** |
| SVG Export | Excellent | None | None | Excellent | Good |
| DXF/DWG Export | External | External | External | External | External |
| Collaboration Ready | Manual | Manual | Manual | Manual | **Built-in** |
| CAD Grade | No | Partial | Engine-only | Math-only | **Yes** |

---

## PART 5: RECOMMENDED ARCHITECTURE

### 5.1 Three Implementation Tiers

#### Option A: Pragmatic Start (Recommended for MVP)

**Timeline:** 3-6 months
**Team:** 3-5 engineers

```
React Application
    |
    +-- tldraw SDK (canvas + state + undo/redo)
    |   +-- Custom ShapeUtils (walls, doors, windows, dimensions)
    |   +-- Custom Tools (wall-tool, door-tool, etc.)
    |   +-- tldraw sync server (Node.js or Cloudflare DO)
    |
    +-- CAD Tools Layer
        +-- Snap engine (grid, endpoint, midpoint)
        +-- Measurement display
        +-- Export pipeline (SVG, DXF)
```

**Pros:** Fast to market, sufficient for <5K objects, React ecosystem
**Cons:** Canvas2D ceiling, will need renderer upgrade eventually

**Stack Details:**
- Frontend: React + TypeScript + tldraw SDK
- State: tldraw store + custom side effects for constraints
- Sync: tldraw sync protocol (built-in) or Yjs bridge
- Server: Cloudflare Workers/DO or Node.js + y-websocket
- Persistence: SQLiteSyncStorage or PostgreSQL

---

#### Option B: Performance-First (For ambitious teams)

**Timeline:** 6-12 months
**Team:** 5-8 engineers with graphics experience

```
React Application
    |
    +-- Custom State Layer (signals-based, like tldraw)
    |   +-- Yjs Y.Doc for CRDT collaboration
    |   +-- History manager (command pattern on Y.UndoManager)
    |   +-- Spatial indexing (R-tree for hit detection)
    |
    +-- Hybrid Rendering Layer
    |   +-- PixiJS for geometry (WebGL, 60K+ objects)
    |   +-- Canvas2D overlay for UI (selection handles, cursors)
    |   +-- Viewport manager (tile-based culling)
    |
    +-- CAD Tools Layer
        +-- Snap engine
        +-- Constraint solver
        +-- Boolean operations (clipper2-js)
        +-- Export pipeline
```

**Pros:** 60K+ objects, WebGL performance, room to grow
**Cons:** Higher complexity, longer development, PixiJS has no CAD abstractions

---

#### Option C: Figma-Grade (For well-funded teams)

**Timeline:** 12-24 months
**Team:** 8-15 engineers (graphics, systems, performance specialists)
**Budget:** $500K+

```
React UI Layer
    |
    +-- WASM Module (Rust or C++ via Emscripten)
    |   +-- Document model (spatial indexing)
    |   +-- Geometry engine (boolean, offset, constraint solver)
    |   +-- Render commands (tile-based list)
    |
    +-- Custom WebGL/WebGPU Renderer
    |   +-- Tile-based engine
    |   +-- Instanced rendering for symbols
    |   +-- Custom shaders (hatching, dimensions)
    |   +-- Custom text engine
    |
    +-- Collaboration Server
        +-- CRDT with server authority
        +-- Presence awareness
        +-- Document versioning
```

**Pros:** Best-in-class performance, handles any scale
**Cons:** Requires systems programmers, 18-24 month development, high cost

---

### 5.2 Yjs + tldraw Integration (Best of Both Worlds)

**Approach 1: Use tldraw sync (Simpler)**
- tldraw's built-in sync protocol (not Yjs-based)
- First-class support, schema migrations, battle-tested
- Sufficient for MVP
- Limitation: Less flexibility for custom CRDT logic

**Approach 2: Bridge tldraw Store to Yjs (More Powerful)**
- tldraw records ↔ Yjs Y.Map bidirectional sync
- Enables shared CRDT model with other components
- Allows y-indexeddb for offline-first workflows
- More complex but flexible

**Bridge Architecture:**
```
tldraw Editor <-> Store <-> Yjs Bridge <-> Y.Doc <-> Provider <-> Server
```

**Bridge Implementation (Conceptual):**
```typescript
function createYjsBridge(doc: Y.Doc, store: TLStore) {
  const yStore = doc.getMap('tldraw-records')

  // Local changes -> Yjs
  store.listen((entry) => {
    doc.transact(() => {
      for (const record of Object.values(entry.changes.added)) {
        yStore.set(record.id, record)
      }
      for (const [, next] of Object.values(entry.changes.updated)) {
        yStore.set(next.id, next)
      }
      for (const record of Object.values(entry.changes.removed)) {
        yStore.delete(record.id)
      }
    })
  }, { source: 'user' })

  // Yjs -> tldraw store
  yStore.observe((event) => {
    store.mergeRemoteChanges(() => {
      event.changes.keys.forEach((change, key) => {
        if (change.action === 'add' || change.action === 'update') {
          const record = yStore.get(key)
          store.put([record])
        } else if (change.action === 'delete') {
          store.remove([key])
        }
      })
    })
  })
}
```

---

### 5.3 Recommended Full Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **UI Framework** | React + TypeScript | Industry standard, huge ecosystem |
| **Canvas Rendering** | tldraw SDK | Best Canvas2D + extensibility, $5M of work |
| **Rendering Upgrade** | PixiJS (when needed) | WebGL performance, 10x more objects |
| **State Management** | tldraw store + Yjs bridge | Signals reactivity + CRDT collaboration |
| **Collaboration** | Yjs + y-websocket | Proven CRDT, offline-first capable |
| **Undo/Redo** | Y.UndoManager | Collaborative-aware, only undoes local changes |
| **Vector Math** | Paper.js algorithms or clipper2-js | Path operations, booleans |
| **SVG Export** | Custom walker of scene graph | tldraw lacks native SVG export |
| **DXF Export** | dxf-writer npm package | Lightweight DXF generation |
| **DWG Import** | Server-side via ODA SDK or LibreDWG | No browser-side option |
| **Snapping** | Custom engine | No library provides CAD-grade snapping |
| **Server** | Node.js + y-websocket OR Cloudflare Workers + Durable Objects | Proven architectures |
| **Persistence** | PostgreSQL + update log | Scalable, queryable, preserves history |
| **Offline** | y-indexeddb | Yjs local-first persistence |

---

### 5.4 Custom CAD Shape Types (tldraw)

```typescript
// Example: CAD wall shape with custom snapping

declare module 'tldraw' {
  export interface TLGlobalShapePropsMap {
    'cad-wall': {
      length: number
      thickness: number
      material: string
      fireRating: string
    }
  }
}

type CadWallShape = TLShape<'cad-wall'>

class CadWallShapeUtil extends ShapeUtil<CadWallShape> {
  static override type = 'cad-wall' as const

  getGeometry(shape: CadWallShape): Geometry2d {
    return new Rectangle2d({
      width: shape.props.length,
      height: shape.props.thickness,
      isFilled: true,
    })
  }

  override onBeforeCreate(next: CadWallShape) {
    // Snap thickness to standard values (50mm increments)
    const snapped = Math.round(next.props.thickness / 50) * 50
    return { ...next, props: { ...next.props, thickness: snapped } }
  }

  component(shape: CadWallShape) {
    return (
      <div style={{
        width: shape.props.length,
        height: shape.props.thickness,
        background: '#888',
        border: '2px solid #333',
      }}>
        <span>{shape.props.thickness}mm • {shape.props.material}</span>
      </div>
    )
  }
}
```

**Built-in CAD Shapes to Implement:**
- `cad-wall` (Rectangle2d + snap to grid)
- `cad-door` (Arc2d for swing + Rectangle2d frame, bound to wall)
- `cad-window` (Rectangle2d, bound to wall)
- `cad-dimension` (Polyline2d, references two shapes)
- `cad-column` (Circle2d or Rectangle2d, structural)
- `cad-annotation` (Text + leader line via binding)

---

### 5.5 Implementation Phases (For MVP)

**Phase 1: Foundation (2-3 weeks)**
- Set up tldraw with React
- Implement 3-4 basic shapes (wall, door, window, dimension)
- Add custom tools for each
- Set up tldraw sync for basic collaboration

**Phase 2: Constraints & Intelligence (2-3 weeks)**
- Wall endpoint snapping (side effects)
- Door/window binding to walls
- Auto-dimensioning
- Grid and guideline snapping
- Undo/redo integration

**Phase 3: Collaboration (1-2 weeks)**
- User presence (cursors, selections, viewports)
- Conflict resolution testing
- Multi-page support

**Phase 4: Production Features (2-3 weeks)**
- Export (DXF, SVG, PDF)
- Layer management
- Symbol library
- Measurement & area calculation
- Print layout

---

## PART 6: KEY ARCHITECTURE PATTERNS

### 6.1 Hit Detection / Object Selection

**Methods (simplest to most complex):**

1. **Bounding box check** — fast but imprecise
2. **`isPointInPath` / `isPointInStroke`** — Canvas 2D API, good for filled shapes
3. **Tolerance padding** — temporarily increase lineWidth, then reset
4. **Spatial indexing** — R-tree, quadtree (essential for 10K+ objects)
5. **Color-picking / GPU** — render to offscreen with unique colors per object

**Critical:** Transform mouse (screen space) to canvas (world space) using zoom/pan matrix.

### 6.2 Zoom and Pan Implementation

**Standard approach (used by all libraries):**

```javascript
let scale = 1
let offsetX = 0
let offsetY = 0

// Apply before rendering
ctx.setTransform(scale, 0, 0, scale, offsetX, offsetY)

// Focal point zoom (zoom toward mouse)
function zoomAtPoint(mouseX, mouseY, newScale) {
  const worldX = (mouseX - offsetX) / scale
  const worldY = (mouseY - offsetY) / scale
  scale = newScale
  offsetX = mouseX - worldX * scale
  offsetY = mouseY - worldY * scale
}
```

**Best practices:**
- Use orthographic camera/projection model
- Track pinch gesture (Chrome: `wheel` + `ctrlKey`)
- Apply transform at render time, not to stored coordinates
- Clamp zoom (e.g., 0.01x to 100x)
- Only render objects within viewport bounds (frustum culling)

### 6.3 Undo/Redo in Collaborative Environments

**Three approaches:**

1. **Snapshot-based** — store entire state at each step (memory-heavy)
2. **Command Pattern** — store actions with execute/undo methods (most common)
3. **Differential** — store deltas between states (most efficient)

**Multiplayer complexity (Figma's insight):**
- "Inherently confusing" in multiplayer
- Principle: "Undo a lot, copy, redo back → document unchanged"
- Undo modifies redo history at undo time
- Redo modifies undo history at redo time

**Excalidraw's simpler approach:**
- Clear undo stack on receiving peer updates
- Acceptable for casual tool, not professional

**Yjs approach (recommended):**
- UndoManager only undoes local user's changes
- Other users' changes remain
- `captureTimeout` groups nearby changes into one undo step

### 6.4 Infinite Canvas Implementation

- Canvas element has FIXED pixel dimensions
- "Infinite" is illusion from zoom/pan transform
- **Viewport culling** — only render objects whose bounds intersect viewport
- **Level of detail (LOD)** — less detail when zoomed out
- **Tile-based rendering** (Figma) — divide world into tiles, render only visible
- Grid/background rendered relative to world coordinates, not screen

---

## PART 7: PERFORMANCE TARGETS

Based on industry leaders:

- **Initial load:** <3 seconds (Figma achieves with WASM caching)
- **Frame rate:** 60 FPS for pan/zoom/draw operations
- **Object count:** Handle 10,000+ objects smoothly
- **Collaboration latency:** <200ms for cursor position updates
- **Document size:** Support files up to 100MB
- **Concurrent users:** At least 10-20 per document

**For Canvas2D apps (tldraw, Konva):**
- Typical ceiling: 5,000-10,000 objects at 60 FPS
- Can push to 15K-20K with aggressive optimization

**For WebGL apps (PixiJS, custom):**
- Typical: 60,000+ objects at 60 FPS
- Max with GPU instancing: 1,000,000+ objects

---

## PART 8: STRATEGIC TAKEAWAYS

### 8.1 What Users Expect (2026 State of the Art)

A modern professional CAD tool MUST have:

1. **Infinite canvas** with smooth zoom/pan
2. **Real-time collaboration** — live cursors, presence, no file locking
3. **Undo/redo** that works correctly in multiplayer
4. **Export** to PNG, SVG, PDF (at minimum)
5. **Offline capability** — graceful degradation or full offline
6. **Responsive** — works on tablets
7. **Sub-100ms interaction latency**
8. **Auto-save** — no explicit save action

**Nice-to-haves:**
- Dark mode
- PWA support
- Shape libraries / components
- Keyboard shortcuts
- Copy/paste
- End-to-end encryption
- Version history
- Comments/annotations
- AI features

### 8.2 Open Source Building Blocks

If building a new CAD tool:

| Need | Option | Notes |
|------|--------|-------|
| Canvas framework | **tldraw SDK** | Most complete, $5M invested |
| Canvas alternative | **Konva.js** | Good for simpler tools |
| 2D rendering | **PixiJS** | WebGL, 60K+ objects |
| Vector math | Paper.js algorithms | Reference, not engine |
| Collaboration | **Yjs + y-websocket** | CRDT, offline-first |
| Multiplayer backend | **Cloudflare Durable Objects** | tldraw's production stack |
| Hand-drawn rendering | Rough.js | Sketchy aesthetic |
| Stroke algorithm | Perfect Freehand | Pressure-sensitive |
| DXF export | dxf-writer | Lightweight generation |

### 8.3 Decision Matrix for Your Project

| If You Have | Recommendation |
|-------------|---------------|
| <5K objects, <6 months deadline | Konva.js + custom CAD layer |
| 5K-15K objects, 6-12 months | tldraw SDK + Yjs bridge |
| 15K+ objects, CAD precision | PixiJS for rendering + custom state |
| $20M+, 2+ years, graphics team | Custom WASM + WebGL (Figma model) |
| Offline-first as requirement | Yjs + y-indexeddb |
| Need schema migrations | tldraw SDK (built-in) |
| Multiple apps share data model | Yjs (CRDT foundation) |

---

## PART 9: CRITICAL GOTCHAS & LESSONS

### 9.1 What NOT to Do

1. **Don't start with SVG** — breaks at >1K objects, re-tessellates on every zoom
2. **Don't build custom CRDT** — use Yjs instead; CRDTs are algorithmically complex
3. **Don't use WebGL** without graphics expertise — steep learning curve, many pitfalls
4. **Don't try to replicate Figma** — they have $20M+ and 5+ years
5. **Don't ignore collaboration from day 1** — hard to retrofit CRDT into existing architecture
6. **Don't serialize entire canvas state on every change** — memory explosion, slow persistence
7. **Don't use THREE.js for pure 2D** — overkill, carries 3D overhead
8. **Don't build custom transport layer** — use proven providers (y-websocket, tldraw sync)

### 9.2 Why Most CAD Apps Fail

1. **Chose wrong rendering technology** (SVG for 10K objects, Canvas2D for CAD precision)
2. **Built collaboration incorrectly** (last-write-wins instead of CRDT)
3. **No offline support** (expectation, not nice-to-have)
4. **Performance ceiling not identified early** (migrating renderers is expensive)
5. **Underestimated undo/redo complexity** (especially in multiplayer)
6. **Constraint solving hard-coded** (not generalizable, breaks with new features)
7. **No schema versioning** (can't evolve data model)

### 9.3 Lessons from Leaders

**Figma:**
- Invest in rendering infrastructure early (WASM + custom WebGL)
- Central server as authority simplifies CRDT significantly
- Same C++ codebase running browser (WASM) + server (native) is powerful pattern

**Onshape:**
- Geometry computation belongs on server, not client
- Incremental history as fundamental to storage (not bolted on)
- PDM is part of core architecture, not separate system

**tldraw:**
- Extensible shapes (ShapeUtil) enable CAD features
- Side effects system powerful for constraint enforcement
- Signals-based reactivity scales better than Redux

**Excalidraw:**
- Simplicity (flat element array) works for whiteboards
- E2E encryption is differentiator
- Hand-drawn aesthetic is NOT for CAD

---

## PART 10: FINAL RECOMMENDATION

### For a Professional CAD Application

**Recommended Stack:**
```
Frontend:  React + TypeScript + tldraw SDK
Sync:      Yjs (Y.Doc) + y-websocket bridge to tldraw
Rendering: Canvas2D via tldraw (upgrade to PixiJS at 5K+ objects)
State:     tldraw store + Yjs CRDT + custom side effects
Server:    Node.js + y-websocket + PostgreSQL
Offline:   y-indexeddb for browser persistence
Deployment: Vercel (frontend) + Railway/Fly.io (backend)
```

**Expected Timeline:**
- **MVP (basic shapes, single-user save):** 2-3 months
- **Collaboration & multiplayer:** 1-2 months additional
- **Production-grade (constraints, symbol libraries, export):** 3-4 months additional
- **Total to market-ready:** 6-12 months for experienced team

**Team:**
- 3-5 engineers for MVP
- +2 for production features (export, constraints, advanced UI)

**Cost Estimate:**
- Engineering: $300K-500K (6-12 months, 3-5 engineers)
- Infrastructure: $2K-5K/month (servers, databases)
- Total first year: ~$400K-600K

**Risk Areas:**
- Constraint solver complexity (underestimated in most projects)
- Performance wall at 5-10K objects (Canvas2D ceiling)
- Offline synchronization conflicts
- DWG/DXF interoperability

---

## APPENDIX A: Key Resources & Links

### Primary Documentation
- **Yjs:** https://docs.yjs.dev
- **tldraw:** https://tldraw.dev
- **y-websocket:** https://github.com/yjs/y-websocket
- **Konva.js:** https://konvajs.org
- **PixiJS:** https://pixijs.com

### Reference Implementations
- **tldraw examples:** https://examples.tldraw.com
- **tldraw + Cloudflare:** https://github.com/tldraw/tldraw-sync-cloudflare
- **tldraw + Yjs (WIP):** https://github.com/shahriar-shojib/tlsync-yjs
- **Excalidraw:** https://github.com/excalidraw/excalidraw

### Technical Papers & Blogs
- **Figma rendering:** https://www.figma.com/blog/building-a-professional-design-tool-on-the-web/
- **Figma WebAssembly:** https://www.figma.com/blog/webassembly-cut-figmas-load-time-by-3x/
- **Figma WebGPU:** https://www.figma.com/blog/figma-rendering-powered-by-webgpu/
- **Figma multiplayer:** https://www.figma.com/blog/how-figmas-multiplayer-technology-works/
- **Onshape architecture:** https://www.onshape.com/en/blog/how-does-onshape-really-work

---

## APPENDIX B: Quick Comparison Table

| Aspect | Konva.js | PixiJS | tldraw | Yjs |
|--------|----------|--------|--------|-----|
| **Best Use** | Canvas MVP | Performance hot paths | Full canvas framework | CRDT collaboration |
| **Learning Curve** | Easy | Medium | Medium | Medium |
| **Scale** | 5-10K objects | 60K+ objects | 5K objects | Unlimited |
| **Undo/Redo** | Manual | Manual | Built-in | Via UndoManager |
| **TypeScript** | Excellent | Excellent | Excellent | Excellent |
| **Ecosystem** | Small | Large | Growing | Moderate |
| **License** | MIT | MIT | Source-avail | MIT |
| **Production Ready** | Yes | Yes | Yes | Yes |
| **Time to MVP** | 2-3 weeks | 3-4 weeks | 1-2 weeks | 1-2 weeks |

---

## APPENDIX C: CAD-Specific Implementation Checklist

### Rendering
- [ ] Choose Canvas2D (tldraw) or WebGL (PixiJS)
- [ ] Implement viewport culling
- [ ] Set up zoom/pan with proper coordinate transforms
- [ ] Test performance at 5K objects
- [ ] Plan upgrade path to next rendering tier

### State Management
- [ ] Define data model (shape, binding, page, asset records)
- [ ] Set up Yjs Y.Doc or tldraw store
- [ ] Implement shape CRUD operations
- [ ] Test atomic multi-shape updates

### Collaboration
- [ ] Choose sync protocol (tldraw sync or Yjs)
- [ ] Set up WebSocket server
- [ ] Test offline → online reconciliation
- [ ] Verify conflict resolution (no data loss)
- [ ] Test multi-user concurrent edits

### CAD Features
- [ ] Implement snap engine (grid, endpoint, midpoint)
- [ ] Add dimension display
- [ ] Create custom shape types (walls, doors, etc.)
- [ ] Test constraint solving under concurrent edits
- [ ] Validate undo/redo in multiplayer

### Export
- [ ] SVG export (via scene graph walker)
- [ ] PNG export (canvas.toDataURL)
- [ ] DXF export (dxf-writer)
- [ ] PDF export (jsPDF or Puppeteer)

### Persistence
- [ ] Set up database (PostgreSQL recommended)
- [ ] Implement update log (append-only)
- [ ] Test snapshot + incremental load
- [ ] Verify version history

### Offline
- [ ] Set up y-indexeddb or localStorage
- [ ] Test offline editing
- [ ] Verify sync on reconnection
- [ ] Handle conflicts from offline changes

---

**End of Complete Summary**

This document synthesizes all findings from three comprehensive CAD research reports, providing a complete roadmap for building professional web-based collaborative CAD applications.
