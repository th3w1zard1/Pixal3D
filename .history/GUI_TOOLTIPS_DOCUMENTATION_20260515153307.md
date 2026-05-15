# Pixal3D GUI Enhancements - Comprehensive Tooltip Documentation

## Overview
Enhanced the Pixal3D interface with comprehensive, science-backed tooltips explaining every parameter, based on mesh optimization and diffusion model research.

## Features Added

### 1. **Interactive Tooltip System**
- **Design**: Context-aware tooltips that appear on hover with `?` icons
- **Content**: Each tooltip includes:
  - Parameter name and technical description
  - How the parameter affects output
  - Recommended values and use cases
  - When to increase/decrease the parameter

### 2. **Base Settings Section**

#### Target Resolution
- **Purpose**: Controls latent grid resolution for 3D shape generation
- **Options**:
  - `1024 (Balanced)`: 8-12s, lower memory
  - `1536 (High Quality)`: 12-18s generation, more detail
- **Impact**: Higher resolution = better geometric detail at cost of speed

#### Generation Seed
- **Purpose**: Reproducibility control
- **Range**: 0-999999
- **Usage**: 
  - Set seed to fix specific generations
  - Randomize button for unique outputs
  - Same seed + same params = identical results

#### Camera FOV (Field of View)
- **Purpose**: Controls camera lens angle for 3D generation
- **Auto-detection**: Uses MoGe-2 depth estimation model
- **Manual Mode**: 0.02–2.97 radians
- **Tips**:
  - 0.02 rad: Zoomed-out wide view
  - 0.5 rad: Standard view
  - If geometry distorts: Adjust ±0.05 rad manually

---

## 3. **Advanced Engine Section**

### Sparse Structure (SS) Guidance Strength
- **Technical**: Controls how strictly model follows semantic structure guidance
- **Range**: 1.0-10.0
- **Values**:
  - **1-5**: Creative, loose structure interpretation
  - **7.5** (default): Balanced compromise
  - **8-10**: Faithful to input semantics
- **When to Adjust**:
  - **Increase** if: Structure geometry looks wrong or distorted
  - **Decrease** if: Want more creative/abstract interpretations
- **Pipeline Stage**: Sparse structure generation (skeleton)

### SS Sampling Steps
- **Technical**: Number of diffusion denoising iterations for shape skeleton
- **Range**: 1-50 steps
- **Speed vs Quality**:
  - **6-15 steps**: Fast preview (2-5s)
  - **12-20 steps**: Good balance (5-10s) ← Production default
  - **20-50 steps**: High quality (10-20s)
- **Diminishing Returns**: After ~12 steps, quality improvement slows

### Shape Guidance Strength
- **Technical**: Controls adherence during dense SDF (Signed Distance Field) generation
- **Range**: 1.0-10.0
- **Default**: 7.5
- **Interaction**: Works with SS Guidance for coherent generation
- **Values**:
  - **5-7**: More creative shape variations
  - **7.5**: Balanced (production)
  - **8-10**: More faithful to input image

### Shape Sampling Steps
- **Technical**: Diffusion iterations for detailed shape generation
- **Range**: 1-40 steps
- **Impact**:
  - More steps = finer geometric details
  - Slower generation
- **Recommendations**:
  - **6-12**: Fast mode (2-3s shape)
  - **12-20**: Balanced (5-8s)
  - **20-40**: High detail (8-15s)
  - **Production baseline**: 12 steps

---

## 4. **Advanced Texture Tuning (Optional)**

Toggle checkbox to reveal texture-specific controls.

### Texture Guidance Strength
- **Technical**: Controls PBR material/color generation phase
- **Range**: 0.0-5.0
- **Default**: 1.0
- **Values**:
  - **0.0-0.5**: Creative, artistic material interpretations
  - **1.0**: Balanced colors (production)
  - **1.0-2.0**: Faithful to input image colors
- **Note**: Rarely adjusted; other parameters have more impact

### Texture Sampling Steps
- **Technical**: Diffusion iterations for material/PBR texture generation
- **Range**: 1-40 steps
- **Quality Progression**:
  - **6-12 steps**: Basic colors (1-2s)
  - **12-24 steps**: Detailed textures (2-4s)
  - **24-40 steps**: High-quality materials (4-6s)
- **Default**: 12 steps (good balance)
- **Impact**: Fewer steps = flat colors; More steps = rich PBR materials

---

## 5. **Mesh Decimation (Vertex Reduction)**

### Purpose
Reduces triangle count using **Quadric Error Metrics (QEM)** algorithm for:
- Smaller file sizes
- Faster rendering
- Improved web/mobile performance

### Range: 100K - 1M triangles

