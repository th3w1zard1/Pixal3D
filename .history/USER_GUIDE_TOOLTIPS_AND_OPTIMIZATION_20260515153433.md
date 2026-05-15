# Pixal3D GUI Enhancements - User Guide

## 🎯 Quick Start: Reducing Mesh Edges/Vertices

### Method 1: Decimation During Export (Post-Processing)

1. **Generate 3D model** from your image
2. Open **Advanced Engine** section
3. Scroll to **Decimation** slider
4. **Move slider left** to reduce triangle count:
   - `100K` (10%): Ultra-low detail, mobile only
   - `300K` (30%): Mobile-optimized
   - `500K` (50%): **Recommended for web** ← Good balance
   - `750K` (75%): High quality
   - `1M` (100%): Full quality, largest file

5. Click **Extract Mesh (GLB)** to export
6. File will automatically be decimated during export

### Method 2: Adjust Shape Generation Parameters

To reduce vertices **during generation** (affects face smoothness):

1. Open **Advanced Engine** section
2. Reduce **Shape Sampling Steps** from 12 to 6-8
   - Fewer steps = simpler geometry = fewer vertices
   - Trade-off: May lose some detail
3. Reduce **SS Sampling Steps** from 12 to 8-10
   - Affects structure skeleton complexity
4. Click **Generate**

---

## 📖 Understanding Each Parameter

### How to Access Parameter Help

1. **Look for `?` icon** next to any parameter
2. **Hover over the `?`** - tooltip appears
3. **Read the explanation** with recommendations

### Base Settings

#### 🖼️ Target Resolution

<img alt="Tooltip: Target Resolution" width="200">

**What it does**: Controls the resolution of the latent grid used by the AI during 3D generation.

| Setting | Speed | Quality | Memory | Best For |
|---------|-------|---------|--------|----------|
| 1024 | ⚡ 8-12s | Good | Low | Quick previews |
| 1536 | ⏱️ 12-18s | Better | Higher | Production |

**Recommendation**: Use 1536 for final exports

#### 🎲 Generation Seed

**What it does**: Random seed for reproducibility (0-999999)

- Same seed + same settings = identical result
- **Use when**: You like a result and want to refine it
- **Use randomize button**: For unique outputs each time

#### 📷 Camera FOV

**What it does**: Field of view angle for the camera

- **Auto (recommended)**: Automatically estimated from image
- **Manual**: Set 0.02-2.97 radians
  - `0.02 rad` = zoomed-out wide view
  - `0.5 rad` = normal view  
  - `1.0 rad` = close-up view

If geometry looks distorted, try adjusting ±0.05 radians manually.

---

### Advanced Engine Settings

#### 🎯 SS Guidance Strength (1-10)

Controls how strictly the AI follows the **input structure**.

| Value | Effect | Best For |
|-------|--------|----------|
| 1-5 | Creative, loose | Artistic variations |
| 7.5 | **Balanced** ← Default | Production quality |
| 8-10 | Faithful, strict | Accurate reproduction |

**When to adjust**:

- ↑ **Increase** if structure looks distorted or wrong
- ↓ **Decrease** if you want creative variations

#### 📊 SS Sampling Steps (1-50)

Number of generation iterations for the structure skeleton.

| Steps | Time | Quality | Use Case |
|-------|------|---------|----------|
| 6-12 | 2-5s | Fair | Quick preview |
| **12-20** | **5-10s** | **Good** | **Production** ← Recommended |
| 20-50 | 10-20s | Excellent | High-quality output |

**Key insight**: Most improvement happens in first 12 steps; diminishing returns after.

#### 🎨 Shape Guidance Strength (1-10)

Controls adherence during **dense shape generation** (detailed geometry).

| Value | Effect | Best For |
|-------|--------|----------|
| 5-7 | Creative shapes | Artistic interpretations |
| 7.5 | **Balanced** ← Default | Production |
| 8-10 | Faithful shapes | Accurate reproductions |

