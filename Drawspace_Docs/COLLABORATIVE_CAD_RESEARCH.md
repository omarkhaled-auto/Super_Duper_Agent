# Collaborative CAD Application — Technology Research Report

**Date:** 2026-02-12
**Scope:** Yjs (CRDT), tldraw (Canvas Engine), Excalidraw (Alternative), Integration Architecture
**Purpose:** Technical evaluation for a collaborative CAD application

---

## Table of Contents

1. [Part 1: Yjs Deep Dive](#part-1-yjs-deep-dive)
2. [Part 2: tldraw Deep Dive](#part-2-tldraw-deep-dive)
3. [Part 3: tldraw + Yjs Integration](#part-3-tldraw--yjs-integration)
4. [Part 4: Excalidraw as Alternative](#part-4-excalidraw-as-alternative)
5. [Part 5: Architecture Recommendations](#part-5-architecture-recommendations)

---

## Part 1: Yjs Deep Dive

### 1.1 Core Data Types

Yjs provides four fundamental shared data types that form the building blocks of any collaborative document.

#### Y.Doc — The Root Container

`Y.Doc` is the root-level document that holds all shared data types. Every collaborative session is organized around a single Y.Doc instance. Key properties:

- **clientID**: Unique identifier for each editing client (auto-assigned)
- **gc**: Garbage collection flag (default `true`) — when enabled, deleted content is permanently removed rather than retained for undo history
- **guid**: Globally unique identifier, critical for sub-documents and persistence

```javascript
import * as Y from 'yjs'

const doc = new Y.Doc()
const yarray = doc.getArray('my-array')   // Named top-level type
const ymap = doc.getMap('my-map')         // Named top-level type
const ytext = doc.getText('my-text')      // Named top-level type
```

Top-level types are accessed by name via `doc.getArray()`, `doc.getMap()`, `doc.getText()`. The name serves as the key — calling `doc.getMap('shapes')` twice returns the same shared instance.

**Critical for CAD:** Y.Doc supports a `transact()` method for batching multiple operations into a single atomic update. This is essential for CAD operations like "move a group of shapes" where you want all position changes to apply as one unit.

```javascript
doc.transact(() => {
  ymap.set('x', 100)
  ymap.set('y', 200)
  ymap.set('width', 50)
}) // Single update emitted, single undo step
```

#### Y.Map — Key-Value Store (Primary for Shape Data)

Y.Map is the most important type for CAD shape storage. It provides a collaborative key-value store with conflict resolution based on last-writer-wins per key.

```javascript
const ymap = doc.getMap('shapes')

ymap.set('shape-001', new Y.Map())  // Nested maps for shape properties
ymap.set('prop-name', 'value')
ymap.get('prop-name')               // => 'value'
ymap.has('count')                    // => true
ymap.delete('key')
ymap.toJSON()                       // => plain JavaScript object

// Observe changes
ymap.observe(event => {
  event.changes.keys.forEach((change, key) => {
    // change.action: 'add' | 'update' | 'delete'
    // change.oldValue: previous value (for update/delete)
  })
})
```

**Conflict resolution:** When two users simultaneously set different values for the same key, Yjs deterministically picks one winner (based on clientID ordering). When they set different keys, both changes are preserved. This is ideal for shape properties — concurrent edits to different properties of the same shape merge cleanly.

**Nesting:** Y.Map supports nesting shared types. You can put a Y.Map inside a Y.Map, enabling hierarchical data structures:

```javascript
const shapeData = new Y.Map()
shapeData.set('x', 100)
shapeData.set('y', 200)
shapeData.set('props', new Y.Map([['color', 'blue'], ['width', 50]]))
rootMap.set('shape-001', shapeData)
```

#### Y.Array — Ordered Sequences (Z-ordering, Layer Lists)

Y.Array provides a collaborative ordered list with conflict-free insertions, deletions, and index-based operations. Uses delta format for change representation.

```javascript
const yarray = doc.getArray('layers')

yarray.insert(0, [1, 2, 3])
yarray.delete(1, 1)           // delete at index 1
yarray.push(['end'])
yarray.unshift(['start'])
yarray.get(0)                 // => 'start'
yarray.slice(1, -1)

// Observe with delta format
yarray.observe(event => {
  event.changes.delta  // e.g., [{ retain: 2 }, { insert: ['a'] }, { delete: 1 }]
})
```

**CAD relevance:** Y.Array is ideal for z-ordering/layer lists where the order of elements matters. Concurrent insertions at the same index are handled by Yjs's internal ordering algorithm (each element gets a unique position identifier).

#### Y.Text — Rich Text (Annotations, Labels, Notes)

Y.Text supports collaborative rich text with inline formatting attributes, using a Quill Delta-compatible format.

```javascript
const ytext = doc.getText('annotation')
ytext.insert(0, 'Dimension: 45mm')
ytext.format(11, 4, { bold: true })  // Bold "45mm"
ytext.toDelta()
// => [{ insert: 'Dimension: ' }, { insert: '45mm', attributes: { bold: true } }]
```

**CAD relevance:** Useful for dimension labels, annotations, notes, and any text content on the canvas.

### 1.2 Provider System

Providers handle the transport layer — how updates are distributed between clients. Yjs's architecture completely decouples the data model from the transport.

#### y-websocket (Primary for Production)

The standard WebSocket-based provider. Connects to a central server that relays updates between clients.

```javascript
import { WebsocketProvider } from 'y-websocket'

const provider = new WebsocketProvider(
  'wss://your-server.com',
  'room-name',
  doc
)
provider.awareness  // Access the awareness instance
provider.on('status', ({ status }) => {
  // 'connecting' | 'connected' | 'disconnected'
})
```

**Server options:**
- **y-websocket server**: Simple Node.js WebSocket server, optional LevelDB persistence
- **y-redis**: Scalable backend using Redis for update distribution + configurable persistent storage (S3, PostgreSQL)
- **Hocuspocus**: Feature-rich server by Tiptap with authentication, webhooks, and persistence hooks

#### y-webrtc (Peer-to-Peer)

Direct peer-to-peer synchronization without a central server. Uses WebRTC data channels with optional signaling server.

```javascript
import { WebrtcProvider } from 'y-webrtc'

const provider = new WebrtcProvider('room-name', doc, {
  signaling: ['wss://signaling.yjs.dev'],
  password: 'optional-encryption-key',
  maxConns: 20
})
```

**Trade-offs:** No central server needed, but requires signaling. Not suitable for persistence. Works well for small groups (< 20 peers).

#### y-indexeddb (Offline Persistence)

Stores the Y.Doc in the browser's IndexedDB for offline access and fast initial loads.

```javascript
import { IndexeddbPersistence } from 'y-indexeddb'

const persistence = new IndexeddbPersistence('doc-name', doc)
persistence.on('synced', () => {
  console.log('Loaded from IndexedDB')
})
```

**CAD relevance:** Critical for offline-first CAD workflows. Users can continue working without network access and sync when reconnected. The provider automatically merges offline changes.

#### Combining Providers

Multiple providers can be used simultaneously on the same Y.Doc:

```javascript
const doc = new Y.Doc()
const wsProvider = new WebsocketProvider('wss://server.com', 'room', doc)
const idbProvider = new IndexeddbPersistence('room', doc)
// Both active simultaneously — IndexedDB for fast load + offline, WS for real-time sync
```

### 1.3 Awareness Protocol

The Awareness protocol manages ephemeral, per-user state that should NOT be persisted — cursor positions, selections, user presence.

```javascript
import * as awarenessProtocol from 'y-protocols/awareness.js'

const awareness = new awarenessProtocol.Awareness(doc)

// Set local user state
awareness.setLocalState({
  user: { name: 'Alice', color: '#ff0000' },
  cursor: { x: 150, y: 300 },
  selectedShapes: ['shape-001', 'shape-003'],
  viewport: { x: 0, y: 0, zoom: 1.5 }
})

// Update single field (preserves other fields)
awareness.setLocalStateField('cursor', { x: 200, y: 350 })

// Read all connected users
awareness.getStates().forEach((state, clientID) => {
  console.log(`${state.user.name} at (${state.cursor.x}, ${state.cursor.y})`)
})

// Listen for presence changes
awareness.on('change', ({ added, updated, removed }) => {
  // added/updated/removed are arrays of clientIDs
})

// Clean up on disconnect
window.addEventListener('beforeunload', () => {
  awarenessProtocol.removeAwarenessStates(awareness, [doc.clientID], 'window unload')
})
```

**CAD presence data to track:**
- Cursor position (page coordinates)
- Selected shapes (array of shape IDs)
- Active tool (select, pen, rectangle, etc.)
- Viewport bounds (what area the user is viewing)
- User identity (name, color, avatar)
- Editing state (which shape is being edited)

### 1.4 Sub-Documents

Sub-documents allow lazy loading of document sections. Each sub-document is a full Y.Doc with its own GUID, loaded on demand.

```javascript
// Root document
const rootDoc = new Y.Doc()
const docsMap = rootDoc.getMap('documents')

// Create sub-document
const subDoc = new Y.Doc({ guid: 'page-001' })
subDoc.getText().insert(0, 'Content of page 1')
docsMap.set('page-001', subDoc)

// Lazy loading on another client
rootDoc.on('subdocs', ({ loaded, added, removed }) => {
  loaded.forEach(subdoc => {
    // Create a provider for each loaded subdoc
    new WebsocketProvider('wss://server.com', subdoc.guid, subdoc)
  })
})

// Load a subdoc on demand
const subDoc = rootDoc.getMap('documents').get('page-001')
subDoc.load()  // Triggers the 'subdocs' event

subDoc.on('synced', () => {
  subDoc.getText().toString() // Content available after sync
})
```

**CAD relevance:** Sub-documents are crucial for large CAD projects with multiple pages/sheets. Instead of loading the entire project (potentially hundreds of drawing sheets), you load only the active sheet and lazy-load others as the user navigates. Each sheet gets its own sync channel.

### 1.5 UndoManager

The UndoManager provides collaborative-aware undo/redo. It only undoes the local user's changes, not other users' changes.

```javascript
const ytext = doc.getText('main')
const ymap = doc.getMap('shapes')

const undoManager = new Y.UndoManager([ytext, ymap], {
  trackedOrigins: new Set([null]),  // Track changes without explicit origin
  captureTimeout: 500              // Group changes within 500ms into one undo step
})

// Make changes
doc.transact(() => {
  ymap.set('x', 100)
  ymap.set('y', 200)
}, null) // null origin = tracked by default

// Undo/Redo
undoManager.undo()
undoManager.redo()

// Listen to undo/redo events
undoManager.on('stack-item-added', event => {
  // event.type: 'undo' | 'redo'
  // event.stackItem.meta: Map for storing metadata
})

// Store metadata on undo items (e.g., selection state)
undoManager.on('stack-item-added', event => {
  event.stackItem.meta.set('selection', editor.getSelectedShapeIds())
})
undoManager.on('stack-item-popped', event => {
  const selection = event.stackItem.meta.get('selection')
  if (selection) editor.setSelectedShapeIds(selection)
})
```

**Key behaviors:**
- Only tracks changes from specified origins (via `trackedOrigins`)
- Changes within `captureTimeout` ms are merged into a single undo step
- Concurrent changes from other users are NOT undone — only local changes
- Can track multiple shared types simultaneously

### 1.6 Performance Characteristics

**Document size:** Yjs uses a highly optimized binary encoding. Benchmarks show:
- 100,000 sequential text insertions: ~30KB encoded
- The encoding is typically 10-30x smaller than JSON representation
- State vectors enable efficient differential sync (only send what's changed)

**Sync efficiency:**

```javascript
// Full sync (initial connection)
const fullState = Y.encodeStateAsUpdate(doc)  // Complete document as binary

// Differential sync (subsequent updates)
const stateVector = Y.encodeStateVector(doc)       // What I have
const diff = Y.encodeStateAsUpdate(doc, stateVector) // What you're missing

// Memory-efficient server sync (no Y.Doc needed)
const sv = Y.encodeStateVectorFromUpdate(storedBinary)
const diff = Y.diffUpdate(storedBinary, remoteSV)
const merged = Y.mergeUpdates([storedBinary, remoteUpdate])
```

**Critical performance considerations for CAD:**
- **Garbage collection (`gc: true`):** Permanently removes deleted content. Reduces document size but prevents undo of garbage-collected operations. For CAD, consider `gc: false` if you need full history.
- **Transaction batching:** Always use `doc.transact()` for multi-property updates to avoid N separate update events.
- **Sub-documents:** Essential for projects with many pages — keeps memory usage proportional to active page, not total project.
- **Update merging:** `Y.mergeUpdates()` compacts multiple update messages into one, reducing storage and initial load time.

### 1.7 Structuring Drawing Data in Yjs

**Recommended structure for CAD:**

```javascript
const doc = new Y.Doc()

// Top-level containers
const shapes = doc.getMap('shapes')           // shape-id => Y.Map of properties
const bindings = doc.getMap('bindings')       // binding-id => Y.Map
const pages = doc.getMap('pages')             // page-id => Y.Map with page metadata
const assets = doc.getMap('assets')           // asset-id => Y.Map (images, etc.)
const layerOrder = doc.getArray('layerOrder') // Ordered array of shape IDs (z-index)

// Each shape is a nested Y.Map
const shape = new Y.Map()
shape.set('id', 'shape-001')
shape.set('type', 'rectangle')
shape.set('x', 100)
shape.set('y', 200)
shape.set('rotation', 0)
shape.set('parentId', 'page:page1')

const props = new Y.Map()
props.set('w', 300)
props.set('h', 150)
props.set('color', 'blue')
props.set('fill', 'solid')
shape.set('props', props)

shapes.set('shape-001', shape)
```

**Alternative: Flat record store (tldraw-compatible):**

```javascript
// Store all records in a single Y.Map, keyed by ID
const store = doc.getMap('tldraw-store')

// Each record is a plain object (not nested Y.Map)
// Serialized as JSON string or Y.Map
store.set('shape:abc123', new Y.Map([
  ['id', 'shape:abc123'],
  ['typeName', 'shape'],
  ['type', 'geo'],
  ['x', 100],
  ['y', 200],
  ['props', new Y.Map([['w', 300], ['h', 150], ['geo', 'rectangle']])]
]))
```

### 1.8 Persistence Strategies

**Strategy 1: Update Log (append-only)**
Store every Y.Doc update as a binary blob, replay on load.
```
updates table: (doc_id, update_index, update_blob)
```
Pros: Simple, preserves full history. Cons: Load time grows with history.

**Strategy 2: Snapshot + Updates**
Periodically snapshot the full state, store only updates since last snapshot.
```
snapshots table: (doc_id, snapshot_blob, created_at)
updates table: (doc_id, update_blob, created_at, after_snapshot_id)
```
Pros: Fast load (snapshot + few updates). Cons: Snapshot generation overhead.

**Strategy 3: State-vector based (recommended for production)**
```javascript
// Server stores merged state
let storedState = Y.encodeStateAsUpdate(doc)

// On new update from client
storedState = Y.mergeUpdates([storedState, clientUpdate])

// On client reconnect
const clientSV = Y.encodeStateVectorFromUpdate(clientState)
const diff = Y.diffUpdate(storedState, clientSV)
// Send diff to client
```

**Strategy 4: Database per record (hybrid)**
Store each shape as a database row for queryability, plus Yjs binary for CRDT sync. Reconcile on load.

---

## Part 2: tldraw Deep Dive

### 2.1 Store Architecture

tldraw's store (`@tldraw/store`) is a reactive, typed record database. It is NOT built on Yjs — it has its own sync protocol called "tldraw sync."

**Core concepts:**
- **Records**: Immutable JSON objects with `id` and `typeName`
- **Reactive**: Changes automatically trigger UI updates via signals
- **Change tracking**: Complete history of all modifications
- **Schema validation**: Full TypeScript support with compile-time + runtime validation
- **Scoped records**: `document` (persisted + synced), `session` (local), `presence` (synced but not persisted)

```typescript
// Shape record example
{
  id: 'shape:abc123',       // Branded string: type prefix + unique ID
  typeName: 'shape',
  type: 'geo',
  x: 100,
  y: 200,
  rotation: 0,
  parentId: 'page:page1',
  index: 'a1',              // Fractional index for z-ordering
  isLocked: false,
  opacity: 1,
  props: {
    geo: 'rectangle',
    w: 300,
    h: 150,
    color: 'blue',
    fill: 'solid',
    // ... shape-type-specific properties
  },
  meta: {}                   // User-defined metadata
}
```

**Record scopes:**

| Scope | Persisted | Synced | Example |
|-------|-----------|--------|---------|
| `document` | Yes | Yes | Shapes, pages, bindings, assets |
| `session` | Optional | No | Current page, camera position |
| `presence` | No | Yes | Cursor positions, user selections |

### 2.2 Editor API

The Editor is the primary API surface for interacting with tldraw. It wraps the store with higher-level methods.

```typescript
// Creating shapes
editor.createShape({
  type: 'geo',
  x: 100,
  y: 100,
  props: { w: 200, h: 150, geo: 'rectangle' }
})

// Bulk creation
editor.createShapes([
  { type: 'geo', x: 0, y: 0, props: { w: 100, h: 100 } },
  { type: 'text', x: 200, y: 0, props: { text: 'Hello' } }
])

// Reading shapes
const shape = editor.getShape(shapeId)
const allShapes = editor.getCurrentPageShapes()
const selectedIds = editor.getSelectedShapeIds()

// Updating shapes
editor.updateShape({ id: shape.id, x: 200 })

// Deleting
editor.deleteShape(shapeId)

// Camera
const camera = editor.getCamera()         // { x, y, z } where z = zoom
editor.setCamera({ x: 0, y: 0, z: 1 })
editor.zoomIn()
editor.zoomOut()
editor.zoomToFit()
editor.zoomToSelection()

// Coordinate conversion
const pagePoint = editor.screenToPage({ x: mouseX, y: mouseY })
const screenPoint = editor.pageToScreen({ x: shapeX, y: shapeY })
const localPoint = editor.getPointInShapeSpace(shape, pagePoint)

// Viewport
const viewportBounds = editor.getViewportPageBounds()

// History (Undo/Redo)
editor.markHistoryStoppingPoint()  // Create undo checkpoint
editor.undo()
editor.redo()
editor.bail()                       // Undo and discard (can't redo)
```

### 2.3 Shape System

The shape system separates data (records in the store) from behavior (ShapeUtil classes).

#### Built-in Shape Types

| Category | Types |
|----------|-------|
| Basic | `geo`, `text`, `note` |
| Drawing | `draw`, `line`, `highlight` |
| Media | `image`, `video`, `bookmark`, `embed` |
| Structural | `frame`, `group` |
| Connectors | `arrow` |

#### Creating Custom Shapes (Critical for CAD)

Every custom shape requires:
1. **Type definition** with props interface
2. **ShapeUtil class** with 4 required methods + optional overrides
3. **Registration** via the `shapeUtils` prop

```tsx
import {
  ShapeUtil, TLShape, Rectangle2d, Geometry2d,
  HTMLContainer, T, RecordProps, resizeBox, TLResizeInfo
} from 'tldraw'

// 1. Extend type system
declare module 'tldraw' {
  export interface TLGlobalShapePropsMap {
    'cad-wall': { w: number; h: number; thickness: number; material: string }
  }
}

type CadWallShape = TLShape<'cad-wall'>

// 2. Define ShapeUtil
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
          <span style={{ fontSize: 10 }}>{shape.props.thickness}mm</span>
        </div>
      </HTMLContainer>
    )
  }

  // Selection indicator
  indicator(shape: CadWallShape) {
    return <rect width={shape.props.w} height={shape.props.h} />
  }

  // Capability flags
  override canResize() { return true }
  override canEdit() { return true }
  override isAspectRatioLocked() { return false }

  // Resize handler
  override onResize(shape: CadWallShape, info: TLResizeInfo<CadWallShape>) {
    return resizeBox(shape, info)
  }

  // Lifecycle hooks
  override onBeforeCreate(next: CadWallShape) {
    // Snap thickness to standard values
    const snapped = Math.round(next.props.thickness / 50) * 50
    return { ...next, props: { ...next.props, thickness: snapped } }
  }
}

// 3. Register
function App() {
  return (
    <Tldraw
      shapeUtils={[CadWallShapeUtil]}
      onMount={(editor) => {
        editor.createShape({ type: 'cad-wall', x: 100, y: 100 })
      }}
    />
  )
}
```

#### Geometry System (Hit Testing)

tldraw provides geometry classes for precise hit testing:

| Class | Use Case |
|-------|----------|
| `Rectangle2d` | Axis-aligned rectangles |
| `Circle2d` | True circles |
| `Ellipse2d` | Ellipses |
| `Polygon2d` | Arbitrary closed polygons |
| `Polyline2d` | Open paths |
| `Arc2d` | Circular arcs |
| `Stadium2d` | Rounded rectangles |
| `Group2d` | Composite geometry |

**Key operations:** `bounds` (AABB), `getVertices()`, `nearestPoint()`, `hitTestPoint(point, margin)`, `hitTestLineSegment()`, `intersectLineSegment()`

**For CAD:** You can create complex custom geometries for irregular shapes (L-shaped rooms, curved walls, custom profiles) using `Polygon2d` or `Group2d` with composite geometries.

#### ShapeUtil Lifecycle Hooks

| Hook | Phase | Can Modify Record? | Use Case |
|------|-------|-------------------|----------|
| `onBeforeCreate` | Before store write | Yes (return modified) | Validation, snapping, defaults |
| `onBeforeUpdate` | Before store write | Yes (return modified) | Constrain values, enforce rules |
| `onResize` | During resize | Yes (return partial update) | Custom resize behavior |
| `onRotate` | During rotation | Yes | Snap rotation angles |
| `onTranslate` | During move | Yes | Grid snapping, boundary constraints |
| `onDoubleClick` | User interaction | No (side effects only) | Toggle edit mode |
| `onChildrenChange` | Children modified | No | Update parent bounds |
| `canResize()` | Query | N/A | Enable/disable resize handles |
| `canEdit()` | Query | N/A | Enable/disable double-click editing |
| `canBind()` | Query | N/A | Enable/disable binding connections |

#### Schema Migrations

tldraw supports versioned shape schemas with up/down migrations, essential for evolving a CAD application:

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
    2: {
      up: (shape) => ({ ...shape, props: { ...shape.props, fireRating: 'none' } }),
      down: (shape) => {
        const { fireRating, ...rest } = shape.props
        return { ...shape, props: rest }
      },
    },
  },
})
```

### 2.4 Tool System

Tools define how user interactions (clicks, drags) create or modify shapes. tldraw includes built-in tools (select, draw, eraser, hand, laser) and supports custom tools.

```typescript
import { StateNode, TLEventHandlers } from 'tldraw'

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

  override onPointerUp: TLEventHandlers['onPointerUp'] = (info) => {
    // Finalize wall
  }
}

// Register
<Tldraw tools={[WallTool]} />
```

### 2.5 Side Effects System

Side effects are lifecycle hooks on the STORE level (not shape-specific) that run when ANY record is created, updated, or deleted.

```typescript
// Before handlers — can modify/block changes
editor.sideEffects.registerBeforeChangeHandler('shape', (prev, next, source) => {
  // source: 'user' | 'remote'
  if (next.x < 0) return prev  // Block change (return previous)
  return next                   // Allow change (return next)
})

editor.sideEffects.registerBeforeDeleteHandler('shape', (shape, source) => {
  if (shape.isLocked) return false  // Prevent deletion
  return true
})

// After handlers — react to completed changes
editor.sideEffects.registerAfterCreateHandler('shape', (shape, source) => {
  if (source === 'user') logAction('created', shape)
})

editor.sideEffects.registerAfterChangeHandler('shape', (prev, next, source) => {
  // Update related shapes, recalculate constraints
})

// Batch handler — runs once after all changes in a transaction
editor.sideEffects.registerOperationCompleteHandler((source) => {
  if (source === 'user') scheduleAutosave()
})
```

**CAD relevance:** Side effects are the backbone for implementing constraint systems (walls meeting at corners), auto-dimensioning, and cross-shape validation.

### 2.6 Signals / Reactivity

tldraw uses a signals-based reactivity system. The `track()` wrapper makes React components automatically re-render when accessed signals change.

```tsx
import { track, useEditor, computed } from 'tldraw'

const ShapeInspector = track(() => {
  const editor = useEditor()
  const selected = editor.getSelectedShapes()

  return (
    <div>
      <p>Selected: {selected.length} shapes</p>
      {selected.map(s => (
        <div key={s.id}>{s.type} at ({s.x}, {s.y})</div>
      ))}
    </div>
  )
})

// Computed signals for derived values
const totalArea = computed('totalArea', () => {
  return editor.getCurrentPageShapes()
    .filter(s => s.type === 'geo')
    .reduce((sum, s) => sum + s.props.w * s.props.h, 0)
})
```

### 2.7 Collaboration via tldraw sync

tldraw has its own sync protocol (NOT Yjs-based). It uses `@tldraw/sync` and `@tldraw/sync-core`.

**Client setup:**

```tsx
import { Tldraw } from 'tldraw'
import { useSync } from '@tldraw/sync'

function CollaborativeEditor({ roomId }) {
  const store = useSync({
    uri: `wss://my-server.com/connect/${roomId}`,
    assets: myAssetStore,
    shapeUtils: [...customShapeUtils, ...defaultShapeUtils],
    bindingUtils: [...customBindingUtils, ...defaultBindingUtils],
  })

  return <Tldraw store={store} shapeUtils={customShapeUtils} />
}
```

**Server setup:**

```typescript
import { TLSocketRoom, SQLiteSyncStorage } from '@tldraw/sync-core'
import { createTLSchema, defaultShapeSchemas } from '@tldraw/tlschema'

const schema = createTLSchema({
  shapes: {
    ...defaultShapeSchemas,
    'cad-wall': { props: cadWallProps, migrations: cadWallMigrations },
  },
})

const storage = new SQLiteSyncStorage({ sql })
const room = new TLSocketRoom({ schema, storage })

// Handle WebSocket connections
wss.on('connection', (ws) => {
  room.handleSocketConnect({ sessionId: generateId(), socket: ws })
})
```

**Server options:**
- `InMemorySyncStorage`: Simple, volatile (data lost on restart)
- `SQLiteSyncStorage`: Recommended for production, auto-manages tables
- Cloudflare Durable Objects: tldraw's production architecture (tldraw.com uses this)

### 2.8 Parent-Child Relationships

- **Frames**: Container shapes with visual clipping boundary. Children position relative to frame origin. Moving frame moves children.
- **Groups**: Logical containers, no visual representation. Double-click to enter group, select children. Empty groups auto-delete.
- **Coordinate spaces**: Screen space -> Page space -> Parent space -> Local space

### 2.9 Embedding tldraw in React

```tsx
import { Tldraw } from 'tldraw'
import 'tldraw/tldraw.css'

function App() {
  return (
    <div style={{ position: 'fixed', inset: 0 }}>
      <Tldraw
        shapeUtils={[...customShapeUtils]}
        tools={[...customTools]}
        snapshot={savedState}
        onMount={(editor) => {
          // Editor is ready
          editor.createShape({ type: 'geo', x: 0, y: 0 })
        }}
      />
    </div>
  )
}
```

**Customizing UI around tldraw:**
- Override components via `components` prop (`CollaboratorCursor`, `SharePanel`, `Toolbar`, etc.)
- Use `uiOverrides` for toolbar customization
- Place custom React components inside `<Tldraw>` — they render as overlays

---

## Part 3: tldraw + Yjs Integration

### 3.1 Integration Approaches

There are two main approaches to integrate tldraw with Yjs:

#### Approach A: Use tldraw sync (Recommended by tldraw team)

tldraw's built-in sync is NOT based on Yjs. It uses its own `@tldraw/sync-core` protocol with `TLSocketRoom`. This is the officially supported path.

**Pros:** First-class support, schema migrations, battle-tested on tldraw.com, simpler setup.
**Cons:** Tied to tldraw's sync protocol, less flexibility for custom CRDT structures, no peer-to-peer option.

#### Approach B: Bridge tldraw Store to Yjs (Custom Integration)

Map tldraw's store records to/from a Yjs Y.Map. This is the approach for when you need Yjs specifically (e.g., shared data model with other CRDT-aware components).

**Reference implementation:** `tlsync-yjs` by shahriar-shojib (GitHub). This is a WIP library that bridges tldraw v2's store to Yjs using y-websocket + Hocuspocus backend.

**Architecture of the bridge:**

```
tldraw Editor <-> Store <-> Yjs Bridge <-> Y.Doc <-> Provider <-> Server/Peers
```

**The bridge must:**
1. Listen to `store.listen()` for local changes
2. Convert tldraw record diffs to Y.Map operations
3. Listen to Yjs `ymap.observe()` for remote changes
4. Convert Y.Map changes back to `store.mergeRemoteChanges()`

**Conceptual bridge implementation:**

```typescript
import * as Y from 'yjs'
import { createTLStore, TLRecord } from 'tldraw'

function createYjsBridge(doc: Y.Doc, store: ReturnType<typeof createTLStore>) {
  const yStore = doc.getMap('tldraw-records')

  // Local changes -> Yjs
  store.listen((entry) => {
    doc.transact(() => {
      for (const record of Object.values(entry.changes.added)) {
        yStore.set(record.id, record)  // Store as JSON
      }
      for (const [, next] of Object.values(entry.changes.updated)) {
        yStore.set(next.id, next)
      }
      for (const record of Object.values(entry.changes.removed)) {
        yStore.delete(record.id)
      }
    })
  }, { source: 'user' })  // Only local changes

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

**Critical considerations for the bridge:**
- Use `store.mergeRemoteChanges()` to apply Yjs changes — this marks them as remote, preventing echo loops
- Use `store.listen({ source: 'user' })` to only capture local changes for Yjs sync
- Awareness: Map Yjs awareness to tldraw's presence records
- Schema validation: tldraw validates records on `put()` — ensure Yjs data conforms to schema

### 3.2 Why You Might Want Yjs Instead of tldraw sync

| Reason | Details |
|--------|---------|
| **Shared data model** | Other parts of your app (text editor, spreadsheet, tree view) also use Yjs |
| **Offline-first** | y-indexeddb provides robust offline persistence |
| **P2P option** | y-webrtc enables serverless collaboration |
| **Ecosystem** | Yjs has providers for Redis, PostgreSQL, MongoDB, etc. |
| **Sub-documents** | Lazy-load drawing pages independently |
| **Custom CRDT logic** | Fine-grained control over merge behavior |

| Reason for tldraw sync | Details |
|------------------------|---------|
| **Official support** | Maintained by tldraw team, guaranteed compatibility |
| **Schema migrations** | Automatic data migration between versions |
| **Simpler setup** | Less bridging code, fewer failure modes |
| **Battle-tested** | Runs tldraw.com in production |

### 3.3 Presence / Awareness Mapping

If using Yjs awareness with tldraw, you need to map awareness state to tldraw's presence records:

```typescript
// Yjs awareness -> tldraw presence
awareness.on('change', ({ added, updated }) => {
  const states = awareness.getStates()

  store.mergeRemoteChanges(() => {
    for (const clientId of [...added, ...updated]) {
      const state = states.get(clientId)
      if (!state) continue

      store.put([{
        id: `instance_presence:${clientId}`,
        typeName: 'instance_presence',
        cursor: state.cursor,
        color: state.user.color,
        userName: state.user.name,
        selectedShapeIds: state.selectedShapes || [],
        // ... other presence fields
      }])
    }
  })
})

// tldraw changes -> Yjs awareness
store.listen((entry) => {
  // Detect local cursor/selection changes and update awareness
  for (const [, next] of Object.values(entry.changes.updated)) {
    if (next.typeName === 'instance') {
      awareness.setLocalStateField('cursor', {
        x: next.cursor?.x,
        y: next.cursor?.y,
      })
    }
  }
}, { source: 'user', scope: 'session' })
```

---

## Part 4: Excalidraw as Alternative

### 4.1 Element Structure

Excalidraw uses a flat array of element objects. Each element is a plain JSON object:

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [
    {
      "id": "pologsyG-tAraPgiN9xP9b",
      "type": "rectangle",
      "x": 928,
      "y": 319,
      "width": 134,
      "height": 90,
      "angle": 0,
      "strokeColor": "#000000",
      "backgroundColor": "#ffffff",
      "fillStyle": "solid",
      "strokeWidth": 1,
      "roughness": 1,
      "opacity": 100,
      "groupIds": [],
      "boundElements": [],
      "isDeleted": false,
      "customData": { "customId": "162" }
    }
  ],
  "appState": {
    "gridSize": 20,
    "viewBackgroundColor": "#ffffff"
  },
  "files": {
    "3cebd7720...": {
      "mimeType": "image/png",
      "id": "3cebd7720...",
      "dataURL": "data:image/png;base64,...",
      "created": 1690295874454
    }
  }
}
```

**Built-in element types:** `rectangle`, `ellipse`, `diamond`, `line`, `arrow`, `freedraw`, `text`, `image`, `frame`, `embeddable`

**Custom data:** Each element supports a `customData: Record<string, any>` field for application-specific data.

### 4.2 Collaboration

Excalidraw has built-in collaboration via its `@excalidraw/excalidraw` npm package. The open-source version provides the rendering/editing engine, but the collaboration backend (used on excalidraw.com) is separate.

For self-hosted collaboration, you would need to:
1. Implement a WebSocket server
2. Broadcast element updates between clients
3. Handle conflict resolution (Excalidraw uses last-write-wins on the element level)

Excalidraw does NOT use CRDTs by default. Its collaboration is simpler — full state sync with last-writer-wins. This works for whiteboards but is problematic for CAD where concurrent edits to different properties of the same element should merge.

### 4.3 Custom Element Types

Excalidraw has LIMITED support for custom element types compared to tldraw. There is no equivalent to tldraw's ShapeUtil system. You can:
- Use `customData` to attach metadata to existing element types
- Override rendering via the `renderCustomElement` callback (limited)
- Fork the library and add element types directly (heavy maintenance burden)

### 4.4 Export Capabilities

```javascript
import { exportToCanvas, exportToSvg, exportToBlob } from "@excalidraw/excalidraw"

// Export to Canvas
const canvas = await exportToCanvas({
  elements: excalidrawAPI.getSceneElements(),
  appState: { ...appState, exportWithDarkMode: false, exportBackground: true },
  files: excalidrawAPI.getFiles(),
})

// Add custom overlays
const ctx = canvas.getContext("2d")
ctx.font = "30px Arial"
ctx.fillText("My Overlay", 50, 50)

// Export to SVG
const svg = await exportToSvg({ elements, appState, files })

// Export to Blob (PNG)
const blob = await exportToBlob({ elements, appState, files, mimeType: "image/png" })

// Serialize to JSON
import { serializeAsJSON } from "@excalidraw/excalidraw"
const json = serializeAsJSON({ elements, appState })
```

### 4.5 Excalidraw vs tldraw for CAD

| Factor | Excalidraw | tldraw |
|--------|-----------|--------|
| **Custom shapes** | Limited (`customData` only) | Full ShapeUtil system |
| **Custom tools** | Not supported | Full tool system (StateNode) |
| **Geometry/hit testing** | Basic bounding box | Rich geometry classes |
| **Collaboration** | LWW (no CRDTs) | Own sync protocol OR Yjs bridge |
| **Rendering control** | Limited | Full SVG/HTML/Canvas control |
| **Schema migrations** | None | Built-in migration system |
| **Side effects** | None | Full lifecycle hook system |
| **TypeScript** | Partial | Full type safety |
| **Visual style** | Hand-drawn/sketchy (by design) | Clean/professional |
| **Export** | SVG, PNG, JSON | SVG, PNG, JSON + custom formats |
| **Performance** | Good for <1000 elements | Culling, caching, optimized for large canvases |
| **Constraint system** | None | Via side effects + custom shapes |
| **Documentation** | Moderate | Excellent (tldraw.dev) |

**Verdict:** Excalidraw is unsuitable for CAD. Its hand-drawn aesthetic, lack of custom shape extensibility, and absence of CRDT-based collaboration make it a poor fit. tldraw is clearly the better foundation for a collaborative CAD application.

---

## Part 5: Architecture Recommendations

### 5.1 Recommended Stack

```
Frontend:  tldraw SDK + React + Custom ShapeUtils + Custom Tools
Sync:      Option A: tldraw sync (simpler, recommended start)
           Option B: Yjs bridge (if you need shared CRDT with other components)
Backend:   Cloudflare Workers + Durable Objects (tldraw sync)
           OR Node.js + y-websocket + Redis (Yjs)
Persistence: SQLite (via SQLiteSyncStorage) or PostgreSQL
Offline:   y-indexeddb (Yjs) or localStorage snapshots (tldraw sync)
```

### 5.2 Data Model for CAD

```
Y.Doc (or tldraw Store)
|
+-- shapes (Y.Map / TLRecords)
|   +-- shape:wall-001  { type: 'cad-wall', x, y, props: { length, thickness, material } }
|   +-- shape:door-001  { type: 'cad-door', x, y, props: { width, swing, fireRated } }
|   +-- shape:dim-001   { type: 'cad-dimension', props: { startRef, endRef, offset } }
|   +-- shape:text-001  { type: 'text', props: { text, fontSize } }
|
+-- bindings (Y.Map / TLRecords)
|   +-- binding:001 { fromId: 'door-001', toId: 'wall-001', type: 'cad-embed' }
|   +-- binding:002 { fromId: 'dim-001', toId: 'wall-001', type: 'cad-dimension-ref' }
|
+-- pages (Y.Map / TLRecords)
|   +-- page:floor-plan-1  { name: 'Ground Floor' }
|   +-- page:floor-plan-2  { name: 'First Floor' }
|
+-- assets (Y.Map / TLRecords)
    +-- asset:img-001 { type: 'image', src: 'https://...', mimeType: 'image/png' }
```

### 5.3 Custom Shape Types for CAD

| Shape Type | Props | Geometry | Notes |
|-----------|-------|----------|-------|
| `cad-wall` | length, thickness, material, fireRating | Rectangle2d or Polygon2d | Snaps to grid, connects at endpoints |
| `cad-door` | width, swingAngle, direction, type | Arc2d + Rectangle2d (Group2d) | Bound to wall via binding |
| `cad-window` | width, height, sillHeight | Rectangle2d | Bound to wall |
| `cad-dimension` | startRef, endRef, offset, unit | Polyline2d | References two shapes, auto-calculates |
| `cad-room` | name, area (computed) | Polygon2d | Closed polygon from walls |
| `cad-column` | diameter, shape | Circle2d or Rectangle2d | Structural element |
| `cad-beam` | width, depth, span | Rectangle2d | Structural element |
| `cad-annotation` | text, type (note/callout) | Rectangle2d | Leader line via binding |

### 5.4 Implementation Phases

**Phase 1: Foundation (2-3 weeks)**
- Set up tldraw with React
- Implement 3-4 basic CAD shapes (wall, door, window, dimension)
- Add custom tools for each shape type
- Set up tldraw sync for basic collaboration

**Phase 2: Constraints & Intelligence (2-3 weeks)**
- Wall endpoint snapping (side effects)
- Door/window binding to walls
- Auto-dimensioning
- Grid and guideline snapping
- Undo/redo integration

**Phase 3: Advanced Collaboration (1-2 weeks)**
- User presence (cursors, selections, viewports)
- Conflict resolution testing
- Offline support (if using Yjs)
- Multi-page/sheet support

**Phase 4: Production Features (2-3 weeks)**
- Export to DXF/SVG/PDF
- Layer management
- Symbol library (reusable components)
- Measurement and area calculation
- Print layout

### 5.5 Key Technical Decisions

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| Sync protocol | Start with tldraw sync, evaluate Yjs if needed | Simpler, officially supported, sufficient for initial MVP |
| Deployment | Cloudflare Workers + Durable Objects | tldraw's proven architecture, handles room isolation natively |
| Custom shapes | Full ShapeUtil per CAD element type | Maximum control over rendering, geometry, and behavior |
| Constraint system | tldraw side effects + custom constraint solver | Side effects intercept changes before store write |
| Persistence | SQLiteSyncStorage | Recommended by tldraw, auto-manages schema |
| Offline | Evaluate after MVP | tldraw sync handles reconnection; full offline needs Yjs bridge |
| Undo/Redo | tldraw's built-in history system | Handles collaboration correctly (only undoes local changes) |

### 5.6 Performance Considerations for Large CAD Documents

1. **Culling:** tldraw automatically culls shapes outside the viewport (`canCull()` on ShapeUtil). Ensure custom shapes support this.
2. **Geometry caching:** tldraw caches geometry computations. Avoid expensive operations in `getGeometry()`.
3. **Computed caches:** Use `store.createComputedCache()` for expensive derived data (area calculations, constraint solving).
4. **Sub-documents (Yjs only):** Separate pages into sub-documents for lazy loading.
5. **Fractional indexing:** tldraw uses fractional indices for z-ordering — no array reindexing.
6. **Batch operations:** Use `editor.batch()` or `store.atomic()` for multi-shape operations.
7. **Level of detail:** Render simplified shapes at low zoom levels, detailed at high zoom.

---

## Appendix A: Key Links

| Resource | URL |
|----------|-----|
| Yjs GitHub | https://github.com/yjs/yjs |
| Yjs Documentation | https://docs.yjs.dev |
| y-websocket | https://github.com/yjs/y-websocket |
| y-redis | https://github.com/yjs/y-redis |
| y-indexeddb | https://github.com/yjs/y-indexeddb |
| tldraw Documentation | https://tldraw.dev |
| tldraw GitHub | https://github.com/tldraw/tldraw |
| tldraw Shapes Docs | https://tldraw.dev/sdk-features/shapes |
| tldraw Store Docs | https://tldraw.dev/sdk-features/store |
| tldraw Side Effects | https://tldraw.dev/sdk-features/side-effects |
| tldraw Collaboration | https://tldraw.dev/docs/collaboration |
| tldraw Sync | https://tldraw.dev/docs/sync |
| tldraw Cloudflare Template | https://github.com/tldraw/tldraw-sync-cloudflare |
| tldraw + Yjs (WIP) | https://github.com/shahriar-shojib/tlsync-yjs |
| tldraw Examples | https://examples.tldraw.com |
| Excalidraw GitHub | https://github.com/excalidraw/excalidraw |

## Appendix B: Yjs Binary Protocol Summary

```
Sync Step 1:  Client A sends stateVector to Client B
Sync Step 2:  Client B computes diff = encodeStateAsUpdate(docB, stateVectorA)
              Client B sends diff to Client A
              Client A applies: applyUpdate(docA, diff)
Update:       When Client A makes a local change, it sends the update to all peers
              Peers apply: applyUpdate(doc, update)
Awareness:    Separate protocol — encodeAwarenessUpdate / applyAwarenessUpdate
              Broadcasts local state changes to all peers
              Auto-timeout for disconnected users (30s default)
```

## Appendix C: tldraw Record Types

| Type | typeName | Scope | Description |
|------|----------|-------|-------------|
| Shape | `shape` | document | Visual element on canvas |
| Page | `page` | document | Drawing page/sheet |
| Binding | `binding` | document | Relationship between shapes |
| Asset | `asset` | document | Image, video, or bookmark data |
| Instance | `instance` | session | Per-editor instance settings |
| Camera | `camera` | session | Viewport position and zoom |
| InstancePageState | `instance_page_state` | session | Per-page selection/focus state |
| InstancePresence | `instance_presence` | presence | Cursor, selection for other users |
| Pointer | `pointer` | presence | Detailed pointer state |
