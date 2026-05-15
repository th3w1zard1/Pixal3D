# Diffusion-Based 3D Generation: Parameter Tuning Guide

## 1. Understanding the Diffusion Process for 3D Generation

### The Denoising Process

Modern diffusion models for 3D generation work through iterative denoising:

```
Step 0:   Pure noise (random 3D representation)
Step 1:   Slight structure emerges
Step 10:  General shape visible
Step 25:  Major details forming
Step 50:  Final details (diminishing returns beyond this)
Step 100: Very minor improvements only
```

Each step applies learned denoising guided by:
- **Condition**: Text prompt or image input
- **Guidance strength**: How strictly to follow condition vs. learned distribution

---

## 2. Guidance Strength Deep Dive

### Mathematical Foundation

The guidance term uses **Classifier-Free Guidance (CFG)**:

```
x_t = x_uncond + λ * (x_cond - x_uncond)

where:
  x_t = final predicted noise at timestep t
  x_uncond = model prediction without condition
  x_cond = model prediction with condition
  λ = guidance_strength (typical: 7.5-15.0)
```

**Interpretation**:
- When λ=0: Model ignores prompt, generates random distribution
- When λ=1: Standard conditional generation
- When λ>1: Amplifies difference between conditional and unconditional
  - λ=10 means 10× amplification of prompt adherence
  - λ=15 means 15× amplification

### Practical Effects by Value

```
Value   | Behavior                  | Visual Result
--------|---------------------------|------------------------------------------
0-1     | Ignores prompt           | Abstract, random, off-topic
1-3     | Weak adherence           | Related to prompt but very diverse
3-5     | Loose adherence          | On-topic but creative interpretation
5-8     | Moderate adherence       | Good prompt match, natural-looking
8-12    | Strong adherence         | Literal interpretation, slight artifacts
12-15   | Very strong adherence    | Potentially over-saturated
15-20   | Extreme adherence        | Noticeable distortion and artifacts
20+     | Overly extreme           | Severe artifacts, unrealistic geometry
```

### How Guidance Strength Affects 3D Quality

**Low guidance (5-7)**: 
- ✓ Diverse, creative outputs
- ✓ Natural-looking geometry
- ✗ May not precisely match prompt
- ✗ Inconsistent across multiple generations

**Medium guidance (10-12)** ← RECOMMENDED:
- ✓ Strong prompt adherence
- ✓ Realistic geometry
- ✓ Consistent results
- ✓ Balances creativity and control

**High guidance (12-15)**:
- ✓ Very precise prompt following
- ✗ Potential over-saturation
- ✗ Less geometric diversity
- ✗ Sometimes unrealistic material distribution

**Very high (15+)**:
- ✗ Visible artifacts
- ✗ Unrealistic geometry
- ✗ Potential topology issues
- ✗ Not recommended

### Task-Specific Recommendations

| Task | Guidance | Reason |
|------|----------|--------|
| Exploration/ideation | 8.0-9.5 | Creative variation while staying on-topic |
| Production output | 11.0-12.5 | Best quality + prompt adherence balance |
| Specific requirement | 13.0-14.0 | Strict control, slight artifact risk |
| Style variation | 7.5-9.0 | Maximize creative interpretation |
| Consistency | 12.0-13.0 | Stable, repeatable results |

---

## 3. Sampling Steps Analysis

### Quality-Speed Tradeoff

```python
# Typical generation times (on RTX 4090)
steps    quality   time (sec)  quality_gain  recommendations
---      -------   ---------   -----------   ---------------
20       Poor      3-5         baseline      Skip, too low
30       Fair      5-8         +25%          Only for quick tests
40       Good      8-12        +40%          For fast iteration
50       V.Good   12-20        +55%          RECOMMENDED
75       Excellent 18-30       +65%          High quality
100      Excellent 24-40       +70%          Diminishing returns
150      Excellent 36-60       +72%          Not worth it
```

### Quality Curve Analysis

**Quality gain per step** (relative):
```
Steps 20→30:   +0.83% per step (steep improvement)
Steps 30→50:   +0.66% per step
Steps 50→75:   +0.27% per step (flattening)
Steps 75→100:  +0.10% per step (marginal)
Steps 100→150: +0.03% per step (minimal)
```

