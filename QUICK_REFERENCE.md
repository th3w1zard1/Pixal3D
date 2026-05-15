# Quick Reference: Mesh Optimization & Diffusion Parameters

## TL;DR Summary

### Mesh Simplification in 3D Generation

**What it is**: Reducing triangle count while preserving visual quality
- Improves performance: 10-100× faster rendering
- Reduces file size: 70-95% reduction typical
- Trade-off: Visual quality vs performance

**Best algorithm**: Quadric Error Metrics (QEM)
- Industry standard (Garland & Heckbert 1997)
- Fast: O(n log n) complexity
- High quality: Preserves important geometry

**Typical strategy**:
```
Original mesh
    ↓
Apply 50-70% reduction
    ↓
Result: 90% geometry preserved, 2-3× faster
```

**Simplification ratios by use case**:
- 30-50% reduction: High-quality (professional use)
- 50-70% reduction: Standard (web/interactive)
- 80-90% reduction: Mobile/distant viewing
- 95%+ reduction: Thumbnails/LOD only

---

### Diffusion 3D Generation Parameters

**Two main parameters control quality**:

1. **Guidance Strength**: How strictly model follows prompt (7.5-15.0)
2. **Sampling Steps**: Number of denoising iterations (20-100)

| Use Case | Guidance | Steps | Time | Quality |
|----------|----------|-------|------|---------|
| Preview | 10.0 | 30 | 8s | Fair |
| **Production** | **12.0** | **50** | **20s** | **Excellent** ⭐ |
| High-quality | 12.5 | 75 | 30s | Outstanding |
| Creative | 8.5 | 50 | 20s | Very Good |

**Recommended baseline** (production quality):
```python
guidance_strength = 12.0      # Strong prompt adherence
sampling_steps = 50           # Balanced quality/speed
solver = "dpm_solver"         # Fast + accurate
temperature = 0.75           # Slightly deterministic
negative_prompt = "artifacts, low quality, distorted geometry"
```

**Quality curve**: Most improvement in first 50 steps; diminishing returns after.

---

## Key Numbers to Remember

### Face Density & Performance

| Triangles | Use Case | File Size (GLTF) | Visual Quality |
|-----------|----------|---|---|
| 5K | Thumbnail | 200 KB | Poor |
| 10K | Web mobile | 400 KB | Fair |
| **25K** | **Web standard** | **600 KB-1.2 MB** | **Good** |
| 50K | High-quality web | 1.2-2.5 MB | Very Good |
| 100K+ | Professional/VR | 2.5+ MB | Excellent |

### Simplification Quality Impact

| Reduction % | Visual Impact | Typical Use |
|---|---|---|
| 50% | Imperceptible | High-quality LOD |
| 70% | Very minor | Standard distant view |
| 90% | Minor artifacts | Far background |
| 95% | Visible artifacts | Very distant only |
| 98%+ | Severe | Silhouette/collision only |

### Diffusion Generation Time Breakdown

```
Steps 30: ~8-12s     (quick preview)
Steps 50: ~15-25s    (production)
Steps 75: ~25-35s    (high quality)
Steps 100: ~35-50s   (diminishing returns)

Per-step cost: ~0.2-0.4s on modern GPU
Solver impact: DPM-Solver ~30% faster than DDPM
```

---

## Decision Trees

### "Which simplification ratio should I use?"

```
┌─ What's your primary goal?
│
├─ Maximum quality
│  └─ Use 30-50% reduction (70-50% original faces)
│
├─ Balance quality & file size
│  └─ Use 50-70% reduction (best for web)
│
├─ Mobile/constrained device
│  └─ Use 80-90% reduction
│
└─ Preview/thumbnail
   └─ Use 95%+ reduction
```

### "Which guidance strength should I use?"

```
┌─ What's your primary need?
│
├─ Following prompt strictly
│  └─ guidance = 12.0-13.0
│
├─ Balance prompt + creativity
│  └─ guidance = 10.0-12.0 ← RECOMMENDED
│
├─ Diverse creative output
│  └─ guidance = 8.0-9.5
│
└─ Consistent/reproducible
   └─ guidance = 12.0-13.0 + fixed seed
```

### "How many sampling steps do I need?"

```
┌─ What's your constraint?
│
├─ Speed critical (<10s)
│  └─ steps = 30-40
│
├─ Standard (15-30s target)
│  └─ steps = 50 ← RECOMMENDED
│
├─ High quality (30-40s target)
│  └─ steps = 75
│
└─ Maximum quality (no constraint)
   └─ steps = 100 (marginal improvement)
```

---

## Common Parameter Combinations

### Preset 1: Fast Preview (Quick iteration)
```
guidance_strength: 10.0
sampling_steps: 30
Result: 8-12s, Fair-Good quality
Use: Quick testing, thumbnails
```

### Preset 2: Production Standard (RECOMMENDED)
```
guidance_strength: 12.0
sampling_steps: 50
Result: 15-25s, Excellent quality
Use: Final output, portfolio
```

### Preset 3: High Quality (Professional)
```
guidance_strength: 12.5
sampling_steps: 75
Result: 25-35s, Outstanding quality
Use: Critical output, VR content
```

