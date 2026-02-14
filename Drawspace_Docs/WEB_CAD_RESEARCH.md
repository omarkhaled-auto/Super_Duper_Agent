# Web-Based CAD & Collaborative Drawing: State of the Art Research

**Date:** 2026-02-12
**Purpose:** Understand what "state of the art" looks like for web CAD — rendering, collaboration, architecture, and patterns.

---

## Table of Contents

1. [Product-by-Product Analysis](#1-product-by-product-analysis)
2. [Feature Matrix](#2-feature-matrix)
3. [Rendering Technology Deep Dive](#3-rendering-technology-deep-dive)
4. [Collaboration Architecture Deep Dive](#4-collaboration-architecture-deep-dive)
5. [Core Implementation Patterns](#5-core-implementation-patterns)
6. [Key Architecture Questions Answered](#6-key-architecture-questions-answered)
7. [Strategic Takeaways](#7-strategic-takeaways)

---

## 1. Product-by-Product Analysis

### 1.1 Figma (Gold Standard — Design Tool)

**Rendering:**
- **C++ core** cross-compiled to WebAssembly (was asm.js before 2017)
- Custom **tile-based WebGL rendering engine** — NOT using Canvas 2D, SVG, or HTML
- As of September 2025, migrated to **WebGPU** (successor to WebGL) with dynamic fallback to WebGL
- Custom DOM, custom compositor, custom text layout engine — "basically a browser inside a browser"
- All rendering is GPU-accelerated and fully anti-aliased
- Supports masking, blurring, dithered gradients, blend modes, nested layer opacity
- Shader processing: maintains GLSL shaders, auto-converts to WGSL (WebGPU's shading language) via custom processor + open-source `naga` tool
- Uses Emscripten to compile C++ to WASM; also compiles same C++ to native x64/arm64 for server-side rendering

**Performance:**
- WebAssembly reduced load time by **3x** over asm.js
- WASM binary format parses **20x faster** than asm.js
- Compact 32-bit floats instead of JS 64-bit doubles
- No GC pauses — C++ memory management via pre-allocated typed arrays
- Uniform buffer batching for WebGPU — encodes multiple draw calls, uploads all uniform data at once, then submits

**Collaboration:**
- **Client/server architecture** over WebSockets
- NOT using true CRDTs or OTs — uses a **custom system inspired by CRDTs** but simplified because of centralized server authority
- Document is a tree of objects: `Map<ObjectID, Map<Property, Value>>`
- **Last-writer-wins per property** — conflicts happen only when two clients change the same property on the same object
- Changes are atomic at the property boundary
- **Fractional indexing** for child ordering — positions are fractions between 0 and 1; insert between two objects by averaging
- Parent-child relationships stored as parent link on the child (prevents multiple parents)
- Server rejects parent updates that would create cycles
- Offline support: downloads fresh copy on reconnect, reapplies offline edits on top
- Multiplayer undo: undo modifies redo history at time of undo (and vice versa) to prevent overwriting others' changes
- Separate per-document server process; Rust used for production multiplayer servers
- Flicker prevention: discard incoming server changes that conflict with unacknowledged local property changes

**Pricing:** Free tier (3 projects, 3 pages), Professional $15/editor/month, Organization $45/editor/month, Enterprise custom.

### 1.2 Onshape (PTC — Full CAD in Browser)

**Architecture:**
- **NOT a screen-scraping approach** — written from scratch for cloud
- Collection of microservices: auth servers, document servers, geometry servers
- **Geometry servers** do all math — feature list reconstruction, assembly solving, graphical tessellation
- Uses **Parasolid** kernel (from Siemens PLM) and **D-Cubed** constraint solver
- Client receives **triangles, not CAD models** — rendered via WebGL (browser) or OpenGL (mobile)
- Custom renderers (not third-party scenegraph libraries)
- Data stored in a **database, not files** — no explicit "save" action
- Every change recorded as an **increment** — old data never erased or overwritten
- Version tagging is trivial: just add a tag at a point in history
- Increments are designed to apply to any document state — enables seamless merge of multiple users' work
- PDM (Product Data Management) built into the fundamental data format

**Collaboration:**
- Client communicates via HTTPS/REST and WebSocket using custom wire protocol
- Multiple users can edit simultaneously — increments can be reconciled
- No file check-out/lock required (though access can be restricted)
- "Follow mode" — watch what another user is doing in real time

**Performance:**
- Minimal client hardware requirements — computation on cloud servers
- WebGL for browser rendering; OpenGL ES for mobile apps
- Native iOS and Android apps (built from scratch, not web wrappers)

**Pricing:** Free (limited, public documents), Professional ~$1,500/user/year, Enterprise custom. Discovery Program: up to 6 months free trial of Professional.

### 1.3 AutoCAD Web

**Architecture:**
- Autodesk's web version of AutoCAD — still in relative infancy
- Browser-based DWG editor
- Server-side processing for heavy operations
- Limited feature set compared to desktop AutoCAD
- Primarily 2D drafting capabilities
- Part of Autodesk's broader cloud-first strategy

**Technology:** Specific stack details not publicly documented in depth. Uses cloud rendering and WebGL for display.

### 1.4 BricsCAD

**Architecture:**
- **Desktop-first** application (Windows, macOS, Linux) — no true web version
- Written in C++ with native DWG file format support
- Single platform supporting 5 product levels: Lite (2D), Pro (3D), BIM, Mechanical, Ultimate
- Uses their own modeling kernel and constraint solver
- Not a web app — does not have a browser-based editor
- V25.2 is latest release with enhanced CAD workflows

**Note:** BricsCAD is NOT a web-based tool. It's a traditional desktop CAD application. Included for completeness as it competes in the CAD space but does NOT represent a web architecture pattern.

### 1.5 Excalidraw (Open Source — Whiteboard)

**Architecture:**
- **React + TypeScript** (93.9% TypeScript codebase)
- Renders via **HTML Canvas 2D** using **Rough.js** library for hand-drawn aesthetic
- No WebGL — achieves good performance with Canvas 2D for its use case (dozens to hundreds of shapes, not thousands)
- MIT licensed, 117k GitHub stars, 353 contributors

**Data Model:**
- Array of `ExcalidrawElement` objects in Z-index order
- Each element has: `id`, `type`, `width`, `height`, position, style properties
- Separated serializable state from UI state (`canvas` element, `isSelected` moved out)
- **Tombstoning** for deletes — `isDeleted` flag instead of removing from array
- **Version numbers** on elements — merge takes highest version
- **versionNonce** (random integer) for deterministic tie-breaking when same version
- Undo/redo stack cleared on receiving updates from new peer (known limitation)

**Collaboration:**
- **Pseudo-P2P model** — central server relays end-to-end encrypted messages
- Socket.IO over WebSockets with auto-reconnection, binary support, room support
- State merging: on receiving update, take union of local and incoming elements by ID
- End-to-end encryption — server stores nothing
- No server-side coordination

**Features:**
- Infinite canvas, hand-drawn style, dark mode
- PWA support (works offline), local-first (autosaves to browser)
- Export to PNG, SVG, clipboard, `.excalidraw` JSON
- Shape libraries, i18n (localization), arrow binding & labeled arrows
- Zoom, pan, undo/redo

**Pricing:** Free and open source. Excalidraw+ (hosted) has paid tiers for teams.

### 1.6 tldraw (Open Source — Infinite Canvas SDK)

**Architecture:**
- **React + TypeScript** SDK for building infinite canvas apps
- High-performance **signals library** and **record store** for state management
- Custom sync engine for multiplayer — supports up to **50 concurrent users**
- OpenGL mini-map component
- Full geometry system for hit-testing
- $5M invested over 3 years — "thousands of table-stakes features"
- Production-ready multiplayer backend using **Cloudflare Durable Objects** + WebSockets

**Key Features:**
- Selection and transformation with nested transforms
- Cross-tab sync, copy/paste, undo/redo out of the box
- Dark mode, accessibility (screen reader, keyboard navigation)
- Drag and drop, alignment/distribution, reordering system
- Complete UI library (toolbars, menus)
- Custom shapes, tools, and UI extensible

**Adopters:** ClickUp, Padlet, Mobbin, Jam.dev, and many others

**Pricing:** Open source (source-available license). Commercial licenses for enterprise use.

### 1.7 draw.io / diagrams.net

**Architecture:**
- **Pure JavaScript** client-side editor (98.5% JavaScript)
- Originally built on **mxGraph** library (now evolved/maintained internally)
- Apache 2.0 license, 3.6k GitHub stars
- Entirely human-written by core team — no AI generation, no PRs accepted
- **Does NOT support real-time collaborative editing** currently (noted explicitly in README)
- Available as: web app, Docker image, Desktop (Electron)
- XML-based diagram format
- 886 releases, very mature codebase

**Technology:**
- SVG-based rendering (via mxGraph)
- Client-side only — no server-side processing for diagram editing
- Integrations with Google Drive, OneDrive, Confluence, etc.
- .war files available for self-hosting

**Pricing:** Completely free.

### 1.8 Penpot (Open Source — Design Tool)

**Architecture:**
- Frontend: **ClojureScript** with React (via rumext library)
- Backend: **Clojure** on JVM — shares code/data structures with frontend
- Database: **PostgreSQL**
- Standard SPA architecture
- SVG-based rendering (native web standards)
- Custom RPC-style API: frontend sends function name + arguments over HTTP
- Web worker for expensive operations (thumbnails, geometric index for snaps)

**Collaboration:**
- WebSocket per file for real-time sync
- Presence events: connection, disconnection, mouse movements
- Changes by other users received and applied in real time
- Redux-like event loop (potok library) with global state + event stream

**Frontend Structure:**
- `store` — global state with event loop (Redux-like)
- `refs` — RX streams for subscribing to state parts
- `streams` — derived streams for keyboard/mouse events
- `repo` — backend API calls
- Worker: selection (geometric index), snaps (distance index), thumbnails, import/export

**Key Differentiators:**
- Works with **open standards**: SVG, CSS, HTML, JSON
- Built-in code inspection (CSS output)
- Self-hostable
- Free and open source

**Pricing:** Free (cloud hosted or self-hosted). Paid plans for teams with extra features.

### 1.9 Miro (Collaborative Whiteboard)

**Architecture:**
- Proprietary, closed-source
- Canvas-based rendering (HTML5 Canvas)
- Real-time collaboration supporting large teams
- "Intelligent Canvas" with AI features
- WebSocket-based real-time sync
- Specific technical architecture details not publicly shared

**Pricing:** Free (limited boards), Starter $10/member/month, Business $20/member/month, Enterprise custom.

---

## 2. Feature Matrix

| Product | Rendering Tech | Collaboration Model | Max Users | Export Formats | Offline | Mobile | License |
|---------|---------------|---------------------|-----------|---------------|---------|--------|---------|
| **Figma** | WebGPU/WebGL (C++/WASM) | Client/server, CRDT-inspired, WebSocket | Unlimited (practical ~100s) | PNG, SVG, PDF, Figma | Partial (offline editing, sync on reconnect) | Responsive web (no native) | Proprietary |
| **Onshape** | WebGL (custom renderer) | Client/server, incremental, WebSocket | Multiple concurrent | STEP, IGES, Parasolid, STL, DWG, PDF | No (cloud-required) | Native iOS/Android | Proprietary |
| **AutoCAD Web** | WebGL (cloud rendering) | Cloud-based | Limited | DWG, PDF | Limited | Responsive web | Proprietary |
| **BricsCAD** | Native OpenGL (desktop) | N/A (desktop) | N/A | DWG, DXF, PDF, STEP, etc. | Yes (desktop) | No | Proprietary |
| **Excalidraw** | Canvas 2D + Rough.js | P2P via Socket.IO, E2E encrypted | ~Dozens | PNG, SVG, JSON (.excalidraw) | Yes (PWA) | Responsive web | MIT |
| **tldraw** | Canvas 2D (custom) | Custom sync engine, Cloudflare DO | Up to 50 | PNG, SVG, JSON | Yes (local-first) | Responsive web | Source-available |
| **draw.io** | SVG (mxGraph) | None (single user) | 1 | PNG, SVG, PDF, XML, VSDX | Yes (offline) | Responsive web | Apache 2.0 |
| **Penpot** | SVG (native) | WebSocket per file | Multiple concurrent | SVG, PNG, PDF, Penpot | Partial | Responsive web | MPL 2.0 |
| **Miro** | Canvas 2D | WebSocket, proprietary | Large teams (100+) | PNG, PDF, JPEG | Partial | Native iOS/Android | Proprietary |

---

## 3. Rendering Technology Deep Dive

### 3.1 Canvas 2D vs SVG vs WebGL vs WebGPU

| Technology | GPU Accelerated | Best For | Object Limit | Learning Curve |
|-----------|----------------|---------|-------------|---------------|
| **SVG** | Partial (browser-dependent) | <1,000 objects, accessibility, CSS styling | ~1,000-5,000 | Easy |
| **Canvas 2D** | Partial (some browsers) | 1,000-10,000 objects, simple 2D | ~10,000-50,000 | Easy |
| **WebGL** | Yes (full GPU) | 10,000+ objects, 3D, complex effects | ~100,000+ | Steep (GLSL shaders) |
| **WebGPU** | Yes (modern GPU API) | Next-gen, compute shaders, max perf | ~1,000,000+ | Very Steep |
| **WASM + WebGL/WebGPU** | Yes | Maximum performance, complex CAD | Millions | Expert (C++/Rust) |

**Key Findings:**

1. **SVG** (used by Penpot, draw.io): Good for diagramming/design tools where individual elements need DOM accessibility. Breaks down at scale. Each element is a DOM node — re-tessellated on zoom. Inconsistent GPU acceleration.

2. **Canvas 2D** (used by Excalidraw, tldraw, Miro): Sweet spot for whiteboard/drawing apps. Immediate-mode rendering. Must re-upload all geometry every frame. Good enough for hundreds to low thousands of objects. Libraries like Fabric.js and Konva.js add object management, hit detection, and interactivity.

3. **WebGL** (used by Figma originally, Onshape): Required for professional tools with 10K+ objects. Full GPU pipeline access. Significant development complexity — need GLSL shader programming, custom hit detection, custom text rendering. Figma built an entire browser rendering stack from scratch.

4. **WebGPU** (Figma's current): Next generation. Eliminates WebGL's global state bugs. Enables compute shaders (move CPU work to GPU). Better error handling (async, descriptive). Figma built dynamic fallback system: start with WebGPU, fall back to WebGL mid-session if needed. Still Chrome-only for broad support.

5. **WASM** (Figma, Onshape server): Cross-compile C++/Rust to run in browser at near-native speed. Figma's C++ core compiles to WASM for browser AND to native for server-side rendering. 32-bit memory layout, no GC pauses, LLVM optimization.

### 3.2 Figma's Rendering Evolution

```
2015: C++ -> asm.js -> WebGL (custom tile-based renderer)
2017: C++ -> WebAssembly -> WebGL (3x faster load)
2025: C++ -> WebAssembly -> WebGPU (with WebGL fallback)
```

Each transition preserved the same C++ rendering engine — only the compilation target and graphics API changed.

### 3.3 What "Custom Renderer" Means

Figma's renderer includes:
- **Custom DOM** — tree of design objects (not HTML DOM)
- **Custom compositor** — manages layering, opacity, blend modes
- **Custom text layout engine** — consistent across browsers (native text layout is inconsistent between browsers/platforms)
- **Tile-based rendering** — divide viewport into tiles, render only visible tiles
- **Custom hit detection** — since WebGL has no DOM events on rendered content
- **Custom cursor management** — had to fix cursor bugs in Chrome, Firefox, and WebKit

---

## 4. Collaboration Architecture Deep Dive

### 4.1 The Three Main Approaches

| Approach | Used By | Complexity | Centralized? | Best For |
|----------|---------|-----------|-------------|---------|
| **OT (Operational Transform)** | Google Docs | Very High | Usually | Text editing |
| **CRDT (Conflict-free Replicated Data Types)** | Yjs, Automerge | High | No (peer-to-peer) | Decentralized systems |
| **CRDT-Inspired (simplified)** | Figma | Medium | Yes (server authority) | Design tools with server |
| **Last-Writer-Wins + Version Numbers** | Excalidraw | Low | Relay only | Simple shared state |
| **Incremental Recording** | Onshape | Medium | Yes | CAD with full history |

### 4.2 Figma's Approach in Detail

**Why not OTs:** Too complex for design tools. OTs have combinatorial explosion of possible states. Good for text but overkill for design objects.

**Why not pure CRDTs:** CRDTs are designed for decentralized systems with no central authority. This adds performance/memory overhead. Since Figma has a central server, they can simplify.

**What Figma actually does:**
1. Document = tree of objects, each with properties
2. **Last-writer-wins per property** (not per object) — server defines ordering
3. **Fractional indexing** for ordering children — position is a fraction between 0 and 1
4. **Parent link on child** — prevents multiple-parent conflicts
5. **Server rejects cycles** — client temporarily removes cycling objects from tree
6. **Unique object IDs** include client ID — enables offline creation without server coordination
7. **Flicker prevention** — discard incoming server changes that conflict with unacknowledged local changes

### 4.3 Excalidraw's Approach in Detail

**Simplest viable approach for a whiteboard:**
1. Share array of elements between peers
2. **Union merge** — on receiving update, take union of all element IDs
3. **Tombstoning** — `isDeleted: true` instead of removing (prevents resurrection)
4. **Version numbers** — each edit increments version; merge keeps highest version
5. **versionNonce** — random integer breaks ties deterministically (lower wins)
6. E2E encrypted — server is just a relay

**Known limitation:** Undo/redo stack cleared on receiving updates from new peer.

### 4.4 tldraw's Approach

- Custom **sync engine** — not a generic CRDT library
- **Signals-based** reactive state (like Solid.js signals)
- Record store — database-like API for managing shape data
- Multiplayer via **Cloudflare Durable Objects** — each room is a DO instance
- WebSocket connections managed by DO
- Supports up to **50 concurrent users**

### 4.5 Onshape's Approach

- Every change is an **increment** applied to the document
- Increments are designed to **apply to any state** — enables merge of concurrent work
- Old data never overwritten — full version history is built into data format
- PDM (version management) is not a separate system — it IS the storage model
- Server processes per-document for multiplayer sessions

---

## 5. Core Implementation Patterns

### 5.1 Hit Detection / Object Selection

**Methods (from simplest to most complex):**

1. **Bounding box check** — check if point is inside rectangle around each object. Fast but imprecise for non-rectangular shapes.

2. **`context.isPointInPath(path, x, y)`** — Canvas 2D API. Checks if point is inside a filled path. Good for filled shapes.

3. **`context.isPointInStroke(path, x, y)`** — Canvas 2D API. Checks if point is on the stroke of a path. Good for lines/outlines.

4. **Tolerance/padding** — Temporarily increase `lineWidth` before `isPointInStroke` check, then reset. Provides larger hit target without changing visual output.

5. **Spatial indexing** — R-tree, quadtree, or grid-based index for O(log n) hit detection instead of O(n). Essential for 10K+ objects.

6. **Color-picking / GPU hit detection** — Render each object with a unique color to an offscreen buffer. Read pixel at mouse position to identify object. Used by some WebGL apps.

**Coordinate translation** is essential: mouse event coordinates (`clientX/Y`) must be transformed to canvas coordinates accounting for:
- Canvas element offset in the page
- Canvas element scaling (CSS size vs pixel size)
- Current zoom/pan transformation matrix

### 5.2 Undo/Redo

**Three main approaches:**

1. **Snapshot-based** — Store entire canvas/document state at each step. Simple but memory-heavy. Used for very simple apps.

2. **Command Pattern** — Store commands (actions) in a stack. Each command has `execute()` and `undo()`. Most common for professional tools.
   - Undo stack + redo stack
   - On action: push to undo stack, clear redo stack
   - On undo: pop from undo stack, push to redo stack (with current state)
   - On redo: pop from redo stack, push to undo stack

3. **Differential** — Store only the delta/diff between states. Most memory-efficient.

**Multiplayer undo complexity (Figma's insight):**
- Undo in multiplayer is "inherently confusing"
- Figma's principle: "if you undo a lot, copy something, and redo back to the present, the document should not change"
- Undo modifies redo history at time of undo
- Redo modifies undo history at time of redo
- This prevents overwriting other users' changes

### 5.3 Zoom and Pan

**Transform matrix approach (industry standard):**

```javascript
// Maintain a transformation matrix
let scale = 1;
let offsetX = 0;
let offsetY = 0;

// Apply before rendering
ctx.setTransform(scale, 0, 0, scale, offsetX, offsetY);

// Zoom toward mouse position (focal point zoom):
// 1. Get mouse position in world coordinates
// 2. Apply new scale
// 3. Adjust offset so mouse world position stays under cursor

function zoomAtPoint(mouseX, mouseY, newScale) {
  const worldX = (mouseX - offsetX) / scale;
  const worldY = (mouseY - offsetY) / scale;
  scale = newScale;
  offsetX = mouseX - worldX * scale;
  offsetY = mouseY - worldY * scale;
}
```

**Best practices:**
- Use **orthographic camera/projection** model — modify camera, not individual points
- Track pinch gesture on trackpad (Chrome: `wheel` event with `ctrlKey`)
- Apply transform at render time, not to stored coordinates
- Clamp zoom to reasonable range (e.g., 0.01x to 100x)
- Only render objects within viewport bounds (frustum culling)

### 5.4 Infinite Canvas

**Key implementation details:**
- Canvas element has FIXED pixel dimensions — "infinite" is an illusion from zoom/pan
- World coordinates are unbounded; screen coordinates are mapped via transform matrix
- **Viewport culling** — only render objects whose bounding boxes intersect the viewport
- **Level of detail (LOD)** — render less detail when zoomed out
- **Tile-based rendering** (Figma) — divide world into tiles, render only visible tiles
- Grid/background pattern must be rendered relative to world coordinates, not screen

### 5.5 Canvas Libraries Ecosystem

| Library | Type | Best For | Stars |
|---------|------|---------|-------|
| **Fabric.js** | Canvas 2D with object model | Interactive drawing, object manipulation | 28K |
| **Konva.js** | Canvas 2D with layering | Performance-sensitive 2D apps | 11K |
| **Paper.js** | Canvas 2D vector graphics | Complex vector operations | 14K |
| **PixiJS** | WebGL 2D renderer | High-performance 2D (games, viz) | 44K |
| **Three.js** | WebGL 3D renderer | 3D scenes and models | 103K |
| **Rough.js** | Canvas 2D sketchy rendering | Hand-drawn aesthetic | 20K |
| **Perfect Freehand** | Stroke algorithm | Pressure-sensitive drawing | 4K |

---

## 6. Key Architecture Questions Answered

### Q: Canvas 2D vs SVG vs WebGL — which should you use?

**Answer:** It depends on object count and visual complexity:
- **< 1,000 objects, need accessibility/CSS:** SVG (Penpot, draw.io model)
- **1,000-10,000 objects, 2D drawing:** Canvas 2D (Excalidraw, tldraw model)
- **10,000+ objects, complex effects, 3D:** WebGL (Figma, Onshape model)
- **Maximum performance, compute shaders:** WebGPU (Figma's latest)

For a **CAD-focused** drawing tool with precision requirements, Canvas 2D is the pragmatic starting point. Migrate to WebGL only when object counts or visual requirements demand it.

### Q: How do you handle performant rendering of many objects?

**Answer:** Combine these techniques:
1. **Viewport culling** — don't render objects outside the visible area
2. **Spatial indexing** (R-tree, quadtree) — O(log n) queries for visible objects
3. **Dirty rectangle tracking** — only re-render changed regions
4. **Object caching** — render complex objects to offscreen canvases, composite them
5. **Level of detail** — simplify rendering at low zoom levels
6. **Batch rendering** — minimize state changes and draw calls
7. **Web Worker** — offload expensive calculations (Penpot does this for snap points and geometric indexing)

### Q: What's the right collaboration architecture?

**Answer:** For a web app with a server:
1. **Start simple** — Excalidraw's version-number approach works for < 50 users
2. **Figma's CRDT-inspired approach** — ideal when you have a central server and need property-level conflict resolution
3. **Full CRDTs** (Yjs, Automerge) — only if you need decentralized/peer-to-peer
4. **OTs** — only if building a text editor (overkill for design/drawing tools)

Key insight from Figma: "Since Figma is centralized, we can simplify by removing the overhead of true CRDTs."

### Q: How do you implement object selection / hit detection on Canvas?

**Answer:**
1. Maintain a **spatial index** of all objects (R-tree or quadtree)
2. On mouse event, query spatial index for objects near cursor
3. For precise detection, use `isPointInPath` / `isPointInStroke` with tolerance padding
4. Transform mouse coordinates from screen space to world space before checking
5. For WebGL: use **color-picking** — render to offscreen buffer with unique colors per object

### Q: How do you implement undo/redo in a collaborative environment?

**Answer:**
1. Use **Command Pattern** — each action has execute/undo methods
2. In multiplayer, undo should only reverse YOUR actions, not others'
3. Figma's rule: "undo a lot, copy, redo back — document should not change"
4. Excalidraw's simpler approach: clear undo stack on receiving peer updates (acceptable for casual tool, not for professional tool)

---

## 7. Strategic Takeaways

### 7.1 Architecture Tiers

**Tier 1 — Simple Drawing Tool (Excalidraw-level):**
- React + TypeScript
- Canvas 2D rendering
- JSON document model (array of elements)
- Socket.IO for collaboration
- Version numbers for conflict resolution
- Local storage for persistence
- ~6 months to build core

**Tier 2 — Professional Design Tool (tldraw-level):**
- React + TypeScript SDK
- Canvas 2D with custom rendering pipeline
- Signals-based reactive state
- Custom sync engine
- Cloudflare Durable Objects or similar for multiplayer backend
- Full undo/redo, copy/paste, selection system
- ~2-3 years, ~$5M (tldraw's own estimate)

**Tier 3 — Enterprise CAD Tool (Figma-level):**
- C++/Rust core compiled to WASM
- Custom WebGL/WebGPU renderer
- Custom text engine, compositor, DOM
- CRDT-inspired sync with central server
- Rust backend for multiplayer servers
- ~4-5 years, $20M+ to reach production quality

**Tier 4 — Full 3D CAD (Onshape-level):**
- Geometric modeling kernel (Parasolid or equivalent)
- Server-side computation with client rendering
- Microservice architecture
- Full PDM built into storage model
- ~5-10 years, $100M+

### 7.2 What Users Expect (2026 State of the Art)

Based on this research, a modern web-based drawing/CAD tool MUST have:

1. **Infinite canvas** with smooth zoom/pan (touchpad pinch, scroll wheel, drag)
2. **Real-time collaboration** — live cursors, presence indicators, no file locking
3. **Undo/redo** that works correctly in multiplayer
4. **Export** to at least PNG, SVG, PDF
5. **Offline capability** — at minimum graceful degradation
6. **Responsive** — works on tablets (not necessarily phone-optimized)
7. **Sub-100ms interaction latency** for drawing operations
8. **Auto-save** — no explicit save action

Nice-to-haves that differentiate:
- Dark mode
- PWA support
- Shape libraries / component reuse
- Keyboard shortcuts
- Copy/paste (including cross-app)
- End-to-end encryption
- Version history
- Comments/annotations
- AI features (Miro's direction)

### 7.3 Open Source Building Blocks

If building a new web drawing/CAD tool, consider these foundations:

| Need | Open Source Option | Notes |
|------|-------------------|-------|
| Canvas framework | **tldraw SDK** | Most complete, React-native, $5M of work done |
| Canvas framework (alt) | **Excalidraw** as npm package | Good for embedding, hand-drawn style |
| 2D rendering library | **Konva.js** or **Fabric.js** | Object model on Canvas 2D |
| High-perf 2D | **PixiJS** | WebGL-based 2D renderer |
| Collaboration/sync | **Yjs** or **Automerge** | Full CRDT implementations |
| Collaboration (simple) | **Socket.IO** + custom logic | Excalidraw's approach |
| Multiplayer backend | **Cloudflare Durable Objects** | tldraw's production stack |
| Hand-drawn rendering | **Rough.js** | Sketchy/hand-drawn aesthetic |
| Stroke algorithm | **Perfect Freehand** | Pressure-sensitive stroke rendering |
| Design tool foundation | **Penpot** (fork) | Full design tool, ClojureScript |

### 7.4 Performance Benchmarks to Target

Based on industry leaders:
- **Initial load:** < 3 seconds (Figma achieves this with WASM caching)
- **Frame rate:** 60 FPS for pan/zoom/draw operations
- **Object count:** Handle 10,000+ objects smoothly
- **Collaboration latency:** < 200ms for cursor position updates
- **Document size:** Support files up to 100MB
- **Concurrent users:** At least 10-20 per document

---

## Sources

### Primary Sources (scraped and analyzed)
- Figma Blog: "Building a professional design tool on the web" (2015) — https://www.figma.com/blog/building-a-professional-design-tool-on-the-web/
- Figma Blog: "WebAssembly cut Figma's load time by 3x" (2017) — https://www.figma.com/blog/webassembly-cut-figmas-load-time-by-3x/
- Figma Blog: "Figma Rendering: Powered by WebGPU" (2025) — https://www.figma.com/blog/figma-rendering-powered-by-webgpu/
- Figma Blog: "How Figma's multiplayer technology works" (2019) — https://www.figma.com/blog/how-figmas-multiplayer-technology-works/
- Onshape Blog: "How Does Onshape Really Work?" (2018) — https://www.onshape.com/en/blog/how-does-onshape-really-work
- Excalidraw GitHub: https://github.com/excalidraw/excalidraw
- Excalidraw Blog: "Building Excalidraw's P2P Collaboration Feature" (2020) — https://plus.excalidraw.com/blog/building-excalidraw-p2p-collaboration-feature
- tldraw SDK: https://tldraw.dev/
- tldraw GitHub: https://github.com/tldraw/tldraw
- draw.io GitHub: https://github.com/jgraph/drawio
- Penpot Architecture: https://help.penpot.app/technical-guide/developer/architecture/
- Penpot Frontend Architecture: https://help.penpot.app/technical-guide/developer/architecture/frontend/
- AlterSquare: "WebGL vs Canvas: Best Choice for Browser-Based CAD Tools" — https://altersquare.io/webgl-vs-canvas-best-choice-for-browser-based-cad-tools/
- Joshua Tzucker: "Canvas Hit Detection Methods" — https://joshuatz.com/posts/2022/canvas-hit-detection-methods/

### Secondary Sources (search results analyzed)
- LibreCAD GitHub (C++/Qt desktop app): https://github.com/LibreCAD/LibreCAD
- BricsCAD: https://www.bricsys.com/ (desktop-only, not web)
- Miro: https://miro.com/ (proprietary, limited public architecture info)
- Onshape Pricing: https://www.onshape.com/en/pricing
