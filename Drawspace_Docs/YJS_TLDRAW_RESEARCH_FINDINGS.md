# YJS CRDT + TLDRAW CANVAS ENGINE RESEARCH FINDINGS
## Complete Deep Dive Summary for Collaborative CAD Development

**Date:** 2026-02-12
**Research Scope:** Yjs CRDT Library, tldraw Canvas Framework, Integration Patterns
**Purpose:** Technical foundation for professional collaborative CAD applications

---

## EXECUTIVE SUMMARY

Research confirms **Yjs + tldraw** is the optimal technology stack for building professional collaborative CAD applications. Expected MVP delivery: **6-12 months** with 3-5 engineers.

**Key Findings:**
- Yjs provides robust CRDT with multiple transport providers
- tldraw offers extensible canvas framework with $5M+ investment
- Integration requires bridge layer between tldraw store and Yjs Y.Doc
- Canvas2D ceiling: 5-10K objects; upgrade to PixiJS (WebGL) for CAD scale
- Offline support critical for CAD workflows (y-indexeddb)

---

## SECTION 1: YJS CRDT LIBRARY FINDINGS

### 1.1 Core Data Types Architecture

#### Y.Doc (Root Container)
- **Purpose:** Holds all shared data types in collaborative session
- **Key Properties:**
  - `clientID` (auto-assigned): Unique identifier per client
  - `guid` (user-provided): Global unique ID for sub-documents
  - `gc` (garbage collection flag): Controls deleted content retention
- **Critical Feature:** `transact()` method batches operations into atomic updates

**Why it matters for CAD:** Multi-property updates (wall position + thickness + material) execute as single transaction, preventing partial states visible to remote users.

#### Y.Map (Key-Value Store — PRIMARY for Shape Data)
- **Conflict Resolution:** Last-writer-wins per KEY (not object)
- **Nesting:** Supports nested shared types for hierarchical structures
- **Ideal for CAD:** Concurrent edits to different shape properties merge cleanly
- **Change Events:** Track action types (`add`, `update`, `delete`)

**Example CAD usage:**
```javascript
const shapes = doc.getMap('shapes')
const wall = new Y.Map([
  ['id', 'wall-001'],
  ['type', 'rectangle'],
  ['x', 100],
  ['y', 200],
  ['props', new Y.Map([['width', 300], ['thickness', 150]])]
])
shapes.set('wall-001', wall)
```

#### Y.Array (Ordered Sequences)
- **Use Case:** Z-ordering, layer lists, ordered collections
- **Conflict Resolution:** Concurrent insertions at same index resolved via position identifiers
- **Change Format:** Delta notation (`{ retain, insert, delete }`)

#### Y.Text (Rich Text)
- **Format:** Quill Delta-compatible
- **Use Case:** Dimension labels, annotations, notes

### 1.2 Provider System (Transport Layer)

#### y-websocket (Production Standard)
- Central WebSocket server relaying updates
- **Server Options:**
  - Simple Node.js with optional LevelDB
  - y-redis: Scalable with Redis + configurable storage
  - Hocuspocus: Feature-rich with auth, webhooks, persistence

#### y-webrtc (Peer-to-Peer)
- Direct peer connections without central server
- **Practical Limit:** ~20 peers
- **Trade-off:** No persistence, low latency for small groups

#### y-indexeddb (Offline Persistence)
- Browser IndexedDB storage for offline workflows
- **Critical for CAD:** Enables graceful offline editing + auto-merge on reconnection
- **Combination:** Can run simultaneously with y-websocket

### 1.3 Awareness Protocol (Ephemeral User State)

Manages transient data NOT persisted:
```javascript
awareness.setLocalState({
  user: { name: 'Alice', color: '#ff0000' },
  cursor: { x: 150, y: 300 },
  selectedShapes: ['shape-001'],
  viewport: { x: 0, y: 0, zoom: 1.5 }
})
```

**CAD Presence to Track:**
- Cursor position (page coordinates)
- Selected shapes (array of IDs)
- Active tool (select, draw, wall-tool, etc.)
- Viewport bounds (viewing area)
- User identity (name, color, avatar)
- Editing state (which shape is being edited)

### 1.4 Sub-Documents (Lazy Loading)