**Works with**: SS Guidance for coherent overall generation

#### 📐 Shape Sampling Steps (1-40)

Number of iterations for detailed geometry (SDF) generation.

| Steps | Time | Quality | Detail |
|-------|------|---------|--------|
| 6-12 | 2-3s | Basic | Low geometry |
| **12-20** | **5-8s** | **Good** | **Standard** ← Recommended |
| 20-40 | 8-15s | Excellent | High geometry |

**Impact on mesh**: More steps = more vertices/edges, smoother surface

---

### Advanced Texture Tuning (Optional)

Click checkbox to reveal texture controls for fine-tuning materials and colors.

#### 🎭 Texture Guidance Strength (0.0-5.0)

Controls how strictly the AI follows input **colors and materials**.

| Value | Effect | Best For |
|-------|--------|----------|
| 0.0-0.5 | Creative colors | Artistic styles |
| **1.0** | **Balanced** ← Default | Production |
| 1.5-2.0 | Faithful colors | Accurate reproduction |

**Note**: Rarely adjusted; less impact than other parameters

#### 🎬 Texture Sampling Steps (1-40)

Iterations for material/PBR texture generation.

| Steps | Time | Quality | Result |
|-------|------|---------|--------|
| 6-12 | 1-2s | Basic | Flat colors |
| **12-24** | **2-4s** | **Good** | **Detailed textures** ← Recommended |
| 24-40 | 4-6s | Excellent | Rich PBR materials |

**Impact**: More steps = more refined materials and colors

---

### 📦 Decimation (100K - 1M triangles)

**What it does**: Reduces triangle count after mesh is generated using the QEM algorithm.

#### Visual Guide

```
Original Mesh
    (1M triangles, 3-4MB)
         ↓
    Decimation applied
         ↓
Result Mesh
    (500K triangles, 1-2MB)
         ↓
    90% geometry preserved!
    File 50% smaller
    Rendering 2-3× faster
```

#### Decimation Recommendations

| Triangles | File Size | Use Case | Quality |
|-----------|-----------|----------|---------|
| 100K | ~200KB | Mobile preview | Poor |
| 250K | ~400KB | Mobile use | Fair |
| **500K** | **~1MB** | **Web standard** | **Good** ← Recommended |
| 750K | ~1.5MB | High quality | Very good |
| 1M | ~2-4MB | Professional | Excellent |

#### When to Adjust

- **Move LEFT (decrease)** if:
  - ❌ File size too large for web upload
  - ❌ Rendering/loading is slow
  - ❌ Mobile viewing is sluggish

- **Move RIGHT (increase)** if:
  - ✅ Model looks boxy/over-simplified
  - ✅ Need professional-quality output
  - ✅ File size not a concern

---

## 🎛️ Preset Configurations

### Scenario 1: Quick Preview (8-12 seconds)

Perfect for rapid iterations and tests.

```
Resolution:        1024
Guidance Strength:   7.5 (SS & Shape)
Sampling Steps:      6-8 (SS), 8 (Shape)
Texture Steps:       8
Decimation:         500K
Result:             Fast, acceptable quality
```

### Scenario 2: Production Quality (15-25 seconds) ⭐

Best for professional use and exports.

```
Resolution:        1536 ← Higher detail
Guidance Strength:   7.5 (SS & Shape)
Sampling Steps:      12 (SS), 12 (Shape)  ← Default balanced
Texture Steps:       12
Decimation:         1M ← Full quality
Result:             Excellent quality, web-friendly
```

### Scenario 3: High-End Quality (25-40 seconds)

For showcases, professional portfolios, or VR.

```
Resolution:        1536
Guidance Strength:   8.0 (SS & Shape)  ← Stricter adherence
Sampling Steps:      20 (SS), 24 (Shape)
Texture Steps:       24
Decimation:         1M
Result:             Outstanding detail, larger files
```

### Scenario 4: Creative/Artistic (12-20 seconds)