**Key observation**: Most quality improvement happens in first 50 steps; beyond that, steep diminishing returns.

### Solver Impact on Step Efficiency

Different solvers achieve different quality per step:

| Solver | Steps for Good | Time | Quality | Notes |
|--------|---|---|---|---|
| DDPM | 100+ | Slow | Baseline | Standard, needs many steps |
| DDIM | 50-75 | Moderate | Good | Much faster than DDPM |
| DPM-Solver | 25-50 | Fast | V.Good | Often better than DDIM |
| Euler | 50+ | Fast | Good | Simple, can be unstable |
| Heun | 40-60 | Moderate | V.Good | Higher-order, smoother |

**Recommendation for Pixal3D**:
- Use **DPM-Solver** with **50 steps** as baseline
- Can reduce to **30 steps** for preview
- Can increase to **75 steps** for high-quality output

---

## 4. Noise Schedule Optimization

### How Noise Schedules Work

The noise schedule defines how much noise to add at each timestep:

```
t=0:    Pure noise (α=0, σ=1)
t=T/4:  Mixed signal/noise (α≈0.5, σ≈0.7)
t=T/2:  More signal than noise (α≈0.7, σ≈0.5)
t=3T/4: Mostly signal (α≈0.9, σ≈0.1)
t=T:    Pure signal (α≈1.0, σ≈0.0)

where α = signal amplitude, σ = noise amplitude
```

### Common Noise Schedules

**1. Linear Schedule** (simple but often suboptimal)
```
α_t = sqrt(1 - (t/T) * β_max)
```
- Simple to implement
- Uniform noise removal rate
- Often leaves artifacts

**2. Quadratic/Sqrt Schedule** (better signal preservation)
```
α_t = sqrt(1 - sqrt(t/T) * β_max)
```
- Slower early denoising (more time on noisy data)
- Faster late denoising (quicker signal refinement)
- Better for complex geometries

**3. Cosine Schedule** (empirically best) ← RECOMMENDED
```
α_t = cos((t/T + s) / (1 + s) × π/2)²
where s ≈ 0.008 (offset for numerical stability)
```
- Smooth transition from noise to signal
- Proven in practice (used in DDPM, Stable Diffusion)
- Best for image and 3D generation
- Industry standard

**4. Power Law Schedules** (specialized)
```
α_t = (1 - t/T)^p
where p = 1.0-2.0
```
- Customizable aggressiveness
- Less common, requires tuning

### Scheduler Impact on Quality

Using **Cosine scheduler** with **50 steps** typically produces better results than:
- Linear scheduler with **75 steps**
- Quadratic scheduler with **60 steps**

**Recommendation**: Always use cosine scheduler unless model documentation specifies otherwise.

---

## 5. Advanced Parameter Tuning

### 5.1 Temperature Parameter

**Definition**: Controls randomness in sampling decisions at each step.

```
probability ∝ exp(logits / temperature)

where:
  temperature < 1.0: More deterministic (sharper distribution)
  temperature = 1.0: Normal distribution
  temperature > 1.0: More random (softer distribution)
```

**Typical range for 3D generation**: 0.7-1.0

| Temperature | Effect | Use Case |
|---|---|---|
| 0.5 | Very deterministic | Consistent output, less variation |
| 0.7 | Deterministic | Standard choice, recommended |
| 0.8 | Balanced | Default in many models |
| 1.0 | Normal | Maximum randomness within normal range |
| 1.2+ | Very random | Creative exploration |

**Recommendation for Pixal3D**: 0.7-0.8

### 5.2 Conditioning Scale (for image-to-3D)

**Definition**: Strength of image influence on output (separate from text guidance).

```
final_output = α * image_conditioned + (1-α) * text_conditioned

where α = image_scale / (image_scale + text_scale)
```

**Typical range**: 0.0-2.0 (model dependent)