**Critical for Large Projects:**
```javascript
const rootDoc = new Y.Doc()
const pages = rootDoc.getMap('pages')
const page1Doc = new Y.Doc({ guid: 'page-1' })

rootDoc.on('subdocs', ({ loaded }) => {
  loaded.forEach(subdoc => {
    new WebsocketProvider('wss://server.com', subdoc.guid, subdoc)
  })
})
```

**CAD Relevance:** Load only active sheet; lazy-load others on demand. Essential for projects with 100+ drawing sheets. Each sheet gets independent sync channel.

### 1.5 UndoManager (Collaborative-Aware)

**Key Behavior:** Only undoes local user's changes, not remote changes.

```javascript
const undoManager = new Y.UndoManager([shapes, layerOrder], {
  trackedOrigins: new Set([null]),
  captureTimeout: 500  // Group changes within 500ms
})

undoManager.undo()  // Only undoes local changes
undoManager.on('stack-item-added', event => {
  event.stackItem.meta.set('selection', editor.getSelectedIds())
})
```

### 1.6 Performance Characteristics

**Document Size:**
- 100,000 text insertions → ~30KB encoded
- 10-30x smaller than JSON representation
- Binary encoding highly optimized

**Sync Efficiency:**
- Full sync: `Y.encodeStateAsUpdate(doc)` — complete document
- Differential sync: `Y.encodeStateAsUpdate(doc, stateVector)` — only changes
- Server works with binary directly (no Y.Doc needed)

**Critical Considerations:**
- **Garbage collection:** `gc: true` reduces size but prevents undo of GC ops
- **Transaction batching:** Always use `doc.transact()` for multi-property updates
- **Sub-documents:** Keep memory proportional to active page
- **Update merging:** `Y.mergeUpdates()` compacts multiple messages

### 1.7 Data Structure for CAD

**Recommended Yjs Structure:**
```javascript
const doc = new Y.Doc()

const shapes = doc.getMap('shapes')           // shape-id => Y.Map
const bindings = doc.getMap('bindings')       // binding-id => Y.Map
const pages = doc.getMap('pages')             // page-id => Y.Map
const assets = doc.getMap('assets')           // asset-id => Y.Map
const layerOrder = doc.getArray('layerOrder') // Ordered shape IDs
```

### 1.8 Persistence Strategies

| Strategy | Storage | Pros | Cons |
|----------|---------|------|------|
| **Update Log** | Append-only binary | Simple, full history | Load time grows |
| **Snapshot + Updates** | Snapshots + deltas | Fast load | Overhead |
| **State-Vector Based** | Merged state + diffs | Efficient | Complex |
| **Database per Record** | Rows + Yjs binary | Queryable | Reconciliation |

---

## SECTION 2: TLDRAW CANVAS ENGINE FINDINGS

### 2.1 Store Architecture

**Key Distinction:** tldraw has its own sync protocol (NOT Yjs-based).

**Core Concepts:**
- **Records:** Immutable JSON with `id` and `typeName`
- **Reactive:** Changes trigger UI updates via signals
- **Change Tracking:** Complete modification history
- **Schema Validation:** Full TypeScript support

**Record Scopes:**

| Scope | Persisted | Synced | Examples |
|-------|-----------|--------|----------|
| `document` | Yes | Yes | Shapes, pages, bindings |
| `session` | Optional | No | Camera, current page |
| `presence` | No | Yes | Cursors, selections |

### 2.2 Shape Record Structure

```typescript
{
  id: 'shape:abc123',           // Branded string
  typeName: 'shape',
  type: 'geo',
  x: 100,
  y: 200,
  rotation: 0,
  parentId: 'page:page1',
  index: 'a1',                  // Fractional index (z-ordering)
  isLocked: false,
  opacity: 1,
  props: {
    geo: 'rectangle',
    w: 300,
    h: 150,
    color: 'blue',
    fill: 'solid'
  },
  meta: {}
}
```

### 2.3 Editor API (High-Level Interface)

**Shape Operations:**
```typescript
editor.createShape({ type: 'geo', x: 100, y: 100 })
editor.updateShape({ id: shape.id, x: 200 })
editor.deleteShape(shapeId)
editor.getCurrentPageShapes()
```

