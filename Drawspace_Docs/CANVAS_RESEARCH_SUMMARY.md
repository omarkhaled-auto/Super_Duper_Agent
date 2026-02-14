# Canvas Engine & Collaborative CAD Research — Complete Summary

**Date**: 2026-02-12
**Scope**: Comprehensive technology evaluation for professional CAD-like collaborative drawing application
**Status**: Final research synthesis with actionable recommendations

---

## Executive Overview

Four detailed research documents were compiled analyzing canvas engines, rendering performance, collaboration frameworks, and architecture patterns:

1. **CAD_CANVAS_ENGINE_RESEARCH.md** — 10 technologies compared across 9 evaluation criteria
2. **COLLABORATIVE_CAD_RESEARCH.md** — Deep dives into Yjs, tldraw, Excalidraw, and integration patterns
3. **WEB_CAD_RESEARCH.md** — WebGL vs Canvas trade-offs and optimization techniques
4. **DWG_DXF_EXPORT_RESEARCH.md** — File format conversion and export strategies

---

## PART 1: CANVAS ENGINE COMPARISON

### Technology Tier Breakdown

#### Tier 1: Best Fit (Production-Ready CAD)
- **Konva.js** — Pragmatic Canvas2D choice with strong scene graph
- **Custom WebGL** — Maximum performance control, highest upfront cost

#### Tier 2: Strong Contenders (Viable with Trade-offs)
- **PixiJS** — Performance leader, zero CAD abstractions
- **tldraw SDK** — Collaboration-first, whiteboard-scale

#### Tier 3: Partial Fit (Specific Sub-problems)
- **Fabric.js** — Object model, limited scale
- **Paper.js** — Best vector math, stagnating maintenance

#### Tier 4: Reference Architecture (Learn, Don't Replicate)
- **Figma** — Gold standard, industry reference
- **AutoCAD Web** — Enterprise CAD model, WASM + WebGL
- **Excalidraw** — Collaboration patterns, whiteboard aesthetic

---

### Detailed Technology Analysis

#### 1. FABRIC.JS

**What it is**: Object-oriented Canvas2D library with interactive object model

**Strengths**:
- Well-established object model with handles, transforms, selection
- Strong TypeScript support in v6
- Excellent SVG export (`canvas.toSVG()`)
- 29K GitHub stars, 250K weekly npm downloads
- MIT license

**Critical Weaknesses**:
- **Performance ceiling**: 200-500 interactive objects before lag; 3K objects with heavy optimization
- **INSUFFICIENT for CAD** that routinely needs 10K+ objects
- No built-in snapping, measurement system, or precision tools
- No built-in undo/redo
- No native layer system for CAD workflows
- No DXF/DWG export

**Verdict**: ❌ NOT SUITABLE for professional CAD
**Best use case**: Design tools, poster makers, meme generators (sub-500 objects)

---

#### 2. KONVA.JS

**What it is**: Scene-graph-based Canvas2D with hierarchical node system (Stage > Layer > Group > Shape)

**Strengths**:
- **Best general-purpose Canvas2D for CAD**
- Multi-layer architecture — each layer is independent `<canvas>` element
- Excellent scene graph serialization (JSON-based)
- 2K-5K objects with good performance; 5K-10K with optimization
- React integration via `react-konva` (declarative canvas)
- Very active maintainer (Anton Lavrenov)
- 700K weekly npm downloads (higher than Fabric!)
- 11.5K GitHub stars
- Written entirely in TypeScript
- MIT license