| Value | Effect | Use |
|---|---|---|
| 0.0 | Ignore image | Pure text generation |
| 0.3-0.5 | Image suggests style | Text is primary |
| **0.6-0.8** | **Balanced** | **Recommended** |
| 0.9-1.2 | Image constrains result | Strict adherence |
| 1.5-2.0 | Strong image dominance | Preserve image details |

**For your use case**: 0.7-0.8 provides good balance between image and text prompts.

### 5.3 Negative Prompts

**Effect**: Explicitly tell model what NOT to generate.

```
negative_prompt_effect ∝ -λ * (x_neg - x_uncond)
```

**Effective negative prompts for 3D**:
```
"low quality, blurry, distorted geometry, non-manifold, 
 artifacts, discontinuous surface, missing geometry"
```

**Impact**: Adds ~10-15% to generation time but significantly improves quality.

### 5.4 Scheduler Steps (T parameter)

**Definition**: Number of scheduling steps (usually equals sampling steps).

- Determines granularity of noise schedule
- Should match number of sampling steps
- More steps = finer control, but with severe diminishing returns

**Typical**: Steps = T (e.g., 50 steps = 50 scheduler steps)

---

## 6. Practical Parameter Configurations

### Configuration A: Fast Preview
```yaml
guidance_strength: 10.0
sampling_steps: 30
scheduler_type: cosine
solver: dpm_solver
temperature: 0.7
negative_prompt: "artifacts, low quality"

Expected results:
  - Time: ~8-12 seconds
  - Quality: Fair-Good
  - Use: Quick iteration, thumbnails
```

### Configuration B: Standard Production (RECOMMENDED)
```yaml
guidance_strength: 12.0
sampling_steps: 50
scheduler_type: cosine
solver: dpm_solver
temperature: 0.75
negative_prompt: "artifacts, low quality, distorted geometry"
image_scale: 0.75  # If image-conditioned

Expected results:
  - Time: ~15-25 seconds
  - Quality: Excellent
  - Use: Production output, portfolio
  - Consistency: High
```

### Configuration C: High Quality
```yaml
guidance_strength: 12.5
sampling_steps: 75
scheduler_type: cosine
solver: dpm_solver
temperature: 0.8
negative_prompt: "artifacts, low quality, distorted geometry, non-manifold"
image_scale: 0.75

Expected results:
  - Time: ~25-35 seconds
  - Quality: Outstanding
  - Use: Critical output, VR/AR
  - Trade-off: Longer generation time
```

### Configuration D: Creative Exploration
```yaml
guidance_strength: 8.5
sampling_steps: 50
scheduler_type: cosine
solver: dpm_solver
temperature: 0.9
negative_prompt: "artifacts"
image_scale: 0.6

Expected results:
  - Time: ~15-25 seconds
  - Quality: Very Good
  - Diversity: High
  - Use: Concept exploration, ideation
```

### Configuration E: Consistency/Reproducibility
```yaml
guidance_strength: 12.0
sampling_steps: 50
scheduler_type: cosine
solver: dpm_solver
temperature: 0.65
negative_prompt: "artifacts, low quality, distorted geometry"
seed: <fixed>  # Set specific seed for reproducibility

Expected results:
  - Time: ~15-25 seconds
  - Quality: Excellent
  - Consistency: Near-perfect across runs
  - Use: Batch generation, testing
```

---

## 7. Troubleshooting Common Issues

### Issue: Output looks overly smooth/plastic

**Causes**:
- Guidance too high (>14)
- Temperature too low (<0.6)
- Not enough steps

**Solution**:
```python
# Before (plastic-looking):
guidance_strength = 15.0
steps = 50
temperature = 0.5

# After (more natural):
guidance_strength = 12.0
steps = 75
temperature = 0.8
```

### Issue: Output doesn't match prompt

**Causes**:
- Guidance too low (<9)
- Negative prompt interfering
- Image scale too high (if image-conditioned)

**Solution**:
```python
# Before (weak prompt adherence):
guidance_strength = 8.0
image_scale = 0.9

# After (strong prompt adherence):
guidance_strength = 12.0
image_scale = 0.7
negative_prompt = ""  # Remove generic negative prompt
```

### Issue: Artifacts or distorted geometry