**Camera/Viewport:**
```typescript
const camera = editor.getCamera()  // { x, y, z } (z = zoom)
editor.zoomToFit()
editor.zoomToSelection()

// Coordinate conversion (CRITICAL for mouse handling)
const pagePoint = editor.screenToPage({ x: mouseX, y: mouseY })
const screenPoint = editor.pageToScreen({ x: shapeX, y: shapeY })
```

**History:**
```typescript
editor.undo()
editor.redo()
editor.markHistoryStoppingPoint()
```

### 2.4 Custom Shapes System (Critical for CAD)

Three requirements per custom shape:

#### 1. Type Definition
```typescript
declare module 'tldraw' {
  export interface TLGlobalShapePropsMap {
    'cad-wall': {
      w: number
      h: number
      thickness: number
      material: string
    }
  }
}

type CadWallShape = TLShape<'cad-wall'>
```

#### 2. ShapeUtil Class
```typescript
class CadWallShapeUtil extends ShapeUtil<CadWallShape> {
  static override type = 'cad-wall' as const

  static override props: RecordProps<CadWallShape> = {
    w: T.number,
    h: T.number,
    thickness: T.number,
    material: T.string,
  }

  getDefaultProps(): CadWallShape['props'] {
    return { w: 200, h: 20, thickness: 150, material: 'concrete' }
  }

  // Hit testing geometry
  getGeometry(shape: CadWallShape): Geometry2d {
    return new Rectangle2d({
      width: shape.props.w,
      height: shape.props.h,
      isFilled: true,
    })
  }

  // Rendering
  component(shape: CadWallShape) {
    return (
      <HTMLContainer>
        <div style={{
          width: shape.props.w,
          height: shape.props.h,
          background: shape.props.material === 'concrete' ? '#888' : '#a52a2a',
          border: '2px solid #333',
        }}>
          <span>{shape.props.thickness}mm</span>
        </div>
      </HTMLContainer>
    )
  }

  // Selection indicator
  indicator(shape: CadWallShape) {
    return <rect width={shape.props.w} height={shape.props.h} />
  }

  // Lifecycle hooks
  override onBeforeCreate(next: CadWallShape) {
    const snapped = Math.round(next.props.thickness / 50) * 50
    return { ...next, props: { ...next.props, thickness: snapped } }
  }
}
```

#### 3. Registration
```typescript
<Tldraw shapeUtils={[CadWallShapeUtil]} />
```

### 2.5 Geometry System (Hit Testing)

**Available Classes:**
- `Rectangle2d` — axis-aligned rectangles
- `Circle2d` — true circles
- `Polygon2d` — arbitrary polygons
- `Polyline2d` — open paths
- `Arc2d` — circular arcs
- `Group2d` — composite geometry

**Key Operations:**
- `hitTestPoint(point, margin)` — point selection with tolerance
- `intersectLineSegment()` — line intersection
- `nearestPoint()` — closest point on geometry
- `bounds` — axis-aligned bounding box

### 2.6 ShapeUtil Lifecycle Hooks

| Hook | Phase | Modifiable? | Use Case |
|------|-------|-----------|----------|
| `onBeforeCreate` | Before store write | Yes | Validation, snapping, defaults |
| `onBeforeUpdate` | Before store write | Yes | Constrain values, enforce rules |
| `onResize` | During resize | Yes | Custom resize behavior |
| `onRotate` | During rotation | Yes | Snap rotation angles |
| `onTranslate` | During move | Yes | Grid snapping, constraints |

### 2.7 Tool System (Custom Interaction)

```typescript
class WallTool extends StateNode {
  static override id = 'wall-tool'

  override onPointerDown: TLEventHandlers['onPointerDown'] = (info) => {
    const point = this.editor.inputs.currentPagePoint
    this.editor.createShape({
      type: 'cad-wall',
      x: point.x,
      y: point.y,
    })
  }

  override onPointerMove: TLEventHandlers['onPointerMove'] = (info) => {
    // Preview wall placement
  }
}

<Tldraw tools={[WallTool]} />
```

### 2.8 Side Effects System (Constraint Enforcement)

Store-level lifecycle hooks for cross-shape logic:

```typescript
// Before handlers — can modify/block changes
editor.sideEffects.registerBeforeChangeHandler('shape', (prev, next, source) => {
  if (next.x < 0) return prev  // Block invalid change
  return next
})

// After handlers — react to completed changes
editor.sideEffects.registerAfterChangeHandler('shape', (prev, next, source) => {
  // Update related shapes, recalculate constraints
  if (source === 'user') {
    // Recalculate dependent dimensions
  }
})

// Batch handler — runs once after all changes
editor.sideEffects.registerOperationCompleteHandler((source) => {
  if (source === 'user') scheduleAutosave()
})
```

