# Mesh Simplification: Implementation Guide & Code Patterns

## 1. Popular Open-Source Libraries & Tools

### Python Mesh Simplification Libraries

#### 1.1 PyMeshLab (Python binding to MeshLab)
```python
import pymeshlab

# Load mesh
ms = pymeshlab.MeshSet()
ms.load_new_mesh("model.obj")

# Simplify using Quadric Error Metric
# Target: reduce triangles to 30% (70% reduction)
target_faces = int(ms.current_mesh().face_number() * 0.3)

ms.simplification_quadricedgemesh_collapse(
    targetfacecount=target_faces,
    updateflag=True,
    preserveborder=True,
    preservenormal=True,
    quality_thr=0.3
)

ms.save_current_mesh("simplified.obj")
```

**Pros**: Industry-proven (uses same algorithms as MeshLab)  
**Cons**: Heavy dependency, can be slow on large meshes

#### 1.2 Pyfqmr (Fast Quadric Mesh Simplification)
```python
import pyfqmr

# Create simplifier
mesh_simplify = pyfqmr.Simplify()

# Load mesh from vertices and faces
mesh_simplify.setMesh(vertices, triangles)

# Simplify to 30% of original (70% reduction)
target_reduction = 0.7
mesh_simplify.simplify(target_reduction=target_reduction)

# Get simplified mesh
simplified_vertices, simplified_triangles, normals = mesh_simplify.getMesh()
```

**Pros**: Fast C++ implementation, lightweight  
**Cons**: Less mature than MeshLab, fewer options

#### 1.3 Trimesh (General mesh processing)
```python
import trimesh

# Load mesh
mesh = trimesh.load('model.obj')

# Option 1: Simple vertex reduction (clustering-based)
simplified = mesh.simplify_mesh(
    target_reduction=0.7,  # Remove 70% of vertices
    iterate_count=7
)

# Option 2: Using quadric error metrics (if tinysimplify installed)
# pip install tinysimplify
import tinysimplify
simplified_vertices, simplified_faces = tinysimplify.simplify(
    vertices=mesh.vertices,
    faces=mesh.faces,
    target_reduction=0.7
)

simplified.export('simplified.obj')
```

**Pros**: General mesh processing library, good documentation  
**Cons**: Not specialized for simplification

#### 1.4 Open3D
```python
import open3d as o3d

# Load mesh
mesh = o3d.io.read_triangle_mesh("model.obj")

# Method 1: Vertex clustering
mesh_simplified = mesh.simplify_vertex_clustering(
    voxel_size=0.05  # Voxel grid size; adjust for desired reduction
)

# Method 2: Quadric Error Metrics (edge collapse)
mesh_simplified = mesh.simplify_quadric_mesh_decay(
    target_number_of_triangles=50000  # Direct target count
)

# Save
o3d.io.write_triangle_mesh("simplified.ply", mesh_simplified)
```

**Pros**: Easy to use, good for point clouds too  
**Cons**: Less control than specialized libraries

### C/C++ Libraries (For Performance-Critical Code)

- **Fast Quadric Mesh Simplification** (Sven Forstmann)
  - Pure C implementation, very fast
  - Minimal dependencies
  - GitHub: pmp-library/pmp-library

- **MeshLab** (Open source, C++)
  - Professional-grade mesh processing
  - Multiple simplification algorithms
  - Command-line and programmatic interfaces

---

## 2. Implementing QEM in Python: Pseudocode