**Causes**:
- Guidance too high
- Solver instability with large guidance
- Temperature extreme (too low or high)
- Not enough steps

**Solution**:
```python
# Before (artifacts):
guidance_strength = 16.0
solver = "euler"
temperature = 0.5

# After (clean geometry):
guidance_strength = 12.0
solver = "dpm_solver"
temperature = 0.75
sampling_steps = 75
```

### Issue: Generation is too slow

**Causes**:
- Too many steps (>100)
- Using slow solver (DDPM)
- Temperature very low (requires more iterations)

**Solution**:
```python
# Before (slow):
sampling_steps = 100
solver = "ddpm"

# After (fast without quality loss):
sampling_steps = 50
solver = "dpm_solver"
# Expected: 2× faster, similar or better quality
```

### Issue: Inconsistent results across runs

**Causes**:
- Temperature too high
- Random seed not fixed
- Guidance strength in unstable range

**Solution**:
```python
import torch
import numpy as np

# Fix randomness:
torch.manual_seed(42)
np.random.seed(42)

# Lower temperature for consistency:
temperature = 0.65  # Avoid 0.9+

# Use stable guidance range:
guidance_strength = 12.0  # Avoid 14-16 range
```

---

## 8. Model-Specific Parameter Recommendations

### Stable 3D / Stable Diffusion 3D Models

**Recommended baseline**:
```python
guidance_scale: 12.0
steps: 50
solver: dpm_solver
negative_prompt: "artifacts, blurry, distorted, low quality"
```

**Notes**:
- Stable at guidance values up to 15
- 50 steps is sweet spot (diminishing returns after)
- Works well with cosine scheduler
- Sensitive to very high guidance (>16)

### TripoSR (Image-to-3D)

**Recommended baseline**:
```python
guidance_scale: 10.0  # Lower due to image conditioning
steps: 50
image_scale: 0.75
solver: dpm_solver
```

**Notes**:
- Image conditioning reduces need for high guidance
- Default guidance often lower than text-only models
- Good detail preservation with 50+ steps

### Point-E (Fast 3D Generation)

**Recommended baseline**:
```python
guidance_scale: 7.5  # Lower by default
steps: 30  # Can achieve good quality with fewer steps
solver: dpm_solver
```

**Notes**:
- Designed for speed (30 steps optimal)
- Lower guidance sweet spot
- Trade-off: Lower detail than other models

### Custom/Fine-tuned Models

**General approach**:
1. Start with 12.0 guidance, 50 steps
2. Adjust guidance ±1-2 based on prompt adherence
3. Adjust steps ±10 based on visual quality
4. Lock in best configuration

---

## 9. Performance Optimization

### Speed Optimization Strategies

**Strategy 1: Reduce Steps**
```python
# Trade-off: 30 steps → 50 steps
# Quality loss: ~15%
# Speed gain: 40% faster
config = {
    'guidance_strength': 12.0,
    'sampling_steps': 30,  # vs 50
    'solver': 'dpm_solver',
}
```

**Strategy 2: Use Faster Solver**
```python
# Trade-off: DDPM → DPM-Solver
# Quality improvement: ~10%
# Speed gain: 30% faster
config = {
    'solver': 'dpm_solver',  # vs 'ddpm'
    'sampling_steps': 50,
}
```

**Strategy 3: Batch Processing**
```python
# Generate multiple models in parallel
import torch.multiprocessing as mp

prompts = ["a blue chair", "a red table", ...]
with mp.Pool(4):  # 4 GPU workers
    results = pool.map(generate_3d, prompts)
```

### Quality Optimization Strategies

**Strategy 1: Higher Steps + Lower Guidance**
```python
# Often gives better results than high guidance
config = {
    'guidance_strength': 10.0,   # Lower
    'sampling_steps': 75,         # Higher
}
# Result: Better geometry, less artifacts
```

**Strategy 2: Fine Negative Prompt**
```python
# Specific negative prompts remove common artifacts
negative_prompt = (
    "low quality, blurry, distorted, "
    "non-manifold, discontinuous surface, "
    "missing pieces, artifacts"
)
# Result: Cleaner geometry, better topology
```