**CAD Relevance:** Backbone for constraint systems, auto-dimensioning, cross-shape validation.

### 2.9 Signals / Reactivity

Fine-grained reactive updates:

```typescript
const ShapeInspector = track(() => {
  const editor = useEditor()
  const selected = editor.getSelectedShapes()

  return (
    <div>
      <p>Selected: {selected.length} shapes</p>
      {selected.map(s => (
        <div key={s.id}>{s.type}</div>
      ))}
    </div>
  )
})

// Computed signals
const totalArea = computed('totalArea', () => {
  return editor.getCurrentPageShapes()
    .reduce((sum, s) => sum + s.props.w * s.props.h, 0)
})
```

### 2.10 Schema Migrations

Versioned shape schemas with up/down migrations:

```typescript
static override migrations = defineMigrations({
  currentVersion: 2,
  migrators: {
    1: {
      up: (shape) => ({ ...shape, props: { ...shape.props, material: 'concrete' } }),
      down: (shape) => {
        const { material, ...rest } = shape.props
        return { ...shape, props: rest }
      },
    },
  },
})
```

### 2.11 Collaboration via tldraw Sync

**Client:**
```typescript
const store = useSync({
  uri: `wss://my-server.com/connect/${roomId}`,
  shapeUtils: customShapeUtils,
})

return <Tldraw store={store} />
```

**Server:**
```typescript
const schema = createTLSchema({
  shapes: { ...defaultShapeSchemas, 'cad-wall': { props } },
})

const storage = new SQLiteSyncStorage({ sql })
const room = new TLSocketRoom({ schema, storage })