### Preset 4: Creative Exploration (Diversity)
```
guidance_strength: 8.5
sampling_steps: 50
Result: 15-25s, Very Good quality, High diversity
Use: Ideation, concept exploration
```

---

## Algorithms at a Glance

| Algorithm | Speed | Quality | Best For | Complexity |
|-----------|-------|---------|----------|------------|
| **QEM** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | General use, quality priority | Medium |
| Vertex Clustering | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Large datasets, speed priority | Low |
| Edge Collapse | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Topology preservation | High |
| Progressive Mesh | ⭐⭐⭐ | ⭐⭐⭐⭐ | Multi-resolution LOD | Medium |

**Recommendation**: Use **QEM** for most cases.

---

## Implementation Quick Start

### Python: Simple Mesh Simplification
```python
import trimesh

mesh = trimesh.load('model.obj')
simplified = mesh.simplify_mesh(
    target_reduction=0.7,  # 70% reduction
    iterate_count=7
)
simplified.export('simplified.obj')
```

### Python: Multi-LOD Generation
```python
for reduction in [0.0, 0.5, 0.8, 0.95]:
    lod = mesh.simplify_mesh(target_reduction=reduction)
    lod.export(f'model_LOD{int(reduction*10)}.obj')
```

### Python: Diffusion 3D Generation
```python
config = {
    'guidance_strength': 12.0,
    'sampling_steps': 50,
    'negative_prompt': 'artifacts, low quality'
}
mesh = model.generate(prompt, **config)
```

---

## When to Simplify More vs. Less

### Simplify More (80-95% reduction) When:
- ✓ Mobile/web viewing required
- ✓ Real-time performance critical
- ✓ File size severely limited
- ✓ Viewing distance far
- ✓ Can use normal maps for detail

### Simplify Less (30-50% reduction) When:
- ✓ High-quality output required
- ✓ Close-up viewing expected
- ✓ Professional/portfolio use
- ✓ Performance not constrained
- ✓ Detailed geometry important

---

## Troubleshooting Quick Reference

| Problem | Likely Cause | Quick Fix |
|---------|---|---|
| Mesh looks too plastic/smooth | Guidance too high | ↓ guidance to 11-12 |
| Doesn't match prompt | Guidance too low | ↑ guidance to 12-13 |
| Takes too long | Too many steps | ↓ steps to 40-50 |
| Output is inconsistent | Temperature too high | ↓ to 0.7 |
| Has artifacts | Guidance >15 or not enough steps | ↓ guidance, ↑ steps to 75 |
| Mesh is too detailed (slow) | Target reduction too low | ↑ reduction to 60-70% |

---

## Integration Checklist for Pixal3D

- [ ] Choose simplification algorithm: **QEM** ✓
- [ ] Define reduction ratio: **50-70%** for standard, **30-50%** for high-quality
- [ ] Generate LOD levels: 0% → 50% → 80% → 95%
- [ ] Set diffusion baseline: guidance=12.0, steps=50
- [ ] Test with negative prompt to remove artifacts
- [ ] Profile performance at each LOD level
- [ ] Validate file sizes meet targets
- [ ] Test on target devices/browsers
- [ ] Document chosen parameters in config

---

## Further Reading

### Academic Papers (Most Important)
1. **"Surface Simplification Using Quadric Error Metrics"** (Garland & Heckbert, 1997)
   - Foundational QEM algorithm

2. **"Polygonal Simplification: An Overview"** (Luebke, 2001)
   - Comprehensive survey of simplification techniques

3. **Diffusion Models papers** (Score-based generation, DiffusionPolicy, etc.)
   - Foundation of modern 3D generation

### Open-Source Tools
- **MeshLab**: Interactive mesh processing
- **Trimesh**: Python mesh library
- **Open3D**: Point cloud and mesh processing
- **PyMeshLab**: Python binding to MeshLab

### Online Resources
- Blender Remesh/Decimate documentation
- Unity/Unreal LOD documentation
- Three.js mesh simplification examples

---

## Performance Metrics Reference

### Simplification Quality Metrics
- **Hausdorff Distance**: Max deviation between original and simplified
- **Symmetric RMS Error**: Bidirectional distance
- **Volume Error**: Relative volume difference
- **Vertex Distance**: Average distance from new mesh to original

### Generation Quality Metrics
- **Prompt Adherence**: How well output matches text/image input
- **Geometry Quality**: Manifoldness, topology correctness
- **Visual Realism**: Texture/material/lighting quality

---

## Decision: When to Use What

| Scenario | Simplification % | Guidance | Steps | Why |
|----------|---|---|---|---|
| Web preview | 70-80% | 12.0 | 30 | Fast loading, quick preview |
| **Final output** | **50-60%** | **12.0** | **50** | Good quality/size balance |
| High-res model | 30-40% | 12.5 | 75 | Maximum quality |
| Mobile app | 85-90% | 10.0 | 40 | Performance priority |
| VR content | 50-60% | 12.5 | 75 | Must maintain 90+ FPS |
| Print/export | 20-30% | 13.0 | 75 | Quality priority |

---