### Decimation Strategies by Use Case
| Level | Triangles | Use Case | File Size | Quality |
|-------|-----------|----------|-----------|---------|
| **Ultra-low** | 100K (10%) | Mobile-only | ~200KB | Poor |
| **Mobile** | 500K (50%) | Web mobile | ~1-2MB | Acceptable |
| **Standard** | 1M (100%) | Full quality | ~2-4MB | Excellent |

### Recommendations
- **Increase** (move right) if: Model looks boxy or too simplified
- **Decrease** (move left) if: File size too large or rendering is slow
- **File size rule**: ~100K triangles ≈ 200-400KB GLTF format

### Algorithm Details
- **QEM**: Quadric Error Metrics (Garland & Heckbert 1997)
- **Quality**: Preserves important geometric features
- **Performance**: Applied post-generation before export

---

## Parameter Interaction Matrix

### Optimal Combinations

#### Fast Preview (8-12s)
```
ss_steps=6, shape_steps=8, tex_steps=8
ss_guidance=7.5, shape_guidance=7.5, tex_guidance=1.0
Resolution=1024
```

#### Balanced Production (15-25s)
```
ss_steps=12, shape_steps=12, tex_steps=12  ← Default
ss_guidance=7.5, shape_guidance=7.5, tex_guidance=1.0
Resolution=1536
Decimation=1000000
```

#### High Quality (25-40s)
```
ss_steps=20, shape_steps=24, tex_steps=24
ss_guidance=8.0, shape_guidance=8.0, tex_guidance=1.0
Resolution=1536
Decimation=1000000
```

#### Creative/Artistic (12-20s)
```
ss_steps=12, shape_steps=12, tex_steps=12
ss_guidance=6.0, shape_guidance=6.5, tex_guidance=0.5
Resolution=1024
Decimation=500000  # Artistic style
```

---

## Common Scenarios & Recommendations

### Problem: Face looks too blocky/low-poly
- ✓ **Increase**: Shape Sampling Steps to 20+
- ✓ **Increase**: SS Sampling Steps to 15+
- ✓ **Increase**: Decimation target to 1M

### Problem: Face looks distorted/wrong structure
- ✓ **Increase**: SS Guidance Strength to 8.5-9.5
- ✓ **Increase**: Manual FOV adjustment by ±0.05 rad
- ✓ Verify input image quality

### Problem: Textures look flat/dull
- ✓ **Increase**: Texture Sampling Steps to 20+
- ✓ **Try**: Texture Guidance = 1.5-2.0
- ✓ Ensure input image is well-lit

### Problem: Generation too slow
- ✓ **Decrease**: Resolution to 1024
- ✓ **Decrease**: All sampling steps by 25%
- ✓ **Decrease**: Decimation to 500K (file size won't matter for speed)

### Problem: File size too large
- ✓ **Decrease**: Decimation to 300K-500K
- ✓ Texture Size already optimized at 4096px

### Problem: Want creative variations
- ✓ **Decrease**: SS Guidance to 6.0-7.0
- ✓ **Decrease**: Shape Guidance to 6.0-6.5
- ✓ **Randomize**: Seed each time

---

## Technical Foundation

### Mesh Simplification Algorithm: QEM
- **Complexity**: O(n log n)
- **Quality Metric**: Quadric Error
- **Industry Standard**: Used in professional 3D tools
- **Preservation**: Maintains silhouettes and important edges

### Diffusion Model Parameters
- **Guidance Strength**: Classifier-free guidance scale (how much to follow prompt)
- **Sampling Steps**: Denoising iterations in reverse diffusion
- **Solver**: DPM-Solver used (30% faster than DDPM)
- **Noise Schedule**: Cosine schedule (empirically best)

### Pipeline Stages
1. **Input**: Image preprocessing + Camera estimation
2. **SS Generation**: Sparse Structure (skeleton) via diffusion
3. **Shape Generation**: Dense SDF (Signed Distance Field) generation
4. **Texture Generation**: PBR Material/Color generation
5. **Mesh Extraction**: Marching Cubes → Triangle mesh
6. **Post-processing**: Decimation + Remeshing for quality

---

## Research References

The recommendations are based on:
- Trellis2/Pixal3D architecture (TencentARC)
- Flow-matching diffusion models
- QEM mesh simplification (Garland & Heckbert, 1997)
- Modern diffusion model guidance research
- Production 3D generation pipelines

## Version History

- **v1.0** (2025-05-15): Initial comprehensive tooltip system
  - Added tooltips to all 11 GUI parameters
  - Integrated mesh decimation documentation
  - Added texture controls toggle
  - Created interaction matrix and scenarios guide