wss.on('connection', (ws) => {
  room.handleSocketConnect({ sessionId: generateId(), socket: ws })
})
```

**Server Storage Options:**
- `InMemorySyncStorage` — volatile
- `SQLiteSyncStorage` — production (auto-manages tables)
- `Cloudflare Durable Objects` — tldraw's production architecture

---

## SECTION 3: TLDRAW + YJS INTEGRATION

### 3.1 Two Integration Approaches

#### Approach A: Use tldraw sync (Recommended Start)
- tldraw's built-in protocol (NOT Yjs)
- Official support from tldraw team
- Schema migrations included
- Battle-tested on tldraw.com
- **Pros:** Simpler, proven, migrations
- **Cons:** Tied to tldraw protocol, less flexibility

#### Approach B: Bridge tldraw Store to Yjs (Custom)
- Map tldraw records to/from Yjs Y.Map
- Enables shared CRDT model with other components
- Allows y-indexeddb for offline-first
- More complex but flexible

### 3.2 Bridge Implementation

```typescript
function createYjsBridge(doc: Y.Doc, store: ReturnType<typeof createTLStore>) {
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
      const toAdd: TLRecord[] = []
      const toRemove: string[] = []

      event.changes.keys.forEach((change, key) => {
        if (change.action === 'add' || change.action === 'update') {
          const record = yStore.get(key) as TLRecord
          toAdd.push(record)
        } else if (change.action === 'delete') {
          toRemove.push(key)
        }
      })

      if (toAdd.length) store.put(toAdd)
      if (toRemove.length) store.remove(toRemove)
    })
  })
}
```

**Critical Considerations:**
- Use `store.mergeRemoteChanges()` for Yjs changes (prevents echo loops)
- Use `store.listen({ source: 'user' })` to capture only local changes
- Map Yjs awareness to tldraw presence records
- Validate Yjs data conforms to tldraw schema

### 3.3 Why Choose Yjs Over tldraw sync

| Reason | Details |
|--------|---------|
| **Shared data model** | Other components use Yjs (text, tree view, etc.) |
| **Offline-first** | y-indexeddb for robust browser persistence |
| **P2P option** | y-webrtc enables serverless collaboration |
| **Ecosystem** | Providers for Redis, PostgreSQL, MongoDB, etc. |
| **Sub-documents** | Lazy-load drawing pages independently |

---

## SECTION 4: RECOMMENDED FULL STACK

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **UI Framework** | React + TypeScript | Industry standard, huge ecosystem |
| **Canvas Rendering** | tldraw SDK | Best Canvas2D + extensibility |
| **Rendering Upgrade** | PixiJS (WebGL) | When scaling beyond 5K objects |
| **State Management** | tldraw store + Yjs | Signals reactivity + CRDT |
| **Collaboration** | Yjs + y-websocket | Proven CRDT, offline-capable |
| **Undo/Redo** | Y.UndoManager | Collaborative-aware |
| **Vector Math** | clipper2-js or Paper.js | Path operations, booleans |
| **SVG Export** | Custom scene graph walker | tldraw lacks native |
| **DXF Export** | dxf-writer npm | Lightweight generation |
| **Snapping** | Custom engine | No library provides CAD-grade |
| **Server** | Node.js + y-websocket | Or Cloudflare Workers + DO |
| **Persistence** | PostgreSQL + update log | Scalable, queryable, historical |
| **Offline** | y-indexeddb | Local-first persistence |

---

## SECTION 5: CUSTOM CAD SHAPE TYPES

**Recommended implementations:**

| Type | Props | Geometry | Notes |
|------|-------|----------|-------|
| `cad-wall` | length, thickness, material, fireRating | Rectangle2d | Snaps to grid, connects at endpoints |
| `cad-door` | width, swingAngle, direction | Arc2d + Rectangle2d | Bound to wall |
| `cad-window` | width, height, sillHeight | Rectangle2d | Bound to wall |
| `cad-dimension` | startRef, endRef, offset, unit | Polyline2d | Auto-calculates measurements |
| `cad-room` | name, area (computed) | Polygon2d | Closed polygon from walls |
| `cad-column` | diameter, shape | Circle2d/Rectangle2d | Structural element |
| `cad-beam` | width, depth, span | Rectangle2d | Structural element |
| `cad-annotation` | text, type | Rectangle2d | Leader line via binding |

---

## SECTION 6: IMPLEMENTATION ROADMAP

### Phase 1: Foundation (2-3 weeks)
- Set up tldraw with React
- Implement 3-4 basic CAD shapes (wall, door, window, dimension)
- Add custom tools for each shape type
- Set up tldraw sync for basic collaboration

### Phase 2: Constraints & Intelligence (2-3 weeks)
- Wall endpoint snapping (side effects)
- Door/window binding to walls
- Auto-dimensioning
- Grid and guideline snapping
- Undo/redo integration

### Phase 3: Advanced Collaboration (1-2 weeks)
- User presence (cursors, selections, viewports)
- Conflict resolution testing
- Multi-page/sheet support
- Offline support (if using Yjs bridge)

### Phase 4: Production Features (2-3 weeks)
- Export to DXF/SVG/PDF
- Layer management
- Symbol library (reusable components)
- Measurement and area calculation
- Print layout

**Total Timeline: 6-12 months for experienced team (3-5 engineers)**

---

## SECTION 7: ARCHITECTURE PATTERNS & BEST PRACTICES

### Hit Detection / Selection
1. Bounding box check (fast, imprecise)
2. Canvas `isPointInPath()` / `isPointInStroke()`
3. Tolerance padding (increase lineWidth temporarily)
4. Spatial indexing (R-tree for 10K+ objects)
5. GPU color-picking (render to offscreen with unique colors)

**Critical:** Transform mouse (screen space) → canvas (world space) using zoom/pan matrix.

### Zoom and Pan Implementation
```javascript
let scale = 1
let offsetX = 0
let offsetY = 0

ctx.setTransform(scale, 0, 0, scale, offsetX, offsetY)

