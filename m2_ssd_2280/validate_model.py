import numpy as np, trimesh
import build_model as b

b.build_pcb(); b.build_edge_contacts(); b.build_screw_ring()
b.build_chips(); b.build_small_parts(); b.build_silkscreen()

bad = []
for name, p in b.PARTS.items():
    if not p.verts:
        continue
    v = np.asarray(p.verts, dtype=float)
    tris = []
    for _, face in p.faces:
        if len(face) == 3:
            tris.append(face)
        else:
            for i in range(1, len(face) - 1):
                tris.append((face[0], face[i], face[i + 1]))
    m = trimesh.Trimesh(vertices=v, faces=np.asarray(tris, dtype=int), process=False)
    if not m.is_watertight or not m.is_winding_consistent or m.volume <= 0:
        bad.append((name, bool(m.is_watertight), bool(m.is_winding_consistent), round(float(m.volume), 4), len(m.faces)))
print('parts', len(b.PARTS), 'bad', len(bad))
for row in bad:
    print(row)