**Performance**:
- ~23 FPS at 8K moving rectangles (vs Fabric's 9 FPS)
- Layer caching strategy: static content on cached layer, dynamic on active layer

**Weaknesses**:
- Canvas2D performance ceiling (~5-10K objects)
- No native SVG/DXF export
- No built-in snapping or CAD-grade precision tools
- No built-in undo/redo

**Verdict**: ✅ **RECOMMENDED as pragmatic MVP choice**
**Clear upgrade path**: Replace rendering with PixiJS when hitting Canvas2D ceiling

---

#### 3. PIXIJS

**What it is**: High-performance WebGL 2D rendering engine (game-focused origin)

**Strengths**:
- **Performance leader**: 10K-60K+ objects at 60 FPS
- Batch rendering, texture atlases, GPU-optimized pipelines
- 60 FPS at 8K objects (vs Konva's 23 FPS)
- Can handle 100K+ sprites with sprite batching
- Written in TypeScript (v8)
- 44K GitHub stars, 1M+ weekly downloads
- Backed by PlayCo (well-funded), v8 released 2024
- MIT license

**Critical Weaknesses**:
- **PURE RENDERING ENGINE** — provides zero CAD abstractions
- No selection, transformation handles, snapping, constraints
- No undo/redo
- No serialization/deserialization
- No layer system in CAD sense
- Bitmap-only export (no SVG/DXF)
- Everything must be built from scratch

**Architecture**: Best for teams with graphics programming expertise

**Verdict**: ⚠️ **Use for performance-critical rendering layer only**
**Not suitable as**: Primary framework (requires building entire CAD layer on top)

---

#### 4. PAPER.JS

**What it is**: Vector graphics scripting framework with powerful path math (inspired by Adobe Illustrator's Scriptographer)

**Strengths**:
- **BEST vector mathematics** of any Canvas library
- Superior path operations: intersection, boolean, offset, simplification
- Full layer support with visibility/opacity/blending
- Excellent SVG import/export (best in class)
- MIT license

**Critical Weaknesses**:
- Performance ceiling: 500-2K objects (16 FPS at 8K)
- Stagnating development — small core team, slow releases in 2024-2025
- Boolean operations are CPU-intensive
- No CAD tooling built-in
- No undo/redo
- 14.5K GitHub stars, 120K weekly downloads

**Verdict**: ⚠️ **Reference only for vector math algorithms**
**Not suitable as**: Primary rendering engine (performance + maintenance concerns)

---

#### 5. THREE.JS (2D Mode)

**What it is**: 3D rendering engine configured for 2D via `OrthographicCamera`

**Strengths**:
- 50K+ objects with instanced rendering (100K+ identical objects possible)
- Excellent TypeScript support
- Massive ecosystem and community
- 104K GitHub stars, 4.5M+ weekly downloads

**Critical Weaknesses**:
- **OVERKILL for pure 2D CAD** — carries entire 3D pipeline overhead
- Not designed for 2D workflows
- No undo/redo, state management
- Weak 2D vector export

**Verdict**: ⚠️ **Only for 2D/3D hybrid applications** (e.g., architectural walkthroughs from floor plans)

---

#### 6. EXCALIDRAW'S ENGINE

**What it is**: Complete open-source whiteboard application with hand-drawn aesthetic

**Architecture**:
- Immediate-mode Canvas2D rendering with Rough.js
- Flat element array as data model
- WebSocket-based collaboration with E2E encryption

**Strengths**:
- Element-centric approach serializes trivially for collaboration
- End-to-end encryption for sensitive drawings
- Infinite canvas implementation
- Simple library system

**Why NOT for CAD**:
- Hand-drawn aesthetic ≠ CAD precision
- Flat element array doesn't support hierarchies
- No measurement, snapping, or constraints
- Performance ceiling: ~15K elements
- Rough.js overhead for sketchy appearance

**Verdict**: ❌ **Learn collaboration patterns, avoid rendering approach**

---

#### 7. TLDRAW SDK

**What it is**: Embeddable infinite canvas React component backed by $5M+ funding

**Architecture**:
- Canvas2D rendering with React UI chrome
- Custom reactive store using signals (like MobX/SolidJS)
- Custom WebSocket-based "tldraw sync" engine (NOT Yjs-based)
- Extensible shape and tool systems
- Cloudflare Durable Objects for collaboration backend

**Strengths**:
- **Best collaboration-first canvas SDK available**
- EXCELLENT undo/redo (best-in-class for multiplayer)
- Built-in snapping (snap-to-grid, snap-to-shape)
- Alignment and distribution tools
- Full UI customization and extensibility
- 45K GitHub stars, 125K weekly downloads
- Actively developed, commercially backed (ClickUp, Padlet, Mobbin using in production)
- Source-available license

**Weaknesses**:
- Whiteboard-scale (~1K-5K shapes), not CAD-scale
- Basic snapping (not CAD-grade precision)
- No named/togglable layer system
- No CAD-grade measurement display
- Canvas2D performance ceiling

**Verdict**: ⚠️ **Use as collaboration architecture reference model**
**Not as**: Primary rendering engine, but study its state management and undo patterns

---

#### 8. FIGMA'S ARCHITECTURE

**The Gold Standard**: Professional design tool running entirely in browser

**Technical Stack**:
```
UI Layer (TypeScript + React)
    ↓
Document Model (C++ → WASM via Emscripten)
    ↓
Rendering Engine (C++ → WebGL, transitioning to WebGPU)
```

**Key Technical Decisions**:

1. **C++ → WebAssembly** via Emscripten
   - Near-native performance for document operations
   - Full memory layout control (32-bit floats vs JS 64-bit doubles)
   - No GC pauses
   - Same codebase runs server-side for thumbnail rendering
   - 3x faster load times vs earlier asm.js approach

2. **Custom WebGL Renderer (now WebGPU)**
   - Tile-based rendering: only dirty/visible tiles re-rendered
   - Infinite canvas without memory explosion
   - GPU-friendly draw call batching
   - Custom text layout engine
   - Custom compositor with masking, blurring, blend modes
   - WebGPU (2023-2024): compute shaders, MSAA, RenderBundles

3. **Collaboration**: CRDT-inspired with central server as source of truth
   - Simpler than pure P2P CRDTs
   - Operations are atomic and ordered
   - Cursor positions broadcast separately

**Performance**: Handles millions of objects, 60 FPS smooth rendering

**Cost to Replicate**: $5M+ investment, 6-18 months of C++/WASM development

**Verdict**: 📚 **Study architecture pattern, copy state management concepts**

---

#### 9. AUTOCAD WEB

**Technology Stack**:
- Core engine: C++ compiled to WASM via Emscripten
- Rendering: WebGL for 2D/3D
- File format: Native DWG parsing in WASM
- Same engine as desktop AutoCAD

**Key Insight**: Validates WASM + WebGL approach for professional CAD

**Verdict**: 📚 **Validate approach, DWG handling requires enterprise SDK (Open Design Alliance)**

---

#### 10. CUSTOM WEBGL/CANVAS2D

**When to Build Custom**:
- Need >10K interactive objects at 60 FPS
- Require pixel-perfect rendering control
- CAD-specific rendering (hatching, dimensions, leaders)
- Performance is competitive advantage
- Team has graphics programming expertise

**Custom WebGL Approach**:
- Raw WebGL achieves **60/120 FPS for 1M boxes**
- Full draw call batching, texture, shader control
- Tile-based rendering for infinite canvas (Figma approach)
- Instanced rendering for repetitive elements

**Hybrid Approach (RECOMMENDED)**:
- **Canvas2D for UI overlays**: selection handles, dimension text, cursors
- **WebGL for geometry**: lines, arcs, hatching
- **Separate state layer**: JSON-serializable document model
- **Abstract renderer interface**: swap Canvas2D ↔ WebGL as needed

---

### Performance Benchmarks (8K Moving Rectangles)

| Library | Chrome | Firefox | Safari | Backend |
|---------|--------|---------|--------|---------|
| **PixiJS** | **60** | **48** | 24 | WebGL |
| Scrawl-canvas | 56 | 60 | 40 | Canvas2D |
| Konva.js | 23 | 7 | 19 | Canvas2D |
| Paper.js | 16 | 6 | 16 | Canvas2D |
| Fabric.js | 9 | 4 | 9 | Canvas2D |
| Raw Canvas2D | 19 | 19 | 39 | Canvas2D |

**Critical Finding**: Pure WebGL (no library) = **60/120 FPS for 1,000,000 boxes**

---

## PART 2: FEATURE COMPARISON MATRIX

| Criteria | Fabric | Konva | PixiJS | Paper | Three.js | tldraw | Excalidraw |
|----------|--------|-------|--------|-------|----------|--------|------------|
| **Max Objects (60fps)** | ~500 | ~5K | ~60K | ~1K | ~50K* | ~5K | ~15K |
| **Precise Measurements** | None | None | None | Excellent | None | Basic | None |
| **Snapping** | None | None | None | None | None | Basic | None |
| **Layer System** | Basic | **Excellent** | Basic | Good | Exists | Minimal | None |
| **Undo/Redo** | None | None | None | None | None | **Excellent** | Basic |
| **Plugin System** | Moderate | Good | Strong | Basic | Excellent | Excellent | Basic |
| **SVG Export** | Excellent | None | None | **Excellent** | Weak | Good | Good |
| **DXF Export** | External | External | External | External | External | External | External |
| **TypeScript** | Excellent | Excellent | Excellent | Adequate | Excellent | Excellent | Good |
| **npm Downloads/wk** | 250K | 700K | 1M+ | 120K | 4.5M | 125K | 200K |
| **Community/Maintenance** | Healthy | **Very Healthy** | Thriving | Stagnating | Dominant | Commercially Backed | Strong |
| **React Integration** | Community | **react-konva** | @pixi/react | None | R3F | Native | Component |
| **CAD Grade** | No | Partial ✅ | Engine-only | Math-only | 3D-focused | Whiteboard | Whiteboard |
| **Collaboration Ready** | Manual | Manual | Manual | Manual | Manual | **Built-in** | Built-in |
| **License** | MIT | MIT | MIT | MIT | MIT | Source-avail | MIT |

---

## PART 3: COLLABORATION DEEP DIVES

### Yjs (CRDT Framework)

**Core Architecture**: Conflict-free Replicated Data Type (CRDT)

**Fundamental Data Types**:

1. **Y.Doc** — Root container
   - Unique `clientID` per editing client
   - `transact()` for atomic batched updates
   - Critical for grouping multi-shape operations

2. **Y.Map** — Key-value collaborative store
   - Last-writer-wins conflict resolution per key
   - Perfect for shape properties (concurrent edits merge cleanly)
   - Supports nesting for hierarchical structures
   - Best for storing shape data

3. **Y.Array** — Ordered collaborative sequence
   - Conflict-free insertions/deletions
   - Ideal for z-ordering and layer lists
   - Handles concurrent insertions at same index deterministically

4. **Y.Text** — Rich collaborative text
   - Quill Delta-compatible format
   - Best for annotations, labels, dimension text

**Provider System** (Transport Layer):

| Provider | Use Case | Trade-offs |
|----------|----------|-----------|
| **y-websocket** | Central server sync | Simple, scalable, persistent |
| **y-webrtc** | P2P without server | No persistence, max ~20 peers |
| **y-indexeddb** | Offline persistence | Local IndexedDB storage |
| **Hybrid** | WSProvider + IndexeddbPersistence | Best UX + offline-first |

**Awareness Protocol**:
- Ephemeral per-user state (not persisted)
- Tracks: cursor positions, selections, active tool, viewport, user presence
- Critical for presence awareness in multi-user apps

**Sub-Documents** (Lazy Loading):
- Each sub-document is full Y.Doc with unique GUID
- Load on demand, essential for projects with many pages/sheets
- Keeps memory proportional to active sheet, not entire project

**UndoManager**:
- Collaborative-aware — only undoes local user's changes
- `captureTimeout` groups changes within time window into one step
- Can track metadata (e.g., selection state before undo)

**Performance**:
- Highly optimized binary encoding (10-30x smaller than JSON)
- State vectors enable efficient differential sync
- Benchmarks: 100K text insertions = ~30KB encoded

**Recommended Yjs Structure for CAD**:
```javascript
const doc = new Y.Doc()
const shapes = doc.getMap('shapes')         // shape-id => Y.Map
const bindings = doc.getMap('bindings')     // binding-id => Y.Map
const pages = doc.getMap('pages')           // page-id => Y.Map
const layerOrder = doc.getArray('layerOrder') // Ordered shape IDs
```

---

### tldraw Store & Architecture

**NOT built on Yjs** — has its own "tldraw sync" protocol

**Core Concepts**:
- **Records**: Immutable JSON objects with `id` and `typeName`
- **Reactive**: Changes trigger automatic UI updates via signals
- **Schema validation**: Full TypeScript with compile + runtime validation
- **Record scopes**: `document` (persisted + synced), `session` (local), `presence` (synced, not persisted)

**Editor API** (Primary interface):
```typescript
editor.createShape({...})         // Create single shape
editor.createShapes([...])        // Bulk create
editor.getShape(shapeId)          // Read shape
editor.deleteShape(shapeId)       // Delete
editor.selectAll()                // Selection operations
editor.undo() / editor.redo()     // Undo/Redo
editor.sideEffects.register()     // Custom side effects
```

**Store Architecture**:
- Immutable record updates
- Complete change tracking history
- Fine-grained reactivity (signals, not observers)
- Designed for embedding and customization

**Extensibility**:
- `ShapeUtil` classes for custom shapes
- `Tool` classes for custom interaction modes
- Full UI customization (menus, toolbars, panels)
- Programmatic API via `Editor` instance

**Collaboration**:
- Custom "tldraw sync" (WebSocket-based)
- Runs on Cloudflare Durable Objects
- Built-in multiplayer undo/redo
- Per-user undo (doesn't undo others' changes)

**Performance**: Whiteboard-scale (~1K-5K shapes), Canvas2D limited

---

### Excalidraw Collaboration Model

**Architecture**:
- Flat element array as data model
- WebSocket for real-time sync
- End-to-end encryption (encrypted on client, server blind)

**Why effective for collaboration**:
- Simple serialization (plain objects)
- Trivial diffing (element array changes)
- Encrypted independently
- Library system for reusable elements

**Why NOT for CAD**:
- No hierarchies/assemblies
- No precision tooling
- Not designed for professional workflows

---

## PART 4: ARCHITECTURE RECOMMENDATIONS

### Option A: Pragmatic Start (Recommended for MVP)

```
React Application
    ├── tldraw-inspired State Layer (signals, CRDT, undo/redo)
    │   ├── Document Model (JSON-serializable element array)
    │   ├── Collaboration Engine (WebSocket + CRDT via Y.js)
    │   └── History Manager (command pattern)
    │
    ├── Konva.js Rendering Layer
    │   ├── Multi-layer canvas (grid, geometry, annotation, UI)
    │   ├── Custom shapes (dimensions, leaders, marks)
    │   └── react-konva for declarative rendering
    │
    └── CAD Tools Layer (Custom)
        ├── Snap engine (grid, endpoint, midpoint, intersection)
        ├── Measurement display
        ├── Constraint solver (parametric)
        ├── Selection manager
        └── Export pipeline (SVG native, DXF via dxf-writer)
```

**Pros**: Fast to market, React ecosystem, 5K object capacity
**Cons**: Canvas2D ceiling, renderer upgrade needed eventually
**Timeline**: 3-6 months MVP
**Clear exit strategy**: Replace Konva with PixiJS + Canvas2D overlay when hitting limits

---

### Option B: Performance-First (For ambitious teams)

```
React Application
    ├── Custom Signals-Based State Layer
    │   ├── Document Model (flat array, spatial hash indexing)
    │   ├── Collaboration (Y.js + WebSocket)
    │   └── History Manager (operational transform)
    │
    ├── Hybrid Rendering Layer
    │   ├── PixiJS for geometry (WebGL, batched, 60K+ objects)
    │   ├── Canvas2D overlay for UI (selection, dimensions)
    │   └── Viewport manager (tile-based, virtual scrolling)
    │
    └── CAD Tools Layer (Custom)
        ├── Advanced snap engine
        ├── Constraint solver
        ├── Boolean operations (clipper2-js or Paper.js algorithms)
        └── Export pipeline
```

**Pros**: 60K+ objects, WebGL performance, room to grow
**Cons**: More complex, longer dev, PixiJS has no CAD abstractions
**Timeline**: 6-12 months MVP

---

### Option C: Figma-Grade (Well-funded teams only)

```
React UI Layer
    ├── WASM Module (Rust or C++ via Emscripten)
    │   ├── Document Model (spatial indexing, constraint solver)
    │   ├── Geometry Engine (boolean, offset, fillet)
    │   └── Render Commands (tile-based list)
    │
    ├── Custom WebGL/WebGPU Renderer
    │   ├── Tile-based engine
    │   ├── Instanced rendering for symbols
    │   ├── Custom shaders (hatching, dimensions)
    │   └── Custom text engine
    │
    └── Collaboration Server (CRDT + central authority)
```

**Pros**: Best-in-class performance, handles any scale
**Cons**: $500K+ cost, 12-24 months, requires C++/Rust engineers
**Timeline**: 12-24 months to production

---

## PART 5: SPECIFIC RECOMMENDATIONS

### Stack Selection (Option A — Recommended)

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **UI Framework** | React + TypeScript | Standard, huge ecosystem |
| **Canvas Rendering** | Konva.js + react-konva | Best Canvas2D, native layers, React integration |
| **State Management** | Custom signals store (reference tldraw) | Fine-grained reactivity for canvas updates |
| **Collaboration** | Y.js (Yjs) CRDT + WebSocket | Proven offline-first, conflict resolution |
| **Undo/Redo** | Y.js UndoManager + command pattern | Built into Yjs, handles multiplayer |
| **Vector Math** | Paper.js algorithms reference + clipper2-js | Path operations, booleans |
| **SVG Export** | Custom scene graph walker | Konva lacks native SVG export |
| **DXF Export** | dxf-writer npm package | Lightweight, browser-side generation |
| **DWG Import** | Server-side (ODA SDK, LibreDWG) | No browser-side solution available |
| **Snapping/Precision** | Custom engine | No library provides CAD-grade precision |
| **Grid System** | Custom Konva cached layer | Static grid on dedicated layer |

### Key Libraries to Evaluate

- `react-konva` — React bindings for Konva.js
- `yjs` — CRDT for real-time collaboration
- `y-websocket` — WebSocket provider
- `y-indexeddb` — Offline persistence
- `clipper2-js` — Polygon boolean operations
- `dxf-writer` — DXF file generation
- `perfect-freehand` — Pressure-sensitive drawing (optional)

### Performance Upgrade Path

**When hitting Canvas2D ceiling (~5-10K objects)**:

1. Replace Konva rendering with PixiJS (WebGL geometry layer)
2. Keep Canvas2D for UI overlay (selection, dimensions, text)
3. Maintain same state management layer (renderer-agnostic)
4. Result: 10x-100x more objects at same performance

**Key principle**: Decouple state from renderer

---

## PART 6: FILE FORMAT SUPPORT

### Export/Import Matrix

| Format | Browser-Side | Server-Side | Library/Notes |
|--------|-------------|-------------|---------------|
| **SVG** | ✅ Native | - | Custom walker or canvas.toSVG() |
| **DXF** | ✅ dxf-writer, maker.js | ✅ LibreDWG, ODA SDK | Browser = lightweight, lossy |
| **DWG** | ❌ NOT POSSIBLE | ✅ ODA, LibreDWG, AutoCAD API | Proprietary format, no JS library |
| **PDF** | ✅ jsPDF, pdf-lib | ✅ wkhtmltopdf, Puppeteer | Various quality levels |
| **PNG/JPEG** | ✅ canvas.toDataURL() | ✅ Sharp, ImageMagick | Rasterization loss |

### DXF Export Best Practice

**Approach**: Walk document model (not canvas pixels)
1. Iterate each element in document
2. Convert to DXF entities (LINE, ARC, CIRCLE, TEXT, etc.)
3. Use `dxf-writer` to generate file
4. **Preserves vector precision** (unlike rasterization)

---

## PART 7: KEY GOTCHAS & LESSONS

### Canvas2D Performance
- **Fabric.js**: Hits wall at 3K objects even with optimization
- **Konva.js**: Better at 5-10K due to layer separation
- **Both**: Layer strategy critical (cache static, dynamic on active)

### No Library Handles CAD Completeness
- All libraries lack: precise snapping, constraints, dimensional annotations
- Must implement custom snap engine regardless of choice
- Measurement display always custom

### Collaboration is NOT Optional
- Real-time sync requires CRDT or OT
- Don't try to build custom (extremely hard)
- Y.js + WebSocket = proven, tested approach

### undo/redo Complexity
- tldraw has best built-in (multiplayer-aware)
- Y.js UndoManager excellent for CRDT
- Command pattern still useful for supplemental history

### Renderer Swap is Possible
- State layer is independent of renderer
- Can migrate Konva → PixiJS without rebuilding
- Keeps development velocity high

### DWG is Enterprise Only
- No browser-side DWG parsing available
- Must use ODA SDK (expensive) or LibreDWG (free but complex)
- For MVP: Focus on SVG + DXF, DWG later via server

### Tile-Based Rendering Matters
- Figma/AutoCAD use tile-based to handle infinite canvas
- Not needed for Konva (Canvas2D does dirty region tracking)
- Becomes critical if upgrading to custom WebGL

---

## FINAL VERDICT

### For Your Professional CAD-like Application:

**IMMEDIATE START** (3-6 months to MVP):
- **Rendering**: Konva.js + react-konva
- **State**: Custom signals store (study tldraw's architecture)
- **Collaboration**: Y.js + y-websocket + y-indexeddb
- **Precision**: Custom snap engine + constraint solver
- **Export**: SVG (native) + DXF (dxf-writer)

**UPGRADE PATH** (12-18 months to production):
1. Hit Canvas2D ceiling at 5-10K objects? → Replace rendering with PixiJS
2. Need DWG support? → Add server-side ODA SDK integration
3. Hit collaboration scaling limits? → Migrate to custom CRDT or evaluate enterprise solutions

### Why This Path Works

✅ **Fast MVP**: Konva + Y.js proven in production
✅ **Team alignment**: React ecosystem is familiar
✅ **Clear exit**: Renderer swap possible without state redesign
✅ **Proven patterns**: tldraw, Figma validate core approaches
✅ **Cost-effective**: $0 for libraries, focus money on domain expertise (CAD precision tools)

### Do NOT

❌ Start with custom WebGL (unless 12-24 month timeline)
❌ Use Fabric.js for professional CAD
❌ Build own collaboration system (use Y.js)
❌ Try native DWG in browser (impossible, server-only)
❌ Ignore layer strategy early (becomes expensive to retrofit)

---

## Sources & References

- canvas-engines-comparison GitHub benchmark
- Figma engineering blog (WebAssembly, WebGPU rendering)
- Konva.js documentation and performance guides
- PixiJS performance tips and community discussions
- Yjs documentation and sub-documents guide
- tldraw SDK documentation and architecture essays
- Excalidraw source code and collaboration analysis
- Paper.js feature documentation
- AutoCAD Web technical sessions

---

**Status**: Complete research synthesis ready for architecture decision
**Next step**: Detailed technical RFC for selected stack
