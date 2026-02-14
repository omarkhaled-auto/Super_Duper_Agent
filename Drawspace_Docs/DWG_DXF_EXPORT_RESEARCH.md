# DWG/DXF Export from Web Canvas — Library & Tool Research

**Date:** 2026-02-12
**Purpose:** Comprehensive research on libraries, tools, and patterns needed to implement DWG/DXF export from a web-based drawing canvas.

---

## Table of Contents

1. [JavaScript DXF Libraries](#1-javascript-dxf-libraries)
2. [Python ezdxf](#2-python-ezdxf)
3. [Server-Side Conversion Pipeline (DXF to DWG)](#3-server-side-conversion-pipeline)
4. [SVG to DXF Conversion](#4-svg-to-dxf-conversion)
5. [DXF Entity Mapping (Canvas Shape to DXF)](#5-dxf-entity-mapping)
6. [Recommended Architecture](#6-recommended-architecture)

---

## 1. JavaScript DXF Libraries

### 1A. `dxf-writer` (formerly `js-dxf`)

- **npm:** `dxf-writer` (v1.18.4, last published ~3 years ago)
- **Author:** Ognjen Petrovic (original), maintained by Tarik EL JABIRI
- **License:** MIT
- **Repository:** https://github.com/ognjen-petrovic/js-dxf
- **Stars:** Moderate adoption (17 dependents on npm)
- **TypeScript:** Has built-in type declarations

**Supported Entities:**
- Arc, Circle, Ellipse, Line, Point, Polygon, Polyline, Polyline 3D, Spline, Text, 3DFace

**Supported Colors:** Red, Green, Cyan, Blue, Magenta, White (ACI color index)

**Supported Units:** Unitless, Inches, Feet, Miles, Millimeters, Centimeters, Meters, Kilometers, and many more

**Line Types:** CONTINUOUS, DASHED, DOTTED + custom line types

**API Example — Node.js:**
```javascript
const Drawing = require('dxf-writer');
const fs = require('fs');

let d = new Drawing();
d.setUnits('Millimeters');

// Layers
d.addLayer('walls', Drawing.ACI.RED, 'CONTINUOUS');
d.addLayer('dimensions', Drawing.ACI.GREEN, 'CONTINUOUS');
d.setActiveLayer('walls');

// Draw entities
d.drawLine(0, 0, 100, 0);         // LINE
d.drawCircle(50, 50, 25);         // CIRCLE
d.drawArc(50, 50, 30, 0, 90);     // ARC (center, radius, startAngle, endAngle)
d.drawText(10, -10, 5, 0, 'Room 101');  // TEXT (x, y, height, rotation, text)

// Polyline (rectangle)
d.drawPolyline([
  [0, 0], [100, 0], [100, 50], [0, 50], [0, 0]
]);

// Spline from control points
d.drawSplineFromControlPoints([[0, 0], [50, 10], [100, 0]]);

// Custom line type
d.addLineType('DASHDOT', '_ . _ ', [0.5, -0.5, 0.0, -0.5]);

// Generate DXF string
fs.writeFileSync('output.dxf', d.toDxfString());
```

**API Example — Browser (client-side download):**
```javascript
let d = new Drawing();
d.setUnits('Millimeters');
d.drawLine(0, 0, 100, 100);
d.drawCircle(50, 50, 25);

// Create download
var blob = new Blob([d.toDxfString()], { type: 'application/dxf' });
var link = document.getElementById('downloadLink');
link.href = URL.createObjectURL(blob);
link.download = 'drawing.dxf';
```

**SVG Coordinate to DXF Coordinate Conversion (from built-in editor example):**
```javascript
// SVG origin is top-left, DXF origin is bottom-left
function getX(el, att) {
  return parseInt(el.getAttribute(att)) - width / 2;
}
function getY(el, att) {
  return height / 2 - parseInt(el.getAttribute(att)); // Y-axis flip
}

function toDxf() {
  d = new Drawing();
  for (var line of Array.from(svg.node.getElementsByTagName('line'))) {
    d.drawLine(getX(line,'x1'), getY(line,'y1'), getX(line,'x2'), getY(line,'y2'));
  }
  for (var circle of Array.from(svg.node.getElementsByTagName('circle'))) {
    d.drawCircle(getX(circle,'cx'), getY(circle,'cy'), circle.getAttribute('r'));
  }
  var b = new Blob([d.toDxfString()], { type: 'application/dxf' });
  document.getElementById('toDxf').href = URL.createObjectURL(b);
}
```

**Limitations:**
- No DIMENSION entity support
- No HATCH entity support
- No block (INSERT) support
- No paper space / viewport support
- No MTEXT (only simple TEXT)
- No filled regions
- Generates DXF R12 only (older format)

---

### 1B. `@tarikjabiri/dxf` (Modern TypeScript DXF Writer)

- **npm:** `@tarikjabiri/dxf` (v2.8.9)
- **Author:** Tarik EL JABIRI
- **License:** MIT
- **Repository:** https://github.com/dxfjs/writer (116 stars, 22 forks)
- **Documentation:** https://dxf.vercel.app/
- **Written in:** TypeScript (100%)
- **Sponsors:** Archilogic, Slate, Autodrop3d, Village Kit

**Supported Features:**
- Blocks, Hatches, Images, Insert, and more
- All entities are customizable
- Modern ES module + TypeScript support

**API Example:**
```typescript
import { Writer, point } from "@tarikjabiri/dxf";

const writer = new Writer();
const modelSpace = writer.document.modelSpace;

// Add a line
modelSpace.addLine({
  start: point(0, 0),
  end: point(100, 100),
  // Other options...
});

// Get DXF string
const content = writer.stringify();
```

**Advantages over dxf-writer:**
- Written in TypeScript with proper types
- Supports Blocks + INSERT (reusable symbol groups)
- Supports Hatches (filled regions)
- Supports Images
- More actively maintained codebase
- Modern module system

**Limitations:**
- Documentation is sparse (VitePress site with limited API docs)
- Smaller community than ezdxf
- No DIMENSION entity support (not confirmed, docs are minimal)

---

### 1C. Maker.js

- **npm:** `makerjs`
- **Repository:** https://github.com/microsoft/maker.js
- **Author:** Microsoft
- **License:** Apache-2.0
- **Documentation:** https://maker.js.org/docs/
- **Stars:** High (Microsoft-backed)
- **Context7 Score:** 82.5/100, 636 code snippets

**Purpose:** Creating and sharing modular line drawings for CNC and laser cutters.

**Core Concepts:**
- **Paths:** Line, Circle, Arc (primitive drawing elements)
- **Models:** Collections of paths and child models
- **Exporters:** SVG, DXF, PDF

**Supported Path Types:**
- `makerjs.paths.Line([x1, y1], [x2, y2])`
- `makerjs.paths.Circle([cx, cy], radius)`
- `makerjs.paths.Arc([cx, cy], radius, startAngle, endAngle)`

**DXF Export:**
```javascript
var makerjs = require('makerjs');

var line = new makerjs.paths.Line([0, 0], [50, 50]);
var circle = new makerjs.paths.Circle([0, 0], 50);
var arc = new makerjs.paths.Arc([0, 0], 25, 0, 90);

// Export to DXF
var dxfString = makerjs.exporter.toDXF([line, circle, arc]);

// Export model to DXF with options
var model = {
  paths: {
    myLine: line,
    myCircle: circle,
    myArc: arc
  }
};
var dxf = makerjs.exporter.toDXF(model, options);
```

**Advanced Features:**
- Path expansion (offsetting)
- Boolean operations (union, intersection, subtraction)
- Chain finding (connected paths)
- SVG path data export (by layer)
- Built-in models (bolt circle, rectangle, oval, etc.)

**Limitations:**
- Focused on 2D cutting paths, not full engineering drawings
- No DIMENSION, HATCH, TEXT, or block support in DXF export
- No layer management in DXF export
- No paper space or viewports

---

### JavaScript Library Comparison

| Feature | dxf-writer | @tarikjabiri/dxf | Maker.js |
|---------|-----------|------------------|----------|
| TypeScript | Declarations | Native | Yes |
| LINE | Yes | Yes | Yes |
| CIRCLE | Yes | Yes | Yes |
| ARC | Yes | Yes | Yes |
| POLYLINE | Yes | Yes | No |
| SPLINE | Yes | ? | No |
| TEXT | Yes | Yes | No |
| MTEXT | No | ? | No |
| DIMENSION | No | No | No |
| HATCH | No | Yes | No |
| Blocks/INSERT | No | Yes | No |
| Layers | Yes | Yes | No |
| DXF Version | R12 | R2007+ | R12 |
| Client-side | Yes | Yes | Yes |
| npm weekly DL | ~2.5k | ~1k | ~3k |

**Verdict:** For a Drawspace-type app needing engineering drawing export, **none of the JS libraries alone are sufficient**. They lack DIMENSION entities, paper space, and proper annotation support. A **server-side Python (ezdxf) pipeline** is required for production-quality output.

---

## 2. Python ezdxf

- **Package:** `ezdxf` (v1.4.3)
- **Author:** Manfred Moitzi (mozman)
- **License:** MIT
- **Documentation:** https://ezdxf.readthedocs.io/
- **Context7 Score:** 91/100, 2113 code snippets
- **PyPI:** `pip install ezdxf`

**ezdxf is the gold standard for DXF manipulation in any language.** It provides complete control over every DXF entity type, all versions from R12 to R2018, and integrates with ODA File Converter for DWG export.

### 2.1 Creating a Basic Drawing

```python
import ezdxf

# Create new DXF document (R2010 is recommended for modern features)
doc = ezdxf.new("R2010", setup=True)  # setup=True creates default styles
msp = doc.modelspace()

# LINE
msp.add_line((0, 0), (100, 0), dxfattribs={"layer": "Walls", "color": 1})

# CIRCLE
msp.add_circle((50, 50), radius=25, dxfattribs={"layer": "Circles", "color": 2})

# ARC
msp.add_arc(
    center=(50, 50), radius=30,
    start_angle=0, end_angle=90,
    dxfattribs={"layer": "Arcs", "color": 3}
)

doc.saveas("output.dxf")
```

### 2.2 Layer Management

```python
doc = ezdxf.new("R2010")

# Create layers
doc.layers.add("Walls", color=1, linetype="CONTINUOUS")
doc.layers.add("Dimensions", color=3, linetype="CONTINUOUS")
doc.layers.add("Hatches", color=4, linetype="CONTINUOUS")
doc.layers.add("Text", color=7, linetype="CONTINUOUS")
doc.layers.add("Hidden", color=8, linetype="DASHED")

msp = doc.modelspace()
msp.add_line((0, 0), (100, 0), dxfattribs={"layer": "Walls"})
```

### 2.3 LWPOLYLINE (Lightweight Polyline — Rectangles, Polygons)

```python
# Simple rectangle
msp.add_lwpolyline(
    [(0, 0), (100, 0), (100, 50), (0, 50)],
    close=True,
    dxfattribs={"layer": "Walls"}
)

# Polyline with bulge (curved segments)
# bulge > 0 = arc to the right, bulge < 0 = arc to the left
# bulge = 1 means semicircle
msp.add_lwpolyline(
    [(0, 0, 0, 0, 0.5), (10, 0), (10, 10, 0, 0, -0.5), (0, 10)],
    format='xyseb',
    close=True,
    dxfattribs={"layer": "Walls"}
)
```

### 2.4 TEXT and MTEXT

```python
# Simple single-line TEXT
text = msp.add_text(
    "Room 101",
    dxfattribs={
        "insert": (50, 25),
        "height": 2.5,
        "layer": "Text",
        "style": "Standard",
        "rotation": 0,
        "color": 1,
    }
)

# Aligned text
text_aligned = msp.add_text("Fitted Text")
text_aligned.set_placement((0, 5), (10, 5), align="MIDDLE_CENTER")

# Multi-line text (MTEXT) with wrapping
mtext = msp.add_mtext(
    "This is a long MTEXT line with automatic line wrapping!",
    dxfattribs={
        "insert": (0, 10),
        "char_height": 0.7,
        "width": 15.0,
        "style": "Standard",
        "attachment_point": 1,  # TOP_LEFT
        "layer": "Text",
    }
)

# MTEXT with background color
mtext.set_bg_color((108, 204, 193))

# MTEXT with formatting
formatted_text = (
    "normal \\Oover strike\\o normal\\P"
    "normal \\Kstrike through\\k normal\\P"
    "normal \\Lunder line\\l normal"
)
msp.add_mtext(formatted_text, dxfattribs={"insert": (0, 15), "char_height": 0.5, "width": 20.0})
```

### 2.5 DIMENSION Entities

```python
doc = ezdxf.new("R2010", setup=True)  # setup=True needed for dimension styles
msp = doc.modelspace()

# Draw the geometry being dimensioned
msp.add_line((0, 0), (3, 0))

# Horizontal linear dimension
dim = msp.add_linear_dim(
    base=(3, 2),    # location of the dimension line
    p1=(0, 0),      # 1st measurement point
    p2=(3, 0),      # 2nd measurement point
    dimstyle="EZDXF",  # default dimension style
)

# IMPORTANT: Must render the dimension to create the geometry block
dim.render()

doc.saveas("dimension_example.dxf")
```

**Dimension Style Configuration:**
```python
# Create custom dimension style
dimstyle = doc.dimstyles.new("MyStyle")
dimstyle.dxf.dimtxt = 2.5    # text height
dimstyle.dxf.dimasz = 2.0    # arrow size
dimstyle.dxf.dimexe = 1.0    # extension line extension
dimstyle.dxf.dimexo = 0.5    # extension line offset
dimstyle.dxf.dimgap = 0.5    # gap between text and dim line
```

### 2.6 HATCH (Filled Regions)

```python
doc = ezdxf.new("R2000")
msp = doc.modelspace()

# Solid fill hatch
hatch = msp.add_hatch(color=2)

# Define boundary using polyline path
hatch.paths.add_polyline_path(
    [(0, 0), (10, 0), (10, 10), (0, 10)],
    is_closed=True
)

# Polyline path with bulge (curved corners)
hatch2 = msp.add_hatch(color=4)
hatch2.paths.add_polyline_path(
    [(0, 0, 1), (10, 0), (10, 10, -0.5), (0, 10)],
    is_closed=True
)
```

### 2.7 Blocks and INSERT

```python
doc = ezdxf.new("R2010")

# Define a block (reusable symbol)
block = doc.blocks.new("FLAG")
block.add_line((-1, -1), (1, 1), dxfattribs={"color": 1})
block.add_line((-1, 1), (1, -1), dxfattribs={"color": 1})
block.add_circle((0, 0), radius=0.4, dxfattribs={"color": 2})

# Add attribute definitions (parametric text fields)
block.add_attdef(
    tag="NAME",
    insert=(0.5, -0.5),
    dxfattribs={"height": 0.5, "color": 3, "prompt": "Enter name:"}
)
block.add_attdef(
    tag="NUMBER",
    insert=(0.5, -1.0),
    dxfattribs={"height": 0.3, "color": 4}
)

# Insert block into modelspace
msp = doc.modelspace()
block_ref = msp.add_blockref(
    "FLAG",
    insert=(5, 5),
    dxfattribs={"rotation": 45, "xscale": 1.5, "yscale": 1.5, "layer": "Symbols"}
)

# Set attribute values
block_ref.add_auto_attribs({"NAME": "Point 1", "NUMBER": "001"})

doc.saveas("blocks_example.dxf")
```

### 2.8 SPLINE

```python
doc = ezdxf.new("R2000")
msp = doc.modelspace()

# Spline from fit points (library auto-generates control points)
fit_points = [(0, 0, 0), (750, 500, 0), (1750, 500, 0), (2250, 1250, 0)]
spline = msp.add_spline(fit_points)

# Spline from control points (more precise control)
msp.add_spline_control_frame(
    fit_points,
    method='chord',   # 'uniform', 'chord', or 'centripetal'
    dxfattribs={'color': 3}
)
```

### 2.9 R12 Fast Stream Writer (High Performance)

For generating large DXF files with thousands of entities:

```python
from ezdxf.addons import r12writer

with r12writer("fast_output.dxf") as dxf:
    dxf.add_line((0, 0), (10, 10), layer="Lines", color=1)
    dxf.add_circle((5, 5), radius=2.5, layer="Circles", color=2)
    dxf.add_arc((0, 0), radius=5, start_angle=0, end_angle=90, color=3)
    dxf.add_point((7, 7), layer="Points")
    dxf.add_solid([(0, 0), (1, 0), (1, 1), (0, 1)], layer="Solids", color=4)
    dxf.add_polyline([(0, 0), (5, 0), (5, 5), (0, 5)], close=True, layer="Polylines")
    dxf.add_text("Fast R12 Writer", insert=(0, 10), height=0.5, layer="Text")

    # Generate 10,000 entities with minimal memory
    for row in range(100):
        for col in range(100):
            x, y = col * 10, row * 10
            dxf.add_circle((x, y), radius=2)
```

### 2.10 Paper Space, Layouts, and Viewports

```python
doc = ezdxf.new("R2010")
msp = doc.modelspace()

# Draw in model space
msp.add_line((0, 0), (100, 0))
msp.add_circle((50, 50), radius=25)

# Create a paper space layout
layout = doc.layouts.new("A3 Sheet")

# Add a viewport to the paper space
# The viewport shows a window into model space
layout.add_viewport(
    center=(150, 100),       # center of viewport on paper
    size=(200, 150),         # size of viewport on paper
    view_center_point=(50, 25),  # what point in model space to look at
    view_height=80,          # how much of model space to show
)
```

---

## 3. Server-Side Conversion Pipeline

### 3.1 ODA File Converter (DXF to DWG)

**The ODA File Converter** is the industry-standard free tool for converting between DXF and DWG formats. It is published by the **Open Design Alliance** (ODA).

- **Website:** https://www.opendesign.com/guestfiles/oda_file_converter
- **Platforms:** Windows, macOS, Linux (32/64-bit RPM, DEB, AppImage)
- **License:** Free for end users (proprietary)
- **CLI + GUI:** Both interfaces available

**ezdxf Integration (recommended approach):**

```python
from ezdxf.addons import odafc

# Check if ODA File Converter is installed
if odafc.is_installed():
    print("ODA File Converter is available")

# Read a DWG file
doc = odafc.readfile('input.dwg')
print(f'Loaded as DXF version: {doc.dxfversion}')

# Export as DWG
odafc.export_dwg(doc, 'output.dwg', version='R2018')

# Direct conversion
odafc.convert("input.dxf", "output.dwg", version="R2018", audit=True)
```

**Configuration (ezdxf config file):**
```ini
[odafc-addon]
win_exec_path = "C:\Program Files\ODA\ODAFileConverter\ODAFileConverter.exe"
unix_exec_path = "/usr/bin/ODAFileConverter"
```

**Supported Version Strings:**

| ODAFC | ezdxf | AutoCAD Version |
|-------|-------|-----------------|
| ACAD12 | R12 | AC1009 |
| ACAD14 | R14 | AC1014 |
| ACAD2000 | R2000 | AC1015 |
| ACAD2004 | R2004 | AC1018 |
| ACAD2007 | R2007 | AC1021 |
| ACAD2010 | R2010 | AC1024 |
| ACAD2013 | R2013 | AC1027 |
| ACAD2018 | R2018 | AC1032 |

**Server Deployment (Docker example):**
```dockerfile
FROM python:3.11-slim
RUN pip install ezdxf
# Install ODA File Converter
# Download from ODA website and install
COPY ODAFileConverter /usr/local/bin/
ENV PATH="/usr/local/bin:$PATH"
```

**Windows GUI Suppression:** On Windows, the ODA converter GUI is automatically suppressed by ezdxf.
**Linux:** May need `xvfb` package installed to suppress GUI.

### 3.2 LibreDWG (Open Source Alternative)

- **Website:** https://www.gnu.org/software/libredwg/
- **Repository:** https://github.com/LibreDWG/libredwg
- **License:** GPLv3+ (important: copyleft license)
- **Language:** C library with Python bindings
- **Status:** Beta — decoder (reader) done, writer good for R1.1-R2000

**Command-Line Tools:**
- `dwg2dxf` — Converts DWG to DXF
- `dxf2dwg` — Converts DXF to DWG
- `dwgread` — Read and dump DWG content
- `dwgwrite` — Write DWG files
- `dwg2SVG` — Convert DWG to SVG
- `dwg2ps` — Convert DWG to PostScript
- `dwggrep` — Search for text in DWG files
- `dwglayer` — List layers in DWG files

**Pros:**
- Fully open source (no proprietary dependencies)
- Supports reading all DWG versions
- WebAssembly build available (libredwg-web) for browser-side DWG parsing

**Cons:**
- GPLv3 license (copyleft — affects distribution)
- Writer only reliable for R1.1–R2000 (older versions)
- More complex to integrate than ODA
- Less reliable output for modern DWG versions

**Verdict:** Use ODA File Converter for production DWG export. LibreDWG is best for DWG reading/parsing or when GPLv3 is acceptable.

### 3.3 ODA SDK Command-Line Samples

The ODA Drawings SDK (commercial license) includes additional CLI tools:
- **OdCopyEx** — Load .dwg/.dxf, save as .dwg/.dxf (any version)
- **OdDwfExport** — Export to .dwf
- **OdColladaExport** — Export to Collada
- **OdPdfExport** — Export to .pdf
- **OdSvgExport** — Export to .svg

These are part of the commercial SDK, not the free ODA File Converter.

### 3.4 AutoCAD Design Automation API (Cloud)

Autodesk offers a cloud API for DWG manipulation:
- Part of Autodesk Platform Services (formerly Forge)
- Can run AutoLISP/ObjectARX in the cloud
- Pay-per-use pricing
- Best for: When you need true AutoCAD compatibility guarantees
- Not suitable for: High-volume, low-latency conversions

---

## 4. SVG to DXF Conversion

### 4.1 Inkscape CLI

**Command-line conversion:**
```bash
# Inkscape 1.0+ syntax
inkscape input.svg --export-filename=output.dxf --export-type=dxf

# Older Inkscape syntax
inkscape input.svg -o output.dxf

# Batch conversion
for f in *.svg; do
    inkscape "$f" --export-filename="${f%.svg}.dxf" --export-type=dxf
done
```

**Limitations:**
- Converts SVG paths to DXF polylines (approximated)
- Loses semantic information (a circle becomes a polyline approximation)
- Bezier curves are flattened to line segments
- No dimension entity creation
- Quality depends on Inkscape's DXF export plugin

### 4.2 svg2dxf (Python/Shell)

**Repository:** https://github.com/Zigazou/svg2dxf

**Dependencies:** Inkscape + pstoedit (pipe-based, no temp files)

**Usage:**
```bash
svg2dxf input.svg output.dxf
```

**SVG Preparation Requirements:**
1. Use only one layer
2. Ungroup everything
3. Convert strokes to paths (`Path > Stroke to Path`)
4. Convert shapes to paths (`Path > Object to Path`)
5. Union all objects

**Verdict:** Not suitable for engineering drawings. Best for simple shape outlines for CNC/laser cutting.

### 4.3 ezdxf Path Module (Best Approach)

ezdxf has a built-in `Path` module that can convert between geometric paths and DXF entities:

```python
from ezdxf.path import Path, make_path
from ezdxf.math import Vec2

# Create a path (similar to SVG path)
p = Path(start=Vec2(0, 0))
p.line_to(Vec2(100, 0))
p.curve4_to(Vec2(200, 100), Vec2(150, 0), Vec2(200, 50))  # cubic bezier
p.line_to(Vec2(200, 200))
p.close()

# Convert path to DXF entities
# The path module can render to LWPOLYLINE, SPLINE, etc.
```

### 4.4 SVG Path to DXF Entity Mapping

| SVG Command | SVG Meaning | DXF Entity | Notes |
|-------------|-------------|------------|-------|
| `M x y` | Move to | (start point) | Sets current position |
| `L x y` | Line to | LINE or LWPOLYLINE vertex | Direct mapping |
| `H x` | Horizontal line | LINE | y unchanged |
| `V y` | Vertical line | LINE | x unchanged |
| `C x1 y1 x2 y2 x y` | Cubic bezier | SPLINE (degree 3) | Control points map directly |
| `Q x1 y1 x y` | Quadratic bezier | SPLINE (degree 2) | Elevate to cubic for DXF |
| `A rx ry rot large sweep x y` | Elliptical arc | ARC or ELLIPSE | Complex decomposition needed |
| `Z` | Close path | Close LWPOLYLINE | Sets `close=True` |

---

## 5. DXF Entity Mapping (Canvas Shape to DXF)

### Complete Mapping Table

| Canvas Shape | DXF Entity | ezdxf Method | Notes |
|-------------|------------|--------------|-------|
| **Rectangle** | LWPOLYLINE (closed) | `msp.add_lwpolyline(pts, close=True)` | 4 vertices, closed |
| **Rounded Rectangle** | LWPOLYLINE with bulge | `msp.add_lwpolyline(pts, format='xyseb')` | Bulge at corners for arcs |
| **Circle** | CIRCLE | `msp.add_circle(center, radius)` | Direct mapping |
| **Ellipse** | ELLIPSE | `msp.add_ellipse(center, major_axis, ratio)` | Major axis + ratio |
| **Line** | LINE | `msp.add_line(start, end)` | Direct mapping |
| **Polyline** | LWPOLYLINE | `msp.add_lwpolyline(points)` | List of vertices |
| **Arc** | ARC | `msp.add_arc(center, radius, start, end)` | Angles in degrees |
| **Text** | TEXT or MTEXT | `msp.add_text()` / `msp.add_mtext()` | MTEXT for multi-line |
| **Dimension** | DIMENSION | `msp.add_linear_dim()` | Must call `.render()` |
| **Group** | INSERT (block ref) | `msp.add_blockref(name, insert)` | Define block first |
| **Bezier Curve** | SPLINE | `msp.add_spline(fit_points)` | Or `add_spline_control_frame()` |
| **Quadratic Bezier** | SPLINE (degree 2→3) | Elevate to cubic, then SPLINE | Convert Q to C bezier first |
| **Polygon** | LWPOLYLINE (closed) | `msp.add_lwpolyline(pts, close=True)` | N vertices, closed |
| **Filled Shape** | HATCH | `msp.add_hatch()` + boundary path | Solid or pattern fill |
| **Image** | IMAGE | Raster image reference | Not commonly used in CAD |
| **Arrow** | LINE + LWPOLYLINE | Arrowhead as small triangle | Or use LEADER entity |
| **Wall (thick line)** | Two parallel LWPOLYLINEs | Or MLINE (multi-line) | Offset by wall thickness |
| **Door swing** | ARC + LINE | Quarter-circle arc | Standard CAD convention |
| **Window** | LINE entities | Parallel lines with gaps | Standard CAD convention |

### Code Examples for Key Mappings

**Rectangle to LWPOLYLINE:**
```python
def canvas_rect_to_dxf(msp, x, y, width, height, layer="0", rotation=0):
    """Convert a canvas rectangle to a DXF LWPOLYLINE."""
    import math
    cos_r = math.cos(math.radians(rotation))
    sin_r = math.sin(math.radians(rotation))

    # Rectangle corners (before rotation)
    corners = [
        (x, y),
        (x + width, y),
        (x + width, y + height),
        (x, y + height),
    ]

    if rotation != 0:
        cx, cy = x + width/2, y + height/2
        rotated = []
        for px, py in corners:
            dx, dy = px - cx, py - cy
            rx = cx + dx * cos_r - dy * sin_r
            ry = cy + dx * sin_r + dy * cos_r
            rotated.append((rx, ry))
        corners = rotated

    msp.add_lwpolyline(corners, close=True, dxfattribs={"layer": layer})
```

**Circle to CIRCLE:**
```python
def canvas_circle_to_dxf(msp, cx, cy, radius, layer="0"):
    """Convert a canvas circle to a DXF CIRCLE."""
    msp.add_circle((cx, cy), radius, dxfattribs={"layer": layer})
```

**Bezier Curve to SPLINE:**
```python
def canvas_bezier_to_dxf(msp, control_points, layer="0"):
    """Convert a canvas cubic bezier curve to a DXF SPLINE.

    control_points: list of (x, y) tuples — [start, cp1, cp2, end]
    For a cubic bezier, we can use these as spline control points.
    """
    # For a single cubic bezier segment:
    # DXF SPLINE with degree=3, 4 control points, knots=[0,0,0,0,1,1,1,1]
    from ezdxf.math import BSpline

    pts_3d = [(x, y, 0) for x, y in control_points]

    spline = msp.add_spline(dxfattribs={"layer": layer})
    spline.set_control_points(pts_3d)
    spline.dxf.degree = 3
    spline.knots = [0, 0, 0, 0, 1, 1, 1, 1]  # clamped knot vector
```

**Dimension to DIMENSION:**
```python
def canvas_dimension_to_dxf(msp, p1, p2, offset_distance, layer="Dimensions"):
    """Convert a canvas dimension annotation to a DXF DIMENSION."""
    import math

    # Calculate dimension line position (offset from measurement line)
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.sqrt(dx*dx + dy*dy)

    # Normal vector for offset
    nx, ny = -dy/length, dx/length
    base_x = (p1[0] + p2[0])/2 + nx * offset_distance
    base_y = (p1[1] + p2[1])/2 + ny * offset_distance

    dim = msp.add_linear_dim(
        base=(base_x, base_y),
        p1=p1,
        p2=p2,
        dimstyle="EZDXF",
        dxfattribs={"layer": layer}
    )
    dim.render()
```

**Group to Block INSERT:**
```python
def canvas_group_to_dxf(doc, msp, group_name, shapes, insert_point, rotation=0, scale=1.0):
    """Convert a canvas group to a DXF Block + INSERT."""
    # Create block definition
    block = doc.blocks.new(group_name)

    # Add shapes to block (relative to block origin)
    for shape in shapes:
        if shape['type'] == 'line':
            block.add_line(shape['start'], shape['end'])
        elif shape['type'] == 'circle':
            block.add_circle(shape['center'], shape['radius'])
        elif shape['type'] == 'text':
            block.add_text(shape['text'], dxfattribs={
                "insert": shape['position'],
                "height": shape['height']
            })

    # Insert block into model space
    msp.add_blockref(
        group_name,
        insert=insert_point,
        dxfattribs={
            "rotation": rotation,
            "xscale": scale,
            "yscale": scale,
            "layer": "Groups"
        }
    )
```

---

## 6. Recommended Architecture

### 6.1 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  Web Canvas (Browser)                │
│  React/Canvas/SVG drawing application                │
│  - User draws shapes, dimensions, annotations        │
│  - Internal representation: JSON scene graph          │
└──────────────────────┬──────────────────────────────┘
                       │ POST /api/export/dxf
                       │ POST /api/export/dwg
                       │ Body: { shapes: [...], options: {...} }
                       ▼
┌─────────────────────────────────────────────────────┐
│              API Server (Express/FastAPI)             │
│  - Receives JSON scene graph                         │
│  - Validates shapes and options                      │
│  - Calls Python conversion service                   │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│           Python DXF Service (ezdxf)                 │
│                                                      │
│  1. Parse JSON scene graph                           │
│  2. Create ezdxf Document                            │
│  3. Set up layers, styles, dimension styles          │
│  4. Map each canvas shape → DXF entity               │
│  5. Add paper space layout (optional)                │
│  6. Save as .dxf                                     │
│  7. If DWG requested:                                │
│     - Use odafc.export_dwg() → .dwg                  │
│  8. Return file to API server                        │
└─────────────────────────────────────────────────────┘
```

### 6.2 JSON Scene Graph Schema (Input)

```json
{
  "version": "1.0",
  "units": "millimeters",
  "paperSize": "A3",
  "scale": "1:100",
  "layers": [
    { "name": "Walls", "color": 1, "lineType": "CONTINUOUS", "visible": true },
    { "name": "Dimensions", "color": 3, "lineType": "CONTINUOUS", "visible": true },
    { "name": "Text", "color": 7, "lineType": "CONTINUOUS", "visible": true }
  ],
  "shapes": [
    {
      "id": "rect-1",
      "type": "rectangle",
      "x": 0, "y": 0,
      "width": 5000, "height": 3000,
      "rotation": 0,
      "layer": "Walls",
      "lineWidth": 0.35
    },
    {
      "id": "circle-1",
      "type": "circle",
      "cx": 2500, "cy": 1500,
      "radius": 500,
      "layer": "Walls"
    },
    {
      "id": "line-1",
      "type": "line",
      "x1": 0, "y1": 0,
      "x2": 5000, "y2": 0,
      "layer": "Walls"
    },
    {
      "id": "dim-1",
      "type": "dimension",
      "dimensionType": "linear",
      "p1": [0, 0],
      "p2": [5000, 0],
      "offset": 500,
      "layer": "Dimensions"
    },
    {
      "id": "text-1",
      "type": "text",
      "content": "Living Room",
      "x": 2500, "y": 1500,
      "height": 200,
      "rotation": 0,
      "alignment": "MIDDLE_CENTER",
      "layer": "Text"
    },
    {
      "id": "bezier-1",
      "type": "bezier",
      "points": [[0,0], [100,200], [300,200], [400,0]],
      "layer": "Walls"
    },
    {
      "id": "group-1",
      "type": "group",
      "name": "Door-900mm",
      "insertPoint": [1000, 0],
      "rotation": 0,
      "scale": 1.0,
      "children": [
        { "type": "line", "x1": 0, "y1": 0, "x2": 900, "y2": 0 },
        { "type": "arc", "cx": 0, "cy": 0, "radius": 900, "startAngle": 0, "endAngle": 90 }
      ]
    }
  ],
  "titleBlock": {
    "projectName": "My Project",
    "drawingNumber": "A-101",
    "drawnBy": "Omar",
    "date": "2026-02-12",
    "scale": "1:100"
  }
}
```

### 6.3 Technology Stack Recommendation

| Component | Technology | Reason |
|-----------|-----------|--------|
| **DXF Generation** | Python ezdxf | Most complete DXF library, 91/100 score, 2113 snippets |
| **DWG Conversion** | ODA File Converter via ezdxf | Industry standard, free, reliable |
| **Client-side Preview DXF** | `dxf-writer` (JS) | Quick DXF preview before server round-trip |
| **API Transport** | JSON scene graph | Language-agnostic, easy to serialize canvas state |
| **API Server** | Express (Node) or FastAPI (Python) | If Python: FastAPI eliminates need for bridge |
| **Coordinate Transform** | Y-axis flip in service | Canvas Y-down → DXF Y-up |

### 6.4 Client-Side Fallback (Simple DXF Only)

For simple exports without DIMENSION/HATCH/blocks, use `dxf-writer` directly in the browser:

```typescript
import Drawing from 'dxf-writer';

export function exportSimpleDxf(shapes: CanvasShape[]): Blob {
  const d = new Drawing();
  d.setUnits('Millimeters');

  // Add layers
  d.addLayer('Walls', Drawing.ACI.RED, 'CONTINUOUS');
  d.addLayer('Text', Drawing.ACI.WHITE, 'CONTINUOUS');

  for (const shape of shapes) {
    d.setActiveLayer(shape.layer || '0');

    switch (shape.type) {
      case 'line':
        d.drawLine(shape.x1, shape.y1, shape.x2, shape.y2);
        break;
      case 'circle':
        d.drawCircle(shape.cx, shape.cy, shape.radius);
        break;
      case 'rectangle':
        d.drawPolyline([
          [shape.x, shape.y],
          [shape.x + shape.width, shape.y],
          [shape.x + shape.width, shape.y + shape.height],
          [shape.x, shape.y + shape.height],
          [shape.x, shape.y],  // close
        ]);
        break;
      case 'arc':
        d.drawArc(shape.cx, shape.cy, shape.radius, shape.startAngle, shape.endAngle);
        break;
      case 'text':
        d.drawText(shape.x, shape.y, shape.height, shape.rotation || 0, shape.content);
        break;
    }
  }

  return new Blob([d.toDxfString()], { type: 'application/dxf' });
}
```

### 6.5 Coordinate System Considerations

```
Canvas (SVG/HTML):          DXF/CAD:
┌──────────► X              Y ▲
│                              │
│                              │
▼ Y                            └──────────► X

Transformation:
dxf_x = canvas_x
dxf_y = canvas_height - canvas_y   (Y-axis flip)

For rotation:
dxf_angle = -canvas_angle  (opposite rotation direction)

For scale:
If canvas uses pixels and DXF uses mm:
dxf_coord = canvas_coord * (scale_factor)
e.g., 1 pixel = 1mm at 1:1, or 1 pixel = 10mm at 1:10
```

### 6.6 Dependencies Summary

**Python (server-side):**
```
ezdxf>=1.4.0          # DXF creation/manipulation
# ODA File Converter   # System install for DWG export (not pip)
```

**JavaScript (client-side — optional):**
```
dxf-writer@^1.18.4    # Simple client-side DXF (fallback)
# OR
@tarikjabiri/dxf@^2.8.9  # If blocks/hatches needed client-side
```

**System dependencies (server):**
```
# For DWG export:
ODA File Converter (free download from opendesign.com)
# OR for open-source DWG:
LibreDWG (GPLv3 — includes dwg2dxf, dxf2dwg CLI tools)
```

---

## Summary of Findings

1. **ezdxf (Python) is the clear winner** for DXF generation. It supports every DXF entity type needed (LINE, CIRCLE, ARC, LWPOLYLINE, SPLINE, TEXT, MTEXT, DIMENSION, HATCH, INSERT/blocks), has excellent documentation (91/100 score, 2113 code snippets), and integrates directly with ODA File Converter for DWG export.

2. **No JavaScript library supports DIMENSION entities.** This is the single biggest gap. For engineering drawings, dimension annotations are essential, and all three JS libraries (dxf-writer, @tarikjabiri/dxf, Maker.js) lack this capability.

3. **ODA File Converter** is the recommended path for DXF-to-DWG conversion. It's free, cross-platform, and ezdxf has a built-in addon (`ezdxf.addons.odafc`) that wraps its CLI. LibreDWG is an open-source alternative but its writer only supports DWG versions up to R2000.

4. **SVG-to-DXF conversion is lossy** — semantic information (circles become polylines, dimensions are just lines) is lost. The recommended approach is to export the canvas scene graph as JSON and reconstruct proper DXF entities server-side with ezdxf, rather than converting an intermediate SVG.

5. **Client-side DXF export** using `dxf-writer` can serve as a quick-export fallback for simple drawings (lines, circles, arcs, text only), avoiding a server round-trip when dimensions and hatches are not needed.

6. **The optimal architecture** is: Canvas JSON scene graph -> Python API endpoint -> ezdxf generates DXF -> ODA converts to DWG if needed -> return file to client.