```python
import numpy as np
from scipy.spatial import distance
from collections import defaultdict
import heapq

class QuadricSimplifier:
    def __init__(self, vertices, faces):
        self.vertices = vertices.copy()
        self.faces = faces.copy()
        self.quadrics = {}
        self.vertex_pairs = {}
        self.heap = []
        
    def compute_plane_equation(self, v0, v1, v2):
        """Compute plane equation ax + by + cz + d = 0 from three vertices"""
        # Compute normal
        edge1 = v1 - v0
        edge2 = v2 - v0
        normal = np.cross(edge1, edge2)
        
        # Normalize
        norm = np.linalg.norm(normal)
        if norm < 1e-8:
            return None
        normal = normal / norm
        
        # Plane equation: normal · (v - v0) = 0
        # n_x*x + n_y*y + n_z*z + d = 0 where d = -n·v0
        d = -np.dot(normal, v0)
        
        return np.array([normal[0], normal[1], normal[2], d])
    
    def plane_to_quadric(self, plane):
        """Convert plane equation to quadric matrix"""
        a, b, c, d = plane
        quadric = np.outer(plane, plane)  # p*p^T
        return quadric
    
    def initialize_quadrics(self):
        """Compute initial quadric error matrices for each vertex"""
        vertex_faces = defaultdict(list)
        
        # Map vertices to faces
        for face_idx, (v0, v1, v2) in enumerate(self.faces):
            vertex_faces[v0].append(face_idx)
            vertex_faces[v1].append(face_idx)
            vertex_faces[v2].append(face_idx)
        
        # For each vertex, sum quadrics of adjacent faces
        for v_idx in range(len(self.vertices)):
            quadric = np.zeros((4, 4))
            
            for face_idx in vertex_faces[v_idx]:
                v0_idx, v1_idx, v2_idx = self.faces[face_idx]
                v0 = self.vertices[v0_idx]
                v1 = self.vertices[v1_idx]
                v2 = self.vertices[v2_idx]
                
                plane = self.compute_plane_equation(v0, v1, v2)
                if plane is not None:
                    face_quadric = self.plane_to_quadric(plane)
                    quadric += face_quadric
            
            self.quadrics[v_idx] = quadric
    
    def compute_error(self, v1_idx, v2_idx, target_pos):
        """Compute error of contracting v1 and v2 to target_pos"""
        combined_quadric = self.quadrics[v1_idx] + self.quadrics[v2_idx]
        
        # Homogeneous coordinates: [x, y, z, 1]
        pos_h = np.array([target_pos[0], target_pos[1], target_pos[2], 1.0])
        
        error = pos_h @ combined_quadric @ pos_h.T
        return error
    
    def compute_target_position(self, v1_idx, v2_idx):
        """Compute optimal target position for edge contraction"""
        combined_quadric = self.quadrics[v1_idx] + self.quadrics[v2_idx]
        
        # Try to find exact optimal position
        # Modify bottom-right to ensure invertibility
        q_3x3 = combined_quadric[:3, :3]
        q_vec = combined_quadric[:3, 3]
        
        try:
            # Solve: Q_3x3 * v + q_vec = 0
            target = -np.linalg.solve(q_3x3, q_vec)
            return target
        except np.linalg.LinAlgError:
            # If singular, use midpoint as fallback
            v1 = self.vertices[v1_idx]
            v2 = self.vertices[v2_idx]
            return (v1 + v2) / 2
    
    def initialize_heap(self):
        """Initialize priority queue with all vertex pairs"""
        edges = set()
        
        # Find all edges from faces
        for v0, v1, v2 in self.faces:
            edges.add((min(v0, v1), max(v0, v1)))
            edges.add((min(v1, v2), max(v1, v2)))
            edges.add((min(v2, v0), max(v2, v0)))
        
        # Compute error for each edge
        for v1, v2 in edges:
            target = self.compute_target_position(v1, v2)
            error = self.compute_error(v1, v2, target)
            
            heapq.heappush(self.heap, (error, v1, v2, target))
            self.vertex_pairs[(v1, v2)] = (error, target)
    
    def simplify(self, target_triangle_count):
        """Simplify mesh to target triangle count"""
        self.initialize_quadrics()
        self.initialize_heap()
        
        collapsed = set()  # Vertices that have been collapsed
        
        while len(self.heap) > 0 and len(self.faces) > target_triangle_count:
            error, v1, v2, target = heapq.heappop(self.heap)
            
            # Skip if already collapsed
            if v1 in collapsed or v2 in collapsed:
                continue
            
            # Contract edge
            self.contract_edge(v1, v2, target)
            collapsed.add(v2)  # Mark as collapsed
            
            # Remove faces with collapsed vertices
            self.faces = [f for f in self.faces 
                         if not (v2 in f or v1 in f and len({v1, v2} & set(f)) == 2)]
        
        return self.get_simplified_mesh()
    
    def contract_edge(self, v1, v2, target_pos):
        """Contract edge v1-v2, merging into v1 at target_pos"""
        # Update vertex position
        self.vertices[v1] = target_pos
        
        # Update quadric
        self.quadrics[v1] = self.quadrics[v1] + self.quadrics[v2]
        
        # Remap v2 -> v1 in all faces
        for i, (a, b, c) in enumerate(self.faces):
            if a == v2: self.faces[i] = (v1, b, c)
            if b == v2: self.faces[i] = (a, v1, c)
            if c == v2: self.faces[i] = (a, b, v1)
    
    def get_simplified_mesh(self):
        """Return simplified mesh (remove unreferenced vertices)"""
        # Remove degenerate faces
        valid_faces = []
        for a, b, c in self.faces:
            if a != b and b != c and c != a:
                valid_faces.append((a, b, c))
        
        return np.array(self.vertices), np.array(valid_faces)

# Usage:
simplifier = QuadricSimplifier(vertices, faces)
new_vertices, new_faces = simplifier.simplify(target_triangle_count=50000)
```

---

## 3. Practical Integration Examples