**Strategy 3: Post-Processing Simplification**
```python
# Generate with high guidance, then simplify
config = {
    'guidance_strength': 12.0,
    'sampling_steps': 50,
}
mesh = generate_3d(prompt, config)

# Simplify to clean up minor artifacts
simplified = mesh.simplify_mesh(target_reduction=0.3)
```

---

## 10. Integration Example for Pixal3D

```python
from dataclasses import dataclass
from typing import Dict

@dataclass
class Diffusion3DConfig:
    """Configuration for diffusion-based 3D generation"""
    
    # Guidance parameters
    guidance_strength: float = 12.0
    negative_prompt: str = "artifacts, low quality, distorted geometry"
    
    # Sampling parameters
    sampling_steps: int = 50
    solver: str = "dpm_solver"
    temperature: float = 0.75
    
    # Conditioning (if image-to-3D)
    image_scale: float = 0.75
    text_scale: float = 1.0
    
    # Scheduler
    noise_schedule: str = "cosine"
    
    # Advanced
    seed: int = None
    num_inference_steps: int = None  # Override sampling_steps if set
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for model inference"""
        return {
            'guidance_scale': self.guidance_strength,
            'negative_prompt': self.negative_prompt,
            'num_inference_steps': self.num_inference_steps or self.sampling_steps,
            'solver_type': self.solver,
            'temperature': self.temperature,
            'image_conditioning_scale': self.image_scale,
        }


class Pixal3DGenerator:
    """Wrapper for Pixal3D generation with optimized parameters"""
    
    # Preset configurations
    PRESETS = {
        'preview': Diffusion3DConfig(
            guidance_strength=10.0,
            sampling_steps=30,
            temperature=0.8,
        ),
        'production': Diffusion3DConfig(
            guidance_strength=12.0,
            sampling_steps=50,
            temperature=0.75,
        ),
        'high_quality': Diffusion3DConfig(
            guidance_strength=12.5,
            sampling_steps=75,
            temperature=0.8,
        ),
        'creative': Diffusion3DConfig(
            guidance_strength=8.5,
            sampling_steps=50,
            temperature=0.9,
        ),
    }
    
    def __init__(self, model):
        self.model = model
    
    def generate(self, 
                 prompt: str, 
                 image_path: str = None,
                 preset: str = 'production',
                 **kwargs) -> object:
        """
        Generate 3D model with optimized parameters
        
        Args:
            prompt: Text description
            image_path: Optional image for image-to-3D
            preset: One of 'preview', 'production', 'high_quality', 'creative'
            **kwargs: Override specific parameters
        
        Returns:
            Generated 3D mesh
        """
        
        # Get preset configuration
        config = self.PRESETS[preset]
        
        # Apply overrides
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        # Generate
        generation_params = config.to_dict()
        
        if image_path:
            mesh = self.model.generate_from_image(
                image_path=image_path,
                prompt=prompt,
                **generation_params
            )
        else:
            mesh = self.model.generate_from_text(
                prompt=prompt,
                **generation_params
            )
        
        return mesh


# Usage:
generator = Pixal3DGenerator(your_model)

# Standard production
mesh = generator.generate(
    "a blue ceramic vase",
    preset='production'
)

# Creative exploration with overrides
mesh = generator.generate(
    "a glass sculpture",
    preset='creative',
    sampling_steps=75,  # Override: higher quality
    guidance_strength=9.0  # Override: less strict
)

# High-quality from image
mesh = generator.generate(
    "modern chair design",
    image_path="chair_photo.jpg",
    preset='high_quality'
)
```

---

## 11. Quick Reference: Parameter Effects

| Parameter | Increase | Decrease | Trade-off |
|-----------|----------|----------|-----------|
| **Guidance** | Stricter prompt | More creative | Quality vs Diversity |
| **Steps** | Better quality | Faster | Quality vs Speed |
| **Temperature** | More random | More deterministic | Creativity vs Consistency |
| **Image Scale** | More image-like | More text-like | Image vs Text fidelity |

**Golden rule**: Start with production config, adjust one parameter at a time.