function zoomAtPoint(mouseX, mouseY, newScale) {
  const worldX = (mouseX - offsetX) / scale
  const worldY = (mouseY - offsetY) / scale
  scale = newScale
  offsetX = mouseX - worldX * scale
  offsetY = mouseY - worldY * scale
}
```

### Collaborative Undo/Redo Patterns
- **Snapshot-based:** Store entire state (memory-heavy)
- **Command pattern:** Store actions with execute/undo (most common)
- **Differential:** Store deltas (most efficient)

**Yjs approach (recommended):** UndoManager only undoes local changes; other users' changes persist.

---

## SECTION 8: PERFORMANCE TARGETS

Based on industry leaders (Figma, Onshape, tldraw):

| Metric | Target |
|--------|--------|
| Initial load | <3 seconds |
| Frame rate | 60 FPS for pan/zoom/draw |
| Object count | 10,000+ smoothly |
| Collaboration latency | <200ms for cursor updates |
| Document size | 100MB+ files |
| Concurrent users | 10-20 per document |

**Canvas2D Ceiling (tldraw, Konva):**
- Typical: 5,000-10,000 objects at 60 FPS
- Can push to 15K-20K with optimization

**WebGL Ceiling (PixiJS):**
- Typical: 60,000+ objects at 60 FPS
- Max with GPU instancing: 1,000,000+ objects

---

## SECTION 9: CRITICAL GOTCHAS & LESSONS

### What NOT to Do
1. Don't start with SVG — breaks at >1K objects
2. Don't build custom CRDT — use Yjs (CRDTs are algorithmically complex)
3. Don't use WebGL without graphics expertise — steep learning curve
4. Don't try to replicate Figma — they have $20M+ and 5+ years
5. Don't ignore collaboration from day 1 — hard to retrofit
6. Don't serialize entire canvas state on every change — memory explosion
7. Don't use THREE.js for pure 2D — overkill
8. Don't build custom transport layer — use proven providers

### Why Most CAD Apps Fail
1. Chose wrong rendering technology
2. Built collaboration incorrectly (no CRDT)
3. No offline support
4. Performance ceiling not identified early
5. Underestimated undo/redo complexity
6. Constraint solving hard-coded (not generalizable)
7. No schema versioning for data model evolution

### Lessons from Industry Leaders

**Figma:**
- Invest in rendering infrastructure early (WASM + custom WebGL)
- Central server as authority simplifies CRDT
- Same C++ codebase in browser (WASM) + server (native)

**Onshape:**
- Geometry computation belongs on server
- Incremental history fundamental to storage
- PDM part of core architecture

**tldraw:**
- Extensible shapes enable CAD features
- Side effects system powerful for constraints
- Signals-based reactivity scales better than Redux

**Excalidraw:**
- Simplicity works for whiteboards
- Hand-drawn aesthetic NOT for CAD
- Limited custom shape support (use tldraw instead)

---

## SECTION 10: FINAL ASSESSMENT & RECOMMENDATIONS

### Recommended Stack for Professional CAD

```
Frontend:     React + TypeScript + tldraw SDK
Sync:         Yjs (Y.Doc) + y-websocket bridge to tldraw
Rendering:    Canvas2D via tldraw (upgrade to PixiJS at 5K+)
State:        tldraw store + Yjs CRDT + custom side effects
Server:       Node.js + y-websocket + PostgreSQL
Offline:      y-indexeddb
Deployment:   Vercel (frontend) + Railway/Fly.io (backend)
```

### Timeline & Team
- **MVP (basic shapes, save):** 2-3 months
- **Collaboration & multiplayer:** 1-2 months
- **Production-grade (constraints, export):** 3-4 months
- **Total to market-ready:** 6-12 months
- **Team size:** 3-5 engineers for MVP, +2 for production features

### Cost Estimate
- **Engineering:** $300K-500K (6-12 months, 3-5 engineers)
- **Infrastructure:** $2K-5K/month
- **Total first year:** ~$400K-600K

### Risk Areas
- Constraint solver complexity (typically underestimated)
- Performance wall at 5-10K objects (Canvas2D ceiling)
- Offline synchronization conflicts
- DWG/DXF interoperability
- Undo/redo complexity in multiplayer (solvable with Y.UndoManager)

---

## CONCLUSION

**Yjs + tldraw is the proven foundation** for professional collaborative CAD applications. The combination provides:

✓ Robust CRDT with proven offline support
✓ Extensible canvas framework with $5M+ investment
✓ Built-in undo/redo that works in multiplayer
✓ Schema migrations for data model evolution
✓ Signals-based reactivity (scales better than Redux)
✓ Full TypeScript support
✓ Production-grade at multiple scales (tldraw.com, Figma uses Yjs patterns)

**Timeline:** Experienced team can deliver market-ready CAD app in 6-12 months.

---

**End of Research Summary**

This document synthesizes comprehensive findings from three technical reports analyzing Yjs CRDT library and tldraw canvas engine for collaborative CAD development.