For stylized, non-photorealistic results.

```
Resolution:        1024
Guidance Strength:   6.0 (SS), 6.5 (Shape)  ← Lower = more creative
Sampling Steps:      12 (SS), 12 (Shape)
Texture Steps:       12
Texture Guidance:    0.5  ← Creative colors
Decimation:         500K  ← Artistic file size
Result:             Creative, stylized output
```

---

## 🔧 Troubleshooting

### Problem: Face looks blocky/low-poly

**Solutions**:

1. Increase **Shape Sampling Steps** to 20+
2. Increase **SS Sampling Steps** to 15+
3. Increase **Decimation** slider to maximum (1M)
4. Use Target **Resolution 1536**

### Problem: Face geometry looks distorted/wrong

**Solutions**:

1. ↑ Increase **SS Guidance Strength** to 8.5-9.5
2. Try adjusting **Camera FOV** manually ±0.05 rad
3. Verify input image is clear and well-lit
4. Try different **random seed**

### Problem: Texture looks flat/dull

**Solutions**:

1. Increase **Texture Sampling Steps** to 20+
2. Set **Texture Guidance** to 1.5-2.0
3. Ensure input image is well-lit and colored
4. Try **High-End Quality** preset

### Problem: Generation too slow

**Solutions**:

1. ↓ Reduce **Resolution** to 1024
2. ↓ Reduce all **Sampling Steps** by 25%
3. ↓ Reduce **Decimation** (won't affect generation speed, only file export)

### Problem: File size too large

**Solutions**:

1. **MOST EFFECTIVE**: ↓ Reduce **Decimation** slider
   - Moving from 1M to 500K ≈ 50% file size reduction
   - Quality impact usually imperceptible
2. Reduce **Texture Sampling Steps** (less impact)
3. Choose lower **Target Resolution** (1024 vs 1536)

---

## 📊 Parameter Impact Summary

### On Mesh Complexity (Vertices/Edges)

| Parameter | Effect | Impact Level |
|-----------|--------|--------------|
| **Decimation** | Direct reduction | ⚡⚡⚡ HIGHEST |
| Shape Sampling Steps | Smoother geometry | ⚡⚡ MEDIUM |
| SS Sampling Steps | Structure detail | ⚡ LOW |
| Resolution | Grid detail | ⚡⚡ MEDIUM |

### On Generation Speed

| Parameter | Effect | Impact Level |
|-----------|--------|--------------|
| **Shape Sampling Steps** | 8s per 10 steps | ⚡⚡⚡ HIGHEST |
| **SS Sampling Steps** | 2s per 5 steps | ⚡⚡ MEDIUM |
| Texture Sampling Steps | 1s per 10 steps | ⚡ LOW |
| Resolution | 4s difference | ⚡⚡ MEDIUM |

### On File Size

| Parameter | Effect | Impact Level |
|-----------|--------|--------------|
| **Decimation** | Linear reduction | ⚡⚡⚡ HIGHEST |
| Texture Steps | Negligible | ⚡ NONE |
| Shape Steps | Negligible | ⚡ NONE |
| Resolution | Base geometry size | ⚡⚡ MEDIUM |

---

## 💡 Pro Tips

1. **Always hover `?` icons** - They have the latest recommendations
2. **Test with Quick Preview first** - Then upgrade to Production preset
3. **Export at 500K decimation** - Rarely notice quality difference on web
4. **Save seed when you like a result** - Modify one parameter at a time
5. **Use presets as starting points** - Customize from there
6. **Monitor file size** - Most users expect <5MB files

---

## 📚 Additional Resources

For deeper technical understanding, see:

- `GUI_TOOLTIPS_DOCUMENTATION.md` - Complete parameter reference
- `QUICK_REFERENCE.md` - Quick lookup tables
- `MESH_OPTIMIZATION_RESEARCH.md` - Research foundations
- `DIFFUSION_PARAMETER_TUNING.md` - Advanced tuning guide