### Example 1: Multi-LOD Generation Pipeline

```python
import trimesh
import numpy as np

def generate_lod_meshes(original_mesh_path, output_prefix):
    """Generate multiple LOD meshes from original"""
    
    mesh = trimesh.load(original_mesh_path)
    print(f"Original: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
    
    # Define LOD levels: (name, reduction_ratio)
    lod_levels = [
        ("LOD0", 0.0),      # 100% (original)
        ("LOD1", 0.5),      # 50% reduction
        ("LOD2", 0.8),      # 80% reduction
        ("LOD3", 0.95),     # 95% reduction
    ]
    
    lod_meshes = {}
    
    for name, reduction in lod_levels:
        if reduction == 0.0:
            simplified = mesh
        else:
            target_reduction = reduction
            simplified = mesh.simplify_mesh(
                target_reduction=target_reduction,
                iterate_count=7
            )
        
        path = f"{output_prefix}_{name}.glb"
        simplified.export(path)
        
        print(f"{name}: {len(simplified.vertices)} vertices, "
              f"{len(simplified.faces)} faces "
              f"(reduction: {reduction*100:.1f}%)")
        
        lod_meshes[name] = simplified
    
    return lod_meshes

# Usage:
lod_meshes = generate_lod_meshes(
    "original_model.obj",
    "output/model"
)
```

### Example 2: Batch Processing with Quality Validation

```python
import trimesh
from pathlib import Path

def batch_simplify_with_validation(input_dir, output_dir, 
                                   target_reduction=0.7,
                                   max_deviation=0.05):
    """Simplify multiple meshes with quality checks"""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    for mesh_file in Path(input_dir).glob("*.obj"):
        try:
            print(f"Processing {mesh_file.name}...")
            
            mesh = trimesh.load(mesh_file)
            original_bounds = mesh.bounds
            
            # Simplify
            simplified = mesh.simplify_vertex_clustering(
                voxel_size=0.02  # Adjust based on model scale
            )
            
            # Validation checks
            simplified_bounds = simplified.bounds
            bounds_deviation = np.linalg.norm(
                original_bounds - simplified_bounds
            ) / np.linalg.norm(original_bounds)
            
            if bounds_deviation > max_deviation:
                print(f"  WARNING: High bounds deviation: {bounds_deviation:.3f}")
            
            # Check volume preservation (approximate)
            volume_error = abs(mesh.volume - simplified.volume) / mesh.volume
            if volume_error > 0.2:  # 20% volume error
                print(f"  WARNING: Volume error: {volume_error*100:.1f}%")
            
            # Save
            output_file = output_path / f"{mesh_file.stem}_simplified.obj"
            simplified.export(output_file)
            
            reduction = 1 - (len(simplified.vertices) / len(mesh.vertices))
            print(f"  ✓ {len(mesh.vertices)} → {len(simplified.vertices)} "
                  f"({reduction*100:.1f}% reduction)")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")

# Usage:
batch_simplify_with_validation(
    "input_models/",
    "output_models/",
    target_reduction=0.7
)
```

### Example 3: Dynamic Simplification Based on File Size Target

```python
import trimesh
import os

def simplify_to_file_size_target(mesh_path, target_size_mb=5.0):
    """Iteratively simplify mesh until it meets file size target"""
    
    mesh = trimesh.load(mesh_path)
    original_size = os.path.getsize(mesh_path) / (1024 * 1024)
    
    print(f"Original: {len(mesh.vertices)} vertices, "
          f"size: {original_size:.2f} MB")
    
    # Estimate reduction needed (rough approximation)
    # File size roughly scales with vertex count
    estimated_reduction = 1 - (target_size_mb / original_size)
    
    # Try with margin for safety
    current_reduction = min(estimated_reduction * 1.2, 0.95)
    
    while current_reduction < 0.99:
        simplified = mesh.simplify_mesh(
            target_reduction=current_reduction,
            iterate_count=7
        )
        
        # Export and check size
        temp_path = "/tmp/test_simplification.glb"
        simplified.export(temp_path)
        file_size = os.path.getsize(temp_path) / (1024 * 1024)
        
        print(f"Reduction {current_reduction*100:.1f}%: "
              f"{len(simplified.vertices)} vertices, "
              f"size: {file_size:.2f} MB")
        
        if file_size <= target_size_mb:
            print(f"✓ Target achieved!")
            return simplified
        
        # Increase reduction
        current_reduction += 0.05
    
    # If we get here, we couldn't achieve target
    print(f"WARNING: Could not achieve {target_size_mb} MB target")
    return simplified

# Usage:
simplified_mesh = simplify_to_file_size_target(
    "model.obj",
    target_size_mb=2.0
)
simplified_mesh.export("output.glb")
```

