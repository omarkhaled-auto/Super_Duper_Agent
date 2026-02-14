# Canvas/Rendering Engine Research for CAD-Like Collaborative Drawing Application

**Date**: 2026-02-12
**Purpose**: Technology selection for a professional CAD-like collaborative drawing application
**Research Scope**: 10 technologies compared across 9 evaluation criteria

---

## Table of Contents

1. [Executive Summary & Recommendation](#executive-summary)
2. [Technology Deep Dives](#technology-deep-dives)
   - [Fabric.js](#1-fabricjs)
   - [Konva.js](#2-konvajs)
   - [PixiJS](#3-pixijs)
   - [Paper.js](#4-paperjs)
   - [Three.js (2D Mode)](#5-threejs-2d-mode)
   - [Excalidraw's Engine](#6-excalidraws-engine)
   - [tldraw](#7-tldraw)
   - [Figma's Approach](#8-figmas-approach)
   - [AutoCAD Web](#9-autocad-web)
   - [Custom WebGL/Canvas2D](#10-custom-webglcanvas2d)
3. [Head-to-Head Performance Benchmarks](#head-to-head-performance-benchmarks)
4. [Comparison Matrix](#comparison-matrix)
5. [Architecture Decision Framework](#architecture-decision-framework)
6. [Final Recommendation](#final-recommendation)

---

## Executive Summary

After extensive research, the landscape breaks into four tiers for a CAD-like collaborative drawing application:

| Tier | Technologies | Verdict |
|------|-------------|---------|
| **Tier 1: Best Fit** | **Konva.js** (pragmatic choice), **Custom WebGL** (maximum control) | Production-ready for CAD |
| **Tier 2: Strong Contenders** | **PixiJS** (performance king), **tldraw SDK** (collaboration-first) | Viable with tradeoffs |
| **Tier 3: Partial Fit** | **Fabric.js** (object model), **Paper.js** (vector math) | Good for specific sub-problems |
| **Tier 4: Reference Architecture** | **Figma** (gold standard), **AutoCAD Web** (industry reference), **Excalidraw** (collaboration model) | Learn from, don't replicate |

**Top recommendation**: Start with **Konva.js** for rapid development with a clear upgrade path to **custom WebGL rendering** as complexity grows, using **tldraw's collaboration architecture** as a reference for the real-time layer.

---

## Technology Deep Dives

### 1. Fabric.js

**What it is**: Object-oriented Canvas2D library providing an interactive object model on top of HTML5 canvas. Originally created by Juriy Zaytsev (kangax), now maintained by a community team.

**Architecture**: Flat object model -- every canvas element (rect, circle, path, text, image, SVG group) is a JavaScript object with built-in selection handles, transformation controls, and event handlers. Uses a single `<canvas>` element with full re-render on changes.

#### CAD Suitability Analysis

**Max Object Count Before Degradation**:
- **200-500 interactive objects** before noticeable lag (per community reports and Reddit benchmarks)
- **1,000-3,000 objects** with aggressive optimization (object caching, `renderOnAddRemove: false`, `skipOffscreen: true`)
- At 3,000 objects (e.g., theater seat maps), performance issues become significant according to Stack Overflow reports
- **Verdict**: INSUFFICIENT for CAD applications that routinely need 10,000+ objects

**Support for Precise Measurements/Snapping**:
- No built-in measurement or snapping system
- Must implement custom coordinate math for snap-to-grid, snap-to-object, and dimensional constraints
- Object position/size available via properties (`left`, `top`, `width`, `height`, `scaleX`, `scaleY`)
- Community snapping plugins exist but are not maintained at CAD precision levels
- **Verdict**: MANUAL IMPLEMENTATION REQUIRED

**Layer System**:
- Fabric.js v6 introduced layer management via canvas groups
- Objects have z-ordering via `bringToFront()`, `sendToBack()`, `moveTo()`
- No true multi-canvas layer system (unlike Konva's separate canvas per layer)
- Layer visibility toggling requires custom implementation
- **Verdict**: BASIC -- not comparable to CAD layer systems

**Undo/Redo Architecture**:
- No built-in undo/redo
- Canvas state can be serialized to JSON (`canvas.toJSON()`) and restored (`canvas.loadFromJSON()`)
- Full-state snapshots are memory-heavy for large documents
- Community implementations use command pattern or state diffing
- **Verdict**: MUST BUILD YOURSELF

**Extension/Plugin System**:
- Extensible via subclassing (`fabric.util.createClass`)
- Custom object types can be created by extending base classes
- v6 improved TypeScript support with proper class hierarchy
- No formal plugin architecture or marketplace
- **Verdict**: MODERATE -- class-based extension

**SVG/DXF/DWG Export**:
- **SVG**: Native export via `canvas.toSVG()` -- well-supported
- **DXF**: No built-in support; requires external library (e.g., `dxf-writer`, `makerjs`)
- **DWG**: No browser-side support; requires server-side conversion (Open Design Alliance libraries)
- **Verdict**: SVG GOOD, DXF/DWG REQUIRES ADDITIONAL LIBRARIES

**TypeScript Support**:
- v6 is written in TypeScript natively (major improvement over v5)
- Full type definitions included
- **Verdict**: EXCELLENT in v6

**Community/Maintenance (2024-2025)**:
- ~29,000 GitHub stars
- ~250,000 npm weekly downloads
- Active development on v6, but pace has slowed compared to 2020-2022
- Community is large but CAD-specific expertise is scarce
- **Verdict**: HEALTHY but not growing rapidly

**License**: MIT -- fully commercial-compatible

#### Bottom Line for CAD
Fabric.js excels at design-tool-like applications (poster makers, label editors, meme generators) where objects are interactive and countable (under 500). For CAD with thousands of precise geometric elements, it is **not the right choice** due to performance ceilings and lack of precision tooling.

---

### 2. Konva.js

**What it is**: Scene-graph-based Canvas2D framework with a hierarchical node system (Stage > Layer > Group > Shape). Created by Anton Lavrenov, actively maintained.

**Architecture**: Scene graph with multiple `<canvas>` elements (one per Layer). Each layer is an independent rendering surface, enabling selective re-rendering. Uses `requestAnimationFrame` for updates.

#### CAD Suitability Analysis

**Max Object Count Before Degradation**:
- **2,000-5,000 objects** with good performance using layer caching
- **5,000-10,000** with aggressive optimization (shape caching, batch draws, layer management)
- Benchmarks show ~23 FPS at 8,000 moving rectangles in Chrome (vs Fabric's 9 FPS)
- Performance highly depends on layer strategy -- static elements on cached layers, dynamic on active layer
- **Verdict**: MODERATE -- better than Fabric, but still Canvas2D-limited

**Support for Precise Measurements/Snapping**:
- No built-in CAD-precision tooling
- Provides coordinate transformation utilities (`getAbsolutePosition()`, `getRelativePointerPosition()`)
- Stage/layer transforms enable zoom/pan with coordinate mapping
- Custom snapping implementation required but geometry math is accessible
- **Verdict**: MANUAL IMPLEMENTATION REQUIRED (but framework supports it well)

**Layer System**:
- **Excellent native layer system** -- each Layer is a separate `<canvas>` element
- Layers render independently -- changing one layer does not re-render others
- Layer ordering via `moveToTop()`, `moveToBottom()`
- Performance tip: put static content on one layer, dynamic on another
- Layer caching (`layer.cache()`) for complex static content
- **Verdict**: STRONG -- maps well to CAD layer concepts

**Undo/Redo Architecture**:
- No built-in undo/redo, but scene graph serializes cleanly to JSON
- `stage.toJSON()` / `Konva.Node.create(json)` for full state
- Command pattern implementation is straightforward with the node-based architecture
- **Verdict**: MUST BUILD YOURSELF (but node architecture makes it cleaner)

**Extension/Plugin System**:
- Custom shapes via `Konva.Shape` with `sceneFunc` for arbitrary drawing
- `Konva.Factory` for adding custom attributes
- Plugin-like extension via prototype modification
- `react-konva` provides React integration (declarative canvas)
- **Verdict**: GOOD -- custom shapes and React integration

**SVG/DXF/DWG Export**:
- **SVG**: No direct SVG export (renders to canvas, not SVG DOM)
- **PNG/JPEG**: `stage.toDataURL()`, `stage.toBlob()`
- **DXF/DWG**: No built-in support
- Custom SVG generation would require walking the scene graph
- **Verdict**: WEAK for vector export -- must build custom exporters

**TypeScript Support**:
- Written in TypeScript since v8+
- Full type definitions, well-typed API
- `react-konva` also has TypeScript support
- **Verdict**: EXCELLENT

**Community/Maintenance (2024-2025)**:
- ~11,500 GitHub stars
- ~700,000 npm weekly downloads (higher than Fabric!)
- Very active maintainer (Anton Lavrenov), consistent releases
- `react-konva` is the standard React canvas library
- **Verdict**: VERY HEALTHY, growing

**License**: MIT -- fully commercial-compatible

#### Bottom Line for CAD
Konva.js is the **strongest general-purpose Canvas2D library for CAD-like applications**. Its scene graph, multi-layer architecture, and React integration make it the pragmatic choice for a collaborative drawing app. The main limitation is Canvas2D performance ceiling (~5-10K objects), which can be mitigated with virtualization and WebGL for hot paths.

---

### 3. PixiJS

**What it is**: High-performance WebGL 2D rendering engine. Originally created for games, now used in data visualization, interactive media, and large-scale rendering applications.

**Architecture**: WebGL-first renderer with Canvas2D fallback. Scene graph with `Container > Sprite/Graphics/Text` hierarchy. Batch rendering, texture atlases, and GPU-optimized pipelines.

#### CAD Suitability Analysis

**Max Object Count Before Degradation**:
- **10,000-60,000+ objects** at 60 FPS (per benchmarks and GitHub issues)
- Community reports: 10K graphics objects on-screen without issues, up to 20K with optimization
- Benchmark comparison repo: PixiJS hits 60 FPS in Chrome at 8K objects (vs Konva 23, Fabric 9)
- With sprite batching and texture atlases, can handle 100K+ sprites
- **Verdict**: EXCELLENT -- best performance of any library tested

**Support for Precise Measurements/Snapping**:
- No CAD tooling whatsoever -- it's a rendering engine, not a drawing framework
- You get raw pixel coordinates and must build all interaction from scratch
- No built-in selection, transformation handles, or constraint system
- `InteractionManager` handles hit testing but not CAD-grade precision
- **Verdict**: EVERYTHING MUST BE BUILT FROM SCRATCH

**Layer System**:
- Container-based hierarchy acts as layer system
- `Container.sortableChildren` for z-ordering
- `Container.mask` for clipping
- No concept of toggling layer visibility (trivial to implement via `visible` property)
- **Verdict**: PRIMITIVES AVAILABLE -- no CAD layer metaphor

**Undo/Redo Architecture**:
- No serialization/deserialization built in
- No state management -- PixiJS is purely a renderer
- Must build entire state management layer
- **Verdict**: NOT APPLICABLE -- must build state layer

**Extension/Plugin System**:
- v8 has a plugin architecture
- `@pixi/` scoped packages for modular builds
- Extensions for custom renderers, systems, and resources
- Large ecosystem of community extensions
- **Verdict**: STRONG modular architecture

**SVG/DXF/DWG Export**:
- No SVG export (WebGL renders to `<canvas>`, not SVG)
- `renderer.extract.canvas()` / `renderer.extract.pixels()` for bitmap export
- SVG rendering is one-way (import SVG as texture) -- no round-trip
- **Verdict**: BITMAP ONLY -- vector export must be built from separate data model

**TypeScript Support**:
- v8 is fully written in TypeScript
- Comprehensive type definitions
- **Verdict**: EXCELLENT

**Community/Maintenance (2024-2025)**:
- ~44,000 GitHub stars
- ~1,000,000+ npm weekly downloads
- Backed by PlayCo, very active team
- v8 released in 2024 with major architecture improvements
- **Verdict**: THRIVING

**License**: MIT -- fully commercial-compatible

#### Bottom Line for CAD
PixiJS gives you the **raw rendering horsepower** to handle anything a CAD app needs. However, it provides zero CAD abstractions -- no selection, no transformation handles, no snapping, no undo/redo, no layers in the CAD sense. You're building an engine on top of an engine. Best for teams with graphics programming expertise who need 10K+ objects.

---

### 4. Paper.js

**What it is**: Open-source vector graphics scripting framework that runs on top of HTML5 Canvas. Created by Jurg Lehni and Jonathan Puckey, inspired by Scriptographer (Adobe Illustrator scripting).

**Architecture**: Retained-mode scene graph with powerful vector math. Uses Canvas2D for rendering but maintains a full vector document model internally (Project > Layer > Item > Path/Shape/Raster).

#### CAD Suitability Analysis

**Max Object Count Before Degradation**:
- **500-2,000 objects** before noticeable performance degradation
- Benchmarks show ~16 FPS at 8K objects in Chrome (roughly comparable to Fabric)
- Boolean operations on complex paths are CPU-intensive
- **Verdict**: LIMITED -- not suitable for large CAD drawings

**Support for Precise Measurements/Snapping**:
- **BEST vector math of any library** -- full path manipulation, intersection, boolean operations
- `Path.getPointAt()`, `Path.getNearestPoint()`, `Path.getIntersections()`
- Bezier curve operations, path offsetting, path simplification
- No built-in snap system but the geometric primitives make it straightforward
- **Verdict**: EXCELLENT geometric primitives, but no built-in CAD tooling

**Layer System**:
- Full layer support (`Project.layers`, `new Layer()`)
- Layer visibility, opacity, blending modes
- Layer clipping via `Layer.clipMask`
- Closest to a traditional drawing application layer system
- **Verdict**: GOOD -- native layer model

**Undo/Redo Architecture**:
- No built-in undo/redo
- Items can be exported to JSON and restored
- **Verdict**: MUST BUILD YOURSELF

**Extension/Plugin System**:
- Minimal plugin architecture
- Extension via subclassing Item types
- PaperScript (a modified JavaScript) for simpler scripting
- **Verdict**: BASIC

**SVG/DXF/DWG Export**:
- **SVG**: Excellent native import AND export (`project.exportSVG()`, `project.importSVG()`)
- Supports gradients, clipping, and advanced SVG features in both directions
- **DXF**: No built-in support
- **DWG**: No built-in support
- **Verdict**: BEST SVG support of any library; DXF/DWG requires external tools

**TypeScript Support**:
- Type definitions available via `@types/paper`
- Core library is not written in TypeScript
- Types can lag behind releases
- **Verdict**: ADEQUATE (community-maintained types)

**Community/Maintenance (2024-2025)**:
- ~14,500 GitHub stars
- ~120,000 npm weekly downloads
- Maintenance is slow -- fewer releases in 2024-2025
- Core team is small, development has slowed significantly
- **Verdict**: STAGNATING -- usable but not actively evolving

**License**: MIT -- fully commercial-compatible

#### Bottom Line for CAD
Paper.js has the **best vector mathematics engine** of any Canvas library. Its path operations (boolean, intersection, offset) are unmatched. However, performance limitations and stagnating maintenance make it unsuitable as a primary rendering engine. Consider using its vector math algorithms as a reference or extracting specific path operations for use in a custom engine.

---

### 5. Three.js (2D Mode)

**What it is**: The dominant WebGL 3D rendering library, which can be used for 2D rendering via `OrthographicCamera` with shapes on a flat plane.

**Architecture**: Full 3D scene graph (Scene > Object3D > Mesh) with WebGL rendering. `OrthographicCamera` eliminates perspective for 2D viewing. `ShaderMaterial` enables custom 2D effects.

#### CAD Suitability Analysis

**Max Object Count Before Degradation**:
- **50,000+ objects** with instanced rendering (`InstancedMesh`)
- Individual meshes start to lag around 10,000 due to draw call overhead
- Instanced geometry can push to 100K+ identical objects at 60 FPS
- **Verdict**: EXCELLENT with proper instancing

**Support for Precise Measurements/Snapping**:
- `Raycaster` for precise hit testing in world coordinates
- Full matrix math, vector operations, and geometric primitives
- No 2D-specific CAD tooling
- **Verdict**: RAW PRIMITIVES -- all CAD logic must be custom

**Layer System**:
- `Layers` object with up to 32 layer channels
- Objects can be assigned to layers; camera can be set to see specific layers
- Not a traditional drawing layer system
- **Verdict**: EXISTS but not designed for 2D CAD

**Undo/Redo Architecture**:
- No built-in state management
- Scene graph is mutable; serialization is partial (`toJSON()` exists but lossy)
- **Verdict**: NOT APPLICABLE

**Extension/Plugin System**:
- Massive ecosystem: post-processing, controls, loaders, physics
- `@react-three/fiber` for React integration
- **Verdict**: EXCELLENT ecosystem

**SVG/DXF/DWG Export**:
- `SVGRenderer` exists but is limited and not the primary renderer
- No DXF/DWG support
- **Verdict**: WEAK for 2D vector export

**TypeScript Support**:
- Full TypeScript definitions included
- **Verdict**: EXCELLENT

**Community/Maintenance (2024-2025)**:
- ~104,000 GitHub stars
- ~4,500,000+ npm weekly downloads
- Most popular WebGL library by far
- **Verdict**: DOMINANT

**License**: MIT -- fully commercial-compatible

#### Bottom Line for CAD
Three.js is **overkill for pure 2D CAD** -- you carry the entire 3D pipeline overhead. However, if your application needs a **2D/3D hybrid** (e.g., architectural walkthroughs from floor plans, 3D previews of mechanical parts), it's the only library that handles both. The `OrthographicCamera` + flat plane approach works but feels like using a jet engine to power a bicycle.

---

### 6. Excalidraw's Engine

**What it is**: Excalidraw is an open-source whiteboard tool with a hand-drawn, sketchy aesthetic. It is NOT a library/SDK -- it's a complete application. Its engine renders directly to Canvas2D using Rough.js for the hand-drawn look.

**Architecture**: React application with a flat element array as the data model. Each element is a plain JavaScript object with position, dimensions, and type. Rendering is direct Canvas2D drawing (no scene graph).

**How It Works**:
- **Rendering**: Immediate-mode Canvas2D with Rough.js for hand-drawn shapes
- **Data model**: Simple array of element objects (`{type, x, y, width, height, ...}`)
- **Collaboration**: WebSocket-based with end-to-end encryption
- **State**: React state with element array; collaboration syncs element arrays
- **Performance**: Starts lagging at ~15,000 elements (per community reports)

#### Why Excalidraw Works for Excalidraw but NOT for CAD:
1. **Hand-drawn aesthetic** is the opposite of CAD precision
2. **Flat element array** doesn't support hierarchical assemblies
3. **No precision tooling** -- no measurements, no snapping, no constraints
4. **Performance ceiling** at ~15K elements
5. **Rough.js dependency** adds overhead for the sketchy look

#### What to LEARN from Excalidraw:
- **Simplicity of data model**: Plain objects serialize trivially for collaboration
- **End-to-end encryption**: Important for sensitive drawings
- **Element-centric approach**: Each element is self-contained, making diffing easy
- **Infinite canvas with viewport management**: Clean zoom/pan implementation
- **Library system**: Reusable element collections

**License**: MIT -- fully commercial-compatible (but using it means inheriting the sketchy aesthetic)

---

### 7. tldraw

**What it is**: An infinite canvas SDK for React, designed to be embedded in other applications. Created by Steve Ruiz, backed by $5M+ in funding. Provides a complete whiteboard experience as an embeddable component.

**Architecture**:
- **Rendering**: Canvas2D with React for UI chrome
- **State**: Custom reactive store using signals (similar to MobX/SolidJS signals)
- **Shapes**: Extensible shape system with custom `ShapeUtil` classes
- **Collaboration**: `tldraw sync` -- custom WebSocket-based sync engine built on Cloudflare Durable Objects
- **Tools**: Extensible tool system for custom interactions

#### CAD Suitability Analysis

**Max Object Count Before Degradation**:
- Designed for whiteboard-scale (~1,000-5,000 shapes)
- Not benchmarked at CAD scale (10K+ precision elements)
- Uses Canvas2D, so inherits Canvas2D performance characteristics
- **Verdict**: WHITEBOARD-SCALE, not CAD-scale

**Support for Precise Measurements/Snapping**:
- Built-in snapping system (snap-to-grid, snap-to-shape)
- Alignment and distribution tools
- No CAD-grade dimensional constraints or precision measurement display
- **Verdict**: BASIC SNAPPING -- not CAD-grade

**Layer System**:
- Z-ordering with `bringToFront`, `sendToBack`
- No named/togglable layer system in the CAD sense
- **Verdict**: MINIMAL

**Undo/Redo Architecture**:
- **EXCELLENT built-in undo/redo** via history stack
- Integrated with collaboration (undo is per-user in multiplayer)
- Command pattern with full state tracking
- **Verdict**: EXCELLENT -- best-in-class for collaborative undo

**Extension/Plugin System**:
- `ShapeUtil` for custom shapes
- `Tool` for custom interaction modes
- Full UI customization (replace menus, toolbars, panels)
- Programmatic API via `Editor` class
- **Verdict**: EXCELLENT -- designed for embedding and customization

**SVG/DXF/DWG Export**:
- SVG export built in
- No DXF/DWG support
- **Verdict**: SVG GOOD, DXF/DWG not available

**TypeScript Support**:
- Written entirely in TypeScript
- Monorepo with comprehensive types
- **Verdict**: EXCELLENT

**Community/Maintenance (2024-2025)**:
- ~45,000 GitHub stars
- ~125,000 npm weekly downloads
- Backed by commercial company (tldraw Inc)
- ClickUp, Padlet, Mobbin use it in production
- Very active development, $5M+ invested
- **Verdict**: THRIVING, commercially backed

**License**: tldraw license (source-available, free for non-commercial; commercial license required for business use)

#### Bottom Line for CAD
tldraw is the **best collaboration-first canvas SDK available**. Its undo/redo, multiplayer sync, and extensibility are best-in-class. However, its rendering performance and precision tooling are whiteboard-grade, not CAD-grade. The **ideal approach**: use tldraw's collaboration architecture and state management patterns as a reference, but build a custom rendering layer for CAD precision and performance.

---

### 8. Figma's Approach

**What it is**: Figma is a professional design tool running entirely in the browser. It represents the gold standard for web-based graphics application performance.

**Architecture** (from Figma engineering blog and reverse engineering):

```
UI Layer (TypeScript + React)
         |
Document Model (C++ -> WASM via Emscripten)
         |
Rendering Engine (C++ -> WebGL, now transitioning to WebGPU)
```

**Key Technical Decisions**:

1. **C++ compiled to WebAssembly**: The document model and rendering engine are C++, compiled to WASM via Emscripten. This provides:
   - Near-native performance for document operations
   - Full memory layout control (32-bit floats instead of JS 64-bit doubles)
   - No GC pauses (manual memory management)
   - Same C++ codebase runs server-side for rendering thumbnails
   - WASM cut load times by 3x vs their earlier asm.js approach

2. **Custom WebGL renderer (now WebGPU)**: Figma bypasses Canvas2D and HTML entirely:
   - Tile-based rendering engine: canvas divided into tiles, only dirty/visible tiles re-rendered
   - Enables infinite canvas without memory explosion
   - GPU-friendly batching of draw calls
   - Custom text layout engine (browsers are inconsistent)
   - Custom compositor with masking, blurring, blend modes
   - WebGPU migration (2023-2024) adds compute shaders, MSAA, RenderBundles

3. **Collaboration**: CRDT-inspired but with a **central server** as source of truth:
   - Simpler than pure P2P CRDTs
   - Operations are atomic and ordered
   - Cursor positions broadcast separately from document changes
   - Server resolves conflicts deterministically

**Performance Characteristics**:
- Handles documents with millions of objects
- 60 FPS smooth rendering even on complex designs
- Instant collaboration with multiple users

**What This Means for You**:
Figma's approach is the **ideal architecture** for a professional CAD tool. However, it requires:
- C++ engineering team (or Rust for WASM compilation)
- Custom WebGL/WebGPU renderer (6-18 months of development)
- Custom text engine, custom compositor
- Significant investment ($5M+ just for the rendering layer)

**You can approximate this with**: WebGL + TypeScript + WASM for performance-critical paths + a state management layer like tldraw's.

---

### 9. AutoCAD Web

**What it is**: Autodesk's browser-based version of AutoCAD, allowing editing, viewing, and collaboration on DWG files from any browser.

**Technology Stack** (from Autodesk University talks and public information):
- **Core engine**: C/C++ compiled to WebAssembly via Emscripten
- **Rendering**: WebGL for 2D/3D display
- **File format**: Native DWG parsing in WASM (same core as desktop AutoCAD)
- **Collaboration**: Cloud-based with Autodesk's infrastructure
- **UI**: Web technologies for the interface chrome

**Key Insights**:
- Autodesk took the SAME approach as Figma: C++ -> WASM + WebGL
- The DWG parsing engine is the same one used in desktop AutoCAD, compiled to WASM
- They leverage decades of CAD-specific optimizations
- File handling uses streaming parsers for large DWG files
- Web Workers used for background processing during imports

**What This Means for You**:
AutoCAD Web validates the WASM + WebGL approach for professional CAD. However, their competitive advantage is the DWG format engine (proprietary). For a new CAD application, you'd use open formats (SVG, DXF) or build your own format.

---

### 10. Custom WebGL/Canvas2D

**When to Build from Scratch**:

| Build Custom When | Use a Library When |
|---|---|
| Need >10,000 interactive objects at 60 FPS | Under 5,000 objects |
| Require pixel-perfect rendering control | Standard rendering suffices |
| CAD-specific rendering (hatching, dimensions, leaders) | Standard shapes/text |
| Performance is a competitive advantage | Time-to-market is priority |
| Team has graphics programming expertise | Team is web-focused |
| Building a platform/engine (not just an app) | Building a product |

**Custom WebGL Approach**:
- Raw WebGL outperforms ALL libraries: 60/120 FPS for 1M boxes (from canvas-engines-comparison benchmark)
- Full control over draw call batching, texture management, shader effects
- Can implement CAD-specific rendering: dimension lines, hatching patterns, center marks
- Tile-based rendering for infinite canvas (Figma approach)
- Instanced rendering for repetitive elements (fasteners, symbols)

**Custom Canvas2D Approach**:
- Simpler than WebGL, still offers decent performance
- Good for 2D-only CAD (floor plans, electrical schematics)
- `OffscreenCanvas` + Web Workers for background rendering
- Dirty region tracking to minimize redraws

**Hybrid Approach** (RECOMMENDED):
- **Canvas2D for UI overlays**: selection handles, dimension text, cursor feedback
- **WebGL for geometry rendering**: large numbers of lines, arcs, hatching
- **Separate state layer**: JSON-serializable document model independent of renderer
- **Abstract renderer interface**: swap Canvas2D for WebGL as needed

---

## Head-to-Head Performance Benchmarks

From the canvas-engines-comparison repository (8,000 moving rectangles on MacBook Pro 2019):

| Library | Chrome FPS | Firefox FPS | Safari FPS | Rendering Backend |
|---------|-----------|------------|------------|-------------------|
| **PixiJS** | **60** | **48** | 24 | WebGL |
| Scrawl-canvas | 56 | 60 | 40 | Canvas2D |
| P5.js | 15 | 4 | 44 | Canvas2D |
| Raw Canvas2D | 19 | 19 | 39 | Canvas2D |
| **Konva.js** | **23** | 7 | 19 | Canvas2D |
| CanvasKit (Skia) | 17 | 19 | 22 | WebGL/WASM |
| **Paper.js** | 16 | 6 | 16 | Canvas2D |
| **Fabric.js** | **9** | 4 | 9 | Canvas2D |
| **Three.js** | 8 | 7 | 4 | WebGL |
| SVG.js | 10 | 7 | 10 | SVG DOM |

**Key Insight**: Pure WebGL (no library) achieves **60/120 FPS for 1,000,000 boxes** on modern hardware by offloading position computation to the GPU.

**Three.js appears slow** in this benchmark because it's optimized for 3D scenes with lighting/materials, not 2D rectangle drawing. With instanced rendering, Three.js would perform much better.

---

## Comparison Matrix

| Criteria | Fabric.js | Konva.js | PixiJS | Paper.js | Three.js | tldraw | Excalidraw |
|----------|-----------|----------|--------|----------|----------|--------|------------|
| **Max Objects (60fps)** | ~500 | ~5K | ~60K | ~1K | ~50K* | ~5K | ~15K |
| **Precise Measurements** | None | None | None | Excellent | None | Basic | None |
| **Snapping** | None | None | None | None | None | Basic | None |
| **Layer System** | Basic | Excellent | Basic | Good | Exists | Minimal | None |
| **Undo/Redo** | None | None | None | None | None | Excellent | Basic |
| **Plugin System** | Moderate | Good | Strong | Basic | Excellent | Excellent | Basic |
| **SVG Export** | Excellent | None | None | Excellent | Weak | Good | Good |
| **DXF Export** | External | External | External | External | External | External | External |
| **DWG Export** | Server | Server | Server | Server | Server | Server | Server |
| **TypeScript** | Excellent | Excellent | Excellent | Adequate | Excellent | Excellent | Good |
| **npm Downloads/wk** | ~250K | ~700K | ~1M+ | ~120K | ~4.5M | ~125K | ~200K |
| **GitHub Stars** | ~29K | ~11.5K | ~44K | ~14.5K | ~104K | ~45K | ~90K+ |
| **License** | MIT | MIT | MIT | MIT | MIT | Source-avail | MIT |
| **Collaboration Ready** | Manual | Manual | Manual | Manual | Manual | Built-in | Built-in |
| **React Integration** | Community | react-konva | @pixi/react | None | R3F | Native | Component |
| **CAD Grade** | No | Partial | Engine-only | Math-only | 3D-focused | Whiteboard | Whiteboard |

*Three.js with InstancedMesh; standard meshes ~10K

---

## Architecture Decision Framework

### Option A: Pragmatic Start (Recommended for MVP/v1)

```
React Application
    |
    +-- tldraw-inspired State Layer (signals, CRDT, undo/redo)
    |       |
    |       +-- Document Model (JSON-serializable, element array)
    |       +-- Collaboration Engine (WebSocket + CRDT or OT)
    |       +-- History Manager (command pattern)
    |
    +-- Konva.js Rendering Layer
    |       |
    |       +-- Multi-layer canvas (grid layer, geometry layer, annotation layer, UI layer)
    |       +-- Custom shapes (dimension lines, leaders, section marks)
    |       +-- react-konva for declarative rendering
    |
    +-- CAD Tools Layer (custom)
            |
            +-- Snap engine (grid, endpoint, midpoint, intersection)
            +-- Measurement display
            +-- Constraint solver (parametric)
            +-- Selection manager
            +-- Export pipeline (SVG native, DXF via dxf-writer)
```

**Pros**: Fast to market, React ecosystem, good enough for 5K objects
**Cons**: Canvas2D performance ceiling, will need renderer upgrade eventually
**Timeline**: 3-6 months to functional MVP

### Option B: Performance-First (Recommended for v2 or ambitious team)

```
React Application
    |
    +-- Custom State Layer (signals-based, like tldraw's store)
    |       |
    |       +-- Document Model (flat element array, indexed by spatial hash)
    |       +-- Collaboration Engine (WebSocket + CRDT, Y.js or Automerge)
    |       +-- History Manager (operational transform)
    |
    +-- Hybrid Rendering Layer
    |       |
    |       +-- PixiJS for geometry rendering (WebGL, batched draw calls)
    |       +-- Canvas2D overlay for UI (selection handles, dimensions)
    |       +-- Viewport manager (tile-based, virtual scrolling)
    |
    +-- CAD Tools Layer (custom)
            |
            +-- Snap engine
            +-- Constraint solver
            +-- Boolean operations (from Paper.js algorithms or clipper2)
            +-- Export pipeline
```

**Pros**: 60K+ objects, WebGL performance, room to grow
**Cons**: More complex, longer development time, PixiJS has no CAD abstractions
**Timeline**: 6-12 months to functional MVP

### Option C: Figma-Grade (For well-funded teams)

```
React UI Layer
    |
    +-- WASM Module (Rust or C++ via Emscripten)
    |       |
    |       +-- Document Model (spatial indexing, constraint solver)
    |       +-- Geometry Engine (boolean ops, offset, fillet)
    |       +-- Render Commands (tile-based rendering list)
    |
    +-- Custom WebGL/WebGPU Renderer
    |       |
    |       +-- Tile-based engine
    |       +-- Instanced rendering for symbols
    |       +-- Custom shaders (hatching, dimension lines)
    |       +-- Text engine
    |
    +-- Collaboration Server
            |
            +-- CRDT with central authority
            +-- Operational transform
            +-- Presence awareness
```

**Pros**: Best-in-class performance, native-like experience, handles any scale
**Cons**: 12-24 months development, requires systems programmers, high cost ($500K+)
**Timeline**: 12-24 months to production

---

## Final Recommendation

### For YOUR application (professional CAD-like collaborative drawing):

**Start with Option A (Konva.js + custom CAD layer), plan for Option B upgrade.**

Here is the specific recommended technology stack:

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **UI Framework** | React + TypeScript | Industry standard, huge ecosystem |
| **Canvas Rendering** | Konva.js via react-konva | Best Canvas2D scene graph, native layers, good React integration |
| **State Management** | Custom signals-based store (reference tldraw's architecture) | Need fine-grained reactivity for canvas updates |
| **Collaboration** | Y.js (Yjs) CRDT library + WebSocket | Proven CRDT library, works offline, handles conflicts |
| **Undo/Redo** | Command pattern on top of Y.js | Y.js has built-in undo manager |
| **Vector Math** | Reference Paper.js algorithms, use clipper2-js for booleans | Best-in-class path operations |
| **SVG Export** | Custom scene graph walker -> SVG DOM | Konva lacks SVG export |
| **DXF Export** | dxf-writer npm package or maker.js | Lightweight DXF generation |
| **DWG Import** | Server-side via Open Design Alliance SDK or LibreDWG | No browser-side DWG parsing |
| **Precision/Snapping** | Custom engine | No library provides CAD-grade snapping |
| **Grid System** | Custom (cached Konva layer) | Static grid on dedicated layer |

**Performance Upgrade Path**:
When you hit the Canvas2D ceiling (~5-10K objects), replace Konva's rendering with:
1. **PixiJS** for the geometry layer (10x-100x more objects)
2. Keep Canvas2D overlay for UI elements (selection handles, cursors)
3. Maintain the same state management / collaboration layer (renderer-agnostic)

**Key Libraries to Evaluate**:
- `react-konva` -- React bindings for Konva.js
- `yjs` -- CRDT for real-time collaboration
- `y-websocket` -- WebSocket provider for Yjs
- `clipper2-js` -- Polygon boolean operations (union, intersection, difference)
- `dxf-writer` -- DXF file generation
- `perfect-freehand` -- Pressure-sensitive freehand drawing (if needed)

---

## DXF/DWG Export Notes

No browser-side JavaScript library can read or write DWG files natively (it's a proprietary Autodesk format). Options:

| Format | Browser-Side | Server-Side |
|--------|-------------|-------------|
| **SVG** | Native (canvas.toSVG or custom) | N/A |
| **DXF** | `dxf-writer`, `maker.js`, custom | LibreDWG, ODA SDK |
| **DWG** | NOT POSSIBLE | ODA (Teigha), LibreDWG, AutoCAD API |
| **PDF** | `jsPDF`, `pdf-lib` | wkhtmltopdf, Puppeteer |
| **PNG/JPEG** | `canvas.toDataURL()` | Sharp, ImageMagick |

For DXF export from a canvas-based app, the recommended approach is:
1. Walk your document model (not the canvas pixels)
2. Convert each element to DXF entities (LINE, ARC, CIRCLE, TEXT, etc.)
3. Use `dxf-writer` to generate the DXF file
4. This preserves vector precision (unlike rasterizing the canvas)

---

## Sources Consulted

- canvas-engines-comparison benchmark: https://github.com/slaylines/canvas-engines-comparison
- Figma rendering architecture: https://kaelan.fyi/research/figma-architecture/
- Figma blog - Building a professional design tool: https://www.figma.com/blog/building-a-professional-design-tool-on-the-web/
- Figma blog - WebAssembly: https://www.figma.com/blog/webassembly-cut-figmas-load-time-by-3x/
- Figma blog - WebGPU rendering: https://www.figma.com/blog/figma-rendering-powered-by-webgpu/
- WebGL vs Canvas for CAD tools: https://altersquare.io/webgl-vs-canvas-best-choice-for-browser-based-cad-tools/
- Technical challenges of web-based AutoCAD alternatives: https://altersquare.medium.com/the-technical-challenges-of-building-web-based-autocad-alternatives-0088e7bedd1a
- Konva.js vs Fabric.js comparison: https://medium.com/@www.blog4j.com/konva-js-vs-fabric-js-in-depth-technical-comparison-and-use-case-analysis-9c247968dd0f
- tldraw SDK: https://tldraw.dev/
- Excalidraw source: https://github.com/excalidraw/excalidraw
- PixiJS performance tips: https://pixijs.com/8.x/guides/concepts/performance-tips
- PixiJS 40K objects discussion: https://github.com/pixijs/pixi.js/issues/6350
- Fabric.js performance optimization: https://fabricjs.com/docs/fabric-object-caching/
- Konva.js performance tips: https://konvajs.org/docs/performance/All_Performance_Tips.html
- Konva.js layer management: https://konvajs.org/docs/performance/Layer_Management.html
- Paper.js features: http://paperjs.org/features/
- npm trends comparison: https://npmtrends.com/fabric-vs-fabric.js-vs-konva-vs-paper-vs-pixi-vs-react-fabricjs
- Autodesk WebAssembly: https://www.autodesk.com/autodesk-university/class/Supercharge-Your-Browser-Based-Autodesk-Platform-Services-Applications-with-WebAssembly-2025
- tldraw collaboration: https://tldraw.dev/features/composable-primitives/multiplayer-collaboration
- DXF export approach: https://dev.to/franksandqvist/making-a-canvas-based-svg-designer-app-that-exports-dxf-files-for-manufacturing-4gjo