---

## 4. Performance Benchmarking

### Benchmark Template

```python
import time
import trimesh
import numpy as np

def benchmark_simplification(mesh_path, reduction_ratios=[0.5, 0.7, 0.9]):
    """Benchmark simplification performance"""
    
    mesh = trimesh.load(mesh_path)
    original_verts = len(mesh.vertices)
    original_faces = len(mesh.faces)
    
    print(f"Benchmark: {mesh_path}")
    print(f"Original: {original_verts} vertices, {original_faces} faces")
    print("\nReduction | Target Faces | Time (ms) | Achieved | Quality")
    print("-" * 60)
    
    for reduction in reduction_ratios:
        start = time.time()
        
        simplified = mesh.simplify_mesh(
            target_reduction=reduction,
            iterate_count=7
        )
        
        elapsed_ms = (time.time() - start) * 1000
        
        achieved_reduction = (1 - len(simplified.vertices) / len(mesh.vertices)) * 100
        
        # Quality metric: average edge length
        edges = simplified.edges_unique
        edge_lengths = np.linalg.norm(
            simplified.vertices[edges[:, 0]] - simplified.vertices[edges[:, 1]],
            axis=1
        )
        avg_edge_length = np.mean(edge_lengths)
        
        print(f"{reduction*100:6.0f}%  | {len(simplified.faces):12d} | "
              f"{elapsed_ms:8.1f} | {achieved_reduction:6.1f}% | "
              f"{avg_edge_length:.4f}")

# Usage:
benchmark_simplification("model.obj", [0.3, 0.5, 0.7, 0.9])
```

---

## 5. Quality Metrics & Comparison

### Hausdorff Distance Calculation

```python
from scipy.spatial.distance import cdist

def hausdorff_distance(vertices1, vertices2):
    """Compute symmetric Hausdorff distance between two point sets"""
    
    # Distance from vertices1 to vertices2
    d1 = np.min(cdist(vertices1, vertices2), axis=1)
    max_d1 = np.max(d1)
    
    # Distance from vertices2 to vertices1
    d2 = np.min(cdist(vertices2, vertices1), axis=1)
    max_d2 = np.max(d2)
    
    # Symmetric: max of both directions
    return max(max_d1, max_d2)

def compare_meshes(original_mesh, simplified_mesh):
    """Compare original and simplified meshes"""
    
    # Geometric error
    h_dist = hausdorff_distance(
        original_mesh.vertices,
        simplified_mesh.vertices
    )
    
    # Vertex reduction
    vertex_reduction = (1 - len(simplified_mesh.vertices) / 
                       len(original_mesh.vertices)) * 100
    
    # Face reduction
    face_reduction = (1 - len(simplified_mesh.faces) / 
                     len(original_mesh.faces)) * 100
    
    # Volume difference
    volume_error = abs(original_mesh.volume - simplified_mesh.volume) / original_mesh.volume * 100
    
    print(f"Vertex reduction: {vertex_reduction:.1f}%")
    print(f"Face reduction: {face_reduction:.1f}%")
    print(f"Hausdorff distance: {h_dist:.6f}")
    print(f"Volume error: {volume_error:.2f}%")
    
    return {
        'vertex_reduction': vertex_reduction,
        'face_reduction': face_reduction,
        'hausdorff_distance': h_dist,
        'volume_error': volume_error
    }
```

---

## 6. Integration with Your Pixal3D Pipeline

### Suggested Integration Points

```python
# In your image-to-3D pipeline:

def generate_3d_with_simplification(image_path, 
                                   guidance_strength=12.0,
                                   sampling_steps=50,
                                   simplification_ratio=0.5):
    """Generate 3D model from image with automatic simplification"""
    
    # 1. Generate mesh (your model output)
    generated_mesh = your_generation_model.generate(
        image_path,
        guidance_strength=guidance_strength,
        sampling_steps=sampling_steps
    )
    
    print(f"Generated: {len(generated_mesh.vertices)} vertices")
    
    # 2. Apply simplification
    simplified_mesh = generated_mesh.simplify_mesh(
        target_reduction=simplification_ratio,
        iterate_count=7
    )
    
    print(f"Simplified: {len(simplified_mesh.vertices)} vertices "
          f"({simplification_ratio*100:.0f}% reduction)")
    
    # 3. Optional: Generate LOD levels
    lods = {
        'high': simplified_mesh,  # Already simplified
        'medium': generated_mesh.simplify_mesh(0.8),
        'low': generated_mesh.simplify_mesh(0.95)
    }
    
    return simplified_mesh, lods
```

This integration guide provides practical code examples and performance benchmarking templates for mesh simplification in your Pixal3D pipeline.

