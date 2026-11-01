#!/usr/bin/env python3
"""
Procedural M.2 2280 NVMe SSD model (bare PCB, no label sticker).
All dimensions in millimetres.  X = length (0..80), Y = thickness (up),
Z = width (-11..11).  Exports a multi-object OBJ + MTL.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import numpy as np
import trimesh
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.geometry.polygon import orient

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "model"
OUT.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------
# materials
# ----------------------------------------------------------------------------
# name: (diffuse hex, specular hex, shininess, metallic hint for renderer)
MATERIALS = {
    "PCB_Black":      ("#16181b", "#3a3d40", 45, 0.10),
    "PCB_Edge":       ("#302e26", "#4a4738", 20, 0.05),
    "PCB_Dark":       ("#0e0f11", "#2a2c2e", 35, 0.05),
    "Gold":           ("#d8b45a", "#fff0b0", 120, 0.95),
    "Gold_Dark":      ("#9b772b", "#e0c070", 90, 0.90),
    "Copper":         ("#b87333", "#ffd0a0", 80, 0.90),
    "Chip_Black":     ("#111216", "#3c3d42", 60, 0.05),
    "Chip_Dark":      ("#191a1e", "#4a4b50", 50, 0.05),
    "Chip_Edge":      ("#0a0b0d", "#2a2b2e", 30, 0.05),
    "Silkscreen":     ("#e6e6dc", "#ffffff", 18, 0.0),
    "Marking_White":  ("#cfd0cb", "#f5f5f0", 35, 0.0),
    "Marking_Gray":   ("#8e9092", "#c8c8c8", 45, 0.0),
    "Cap_Body":       ("#7b5a3d", "#b08a60", 30, 0.05),
    "Cap_Terminal":   ("#b9b9b4", "#f0f0e8", 80, 0.75),
    "Res_Body":       ("#17181a", "#3a3b3d", 40, 0.05),
    "Res_Terminal":   ("#b8b8b3", "#f2f2ea", 80, 0.75),
    "Inductor_Body":  ("#3a3b3d", "#6a6b6d", 55, 0.15),
    "Inductor_Top":   ("#26272a", "#55565a", 55, 0.15),
    "Polymer_Body":   ("#252629", "#55565a", 45, 0.10),
    "Polymer_Top":    ("#707276", "#b8b9bc", 70, 0.55),
    "Crystal_Metal":  ("#b9bcc0", "#f4f5f7", 120, 0.85),
    "QFN_Body":       ("#131417", "#3a3b3f", 50, 0.05),
    "Solder":         ("#a8a8a3", "#e8e8e0", 70, 0.65),
    "Black_Plastic":  ("#0b0c0e", "#2a2b2e", 30, 0.02),
}


def hex_rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


# ----------------------------------------------------------------------------
# mesh / OBJ helpers
# ----------------------------------------------------------------------------
class Part:
    def __init__(self, name: str):
        self.name = name
        self.verts: list[tuple[float, float, float]] = []
        self.faces: list[tuple[str, tuple[int, ...]]] = []

    def add_face(self, pts: Iterable[Iterable[float]], mat: str):
        pts = list(pts)
        if len(pts) < 3:
            return
        off = len(self.verts)
        self.verts.extend(tuple(float(c) for c in p) for p in pts)
        self.faces.append((mat, tuple(range(off, off + len(pts)))))

    def add_mesh(self, mesh: trimesh.Trimesh, mat: str):
        if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
            return
        off = len(self.verts)
        self.verts.extend(tuple(float(c) for c in v) for v in mesh.vertices)
        for f in mesh.faces:
            self.faces.append((mat, tuple(int(off + i) for i in f)))

    def bounds(self):
        a = np.asarray(self.verts)
        return a.min(axis=0), a.max(axis=0)


PARTS: dict[str, Part] = {}


def part(name: str) -> Part:
    if name not in PARTS:
        PARTS[name] = Part(name)
    return PARTS[name]


def add_box(p: Part, cx: float, cz: float, sx: float, sz: float,
            y0: float, y1: float, mat: str):
    m = trimesh.creation.box(extents=(sx, y1 - y0, sz))
    m.apply_translation((cx, (y0 + y1) / 2, cz))
    p.add_mesh(m, mat)


def rounded_rect(cx: float, cz: float, w: float, d: float, r: float,
                 res: int = 10) -> Polygon:
    p = box(cx - w / 2, cz - d / 2, cx + w / 2, cz + d / 2)
    r = min(r, w * 0.45, d * 0.45)
    if r > 1e-5:
        p = p.buffer(-r, join_style=1, resolution=res).buffer(
            r, join_style=1, resolution=res)
    return p


def _ring_coords(poly: Polygon):
    yield list(poly.exterior.coords)[:-1]
    for interior in poly.interiors:
        yield list(interior.coords)[:-1]


def _signed_area(ring) -> float:
    s = 0.0
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        s += x1 * y2 - x2 * y1
    return s * 0.5


def add_extruded_poly(p: Part, poly: Polygon, y0: float, y1: float,
                      mat_top: str, mat_side: str | None = None,
                      mat_bottom: str | None = None):
    """Extrude a (possibly holed) XZ polygon.  Caps use triangulation."""
    if poly.is_empty:
        return
    if not isinstance(poly, Polygon):
        for g in poly.geoms:
            add_extruded_poly(p, g, y0, y1, mat_top, mat_side, mat_bottom)
        return
    mat_side = mat_side or mat_top
    mat_bottom = mat_bottom or mat_top
    v2, f = trimesh.creation.triangulate_polygon(poly)
    if len(f) == 0:
        return
    n = len(v2)
    off_b = len(p.verts)
    p.verts.extend((float(x), y0, float(z)) for x, z in v2)
    p.verts.extend((float(x), y1, float(z)) for x, z in v2)

    for tri in f:
        a, b, c = (v2[i] for i in tri)
        ar = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        top = tuple(off_b + n + i for i in tri)
        bot = tuple(off_b + i for i in tri)
        if ar > 0:
            top = top[::-1]
        else:
            bot = bot[::-1]
        p.faces.append((mat_top, top))
        p.faces.append((mat_bottom, bot))

    # dedicated side-wall vertices (one ring pair per boundary)
    for ring in _ring_coords(poly):
        if len(ring) < 3:
            continue
        ccw = _signed_area(ring) > 0
        m = len(ring)
        base = len(p.verts)
        p.verts.extend((float(x), y0, float(z)) for x, z in ring)
        p.verts.extend((float(x), y1, float(z)) for x, z in ring)
        for i in range(m):
            j = (i + 1) % m
            bi, bj = base + i, base + j
            ti, tj = base + m + i, base + m + j
            quad = (bi, ti, tj, bj) if ccw else (bi, bj, tj, ti)
            p.faces.append((mat_side, quad))


def add_package(p: Part, cx: float, cz: float, w: float, d: float, h: float,
                mat: str, y0: float = 0.8, corner: float = 0.18,
                bevel: float = 0.10, top_mat: str | None = None,
                side_mat: str | None = None):
    """SMD package with a small top chamfer."""
    base = rounded_rect(cx, cz, w, d, corner)
    top = affinity.scale(base, xfact=(w - 2 * bevel) / w,
                         yfact=(d - 2 * bevel) / d, origin=(cx, cz))
    top_mat = top_mat or mat
    side_mat = side_mat or mat
    y_mid = y0 + h - bevel
    y_top = y0 + h

    # bottom cap
    v2, f = trimesh.creation.triangulate_polygon(base)
    ob = len(p.verts)
    p.verts.extend((float(x), y0, float(z)) for x, z in v2)
    for tri in f:
        a, b, c = (v2[i] for i in tri)
        ar = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        bot = tuple(ob + i for i in tri)
        if ar < 0:
            bot = bot[::-1]
        p.faces.append((mat, bot))

    # top cap
    v2t, ft = trimesh.creation.triangulate_polygon(top)
    ot = len(p.verts)
    p.verts.extend((float(x), y_top, float(z)) for x, z in v2t)
    for tri in ft:
        a, b, c = (v2t[i] for i in tri)
        ar = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        topf = tuple(ot + i for i in tri)
        if ar > 0:
            topf = topf[::-1]
        p.faces.append((top_mat, topf))

    # side walls base->mid
    ring = list(base.exterior.coords)[:-1]
    m = len(ring)
    base_i = len(p.verts)
    p.verts.extend((float(x), y0, float(z)) for x, z in ring)
    p.verts.extend((float(x), y_mid, float(z)) for x, z in ring)
    ccw = _signed_area(ring) > 0
    for i in range(m):
        j = (i + 1) % m
        bi, bj = base_i + i, base_i + j
        ti, tj = base_i + m + i, base_i + m + j
        quad = (bi, ti, tj, bj) if ccw else (bi, bj, tj, ti)
        p.faces.append((side_mat, quad))

    # chamfer mid->top (same vertex count, top scaled about center)
    ring_t = list(top.exterior.coords)[:-1]
    if len(ring_t) != m:
        return
    cham_i = len(p.verts)
    p.verts.extend((float(x), y_mid, float(z)) for x, z in ring)
    p.verts.extend((float(x), y_top, float(z)) for x, z in ring_t)
    for i in range(m):
        j = (i + 1) % m
        bi, bj = cham_i + i, cham_i + j
        ti, tj = cham_i + m + i, cham_i + m + j
        quad = (bi, ti, tj, bj) if ccw else (bi, bj, tj, ti)
        p.faces.append((side_mat, quad))


def add_cylinder(p: Part, cx: float, cz: float, y0: float, y1: float,
                 r: float, mat: str, segments: int = 36,
                 cap_mat: str | None = None):
    cap_mat = cap_mat or mat
    base = len(p.verts)
    for y in (y0, y1):
        p.verts.append((cx, y, cz))
        for i in range(segments):
            a = 2 * math.pi * i / segments
            p.verts.append((cx + r * math.cos(a), y, cz + r * math.sin(a)))
    bc, tc = base, base + 1 + segments
    for i in range(segments):
        j = (i + 1) % segments
        bi, bj = base + 1 + i, base + 1 + j
        ti, tj = tc + 1 + i, tc + 1 + j
        p.faces.append((mat, (bi, ti, tj, bj)))
        p.faces.append((cap_mat, (bc, bj, bi)))       # bottom -Y
        p.faces.append((cap_mat, (tc, ti, tj)))       # top +Y


# ----------------------------------------------------------------------------
# text
# ----------------------------------------------------------------------------
_FONT_BOLD = FontProperties(family="DejaVu Sans", weight="bold")
_FONT_REG = FontProperties(family="DejaVu Sans", weight="normal")


def _text_polygons(text: str, size: float, bold: bool = True,
                   align: str = "center", valign: str = "center",
                   rot: float = 0.0) -> list[Polygon]:
    prop = _FONT_BOLD if bold else _FONT_REG
    tp = TextPath((0, 0), text, size=size, prop=prop, usetex=False)
    rings = []
    for coords in tp.to_polygons():
        if len(coords) < 3:
            continue
        poly = Polygon(coords).buffer(0)
        if poly.is_empty or poly.area < 1e-9:
            continue
        if poly.geom_type != "Polygon":
            for g in poly.geoms:
                if g.area > 1e-9:
                    rings.append(g)
        else:
            rings.append(poly)
    if not rings:
        return []
    rings.sort(key=lambda q: q.area, reverse=True)
    outers: list[tuple[int, Polygon]] = []
    holes_for: dict[int, list[Polygon]] = {}
    for i, r in enumerate(rings):
        containers = [j for j, s in enumerate(rings)
                      if j != i and s.area > r.area
                      and s.contains(r.representative_point())]
        if containers:
            j = min(containers, key=lambda k: rings[k].area)
            holes_for.setdefault(j, []).append(r)
        else:
            outers.append((i, r))
    polys: list[Polygon] = []
    for oi, o in outers:
        hs = holes_for.get(oi, [])
        poly = Polygon(o.exterior.coords, [h.exterior.coords for h in hs])
        if not poly.is_valid:
            poly = poly.buffer(0)
        if poly.is_empty:
            continue
        if poly.geom_type == "Polygon":
            polys.append(orient(poly, sign=1.0))
        else:
            polys.extend(orient(g, sign=1.0) for g in poly.geoms if g.area > 1e-9)

    # align using overall bounds of the original path
    bb = tp.get_extents()
    if align == "center":
        dx = -(bb.x0 + bb.x1) / 2
    elif align == "left":
        dx = -bb.x0
    elif align == "right":
        dx = -bb.x1
    else:
        dx = 0.0
    if valign == "center":
        dy = -(bb.y0 + bb.y1) / 2
    elif valign == "bottom":
        dy = -bb.y0
    elif valign == "top":
        dy = -bb.y1
    else:
        dy = 0.0
    out = []
    for poly in polys:
        q = affinity.translate(poly, xoff=dx, yoff=dy)
        if abs(rot) > 1e-9:
            q = affinity.rotate(q, rot, origin=(0, 0), use_radians=False)
        out.append(q)
    return out


def add_text(p: Part, text: str, x: float, z: float, cap_height: float,
             mat: str, y: float = 0.804, bold: bool = True,
             align: str = "center", valign: str = "center",
             rot: float = 0.0, bottom: bool = False, thick: float = 0.012):
    """Text as thin extruded geometry. cap_height is approximate capital height."""
    if not text:
        return
    size = cap_height / 0.72
    polys = _text_polygons(text, size, bold=bold, align=align,
                           valign=valign, rot=rot)
    if not polys:
        return
    for poly in polys:
        try:
            m = trimesh.creation.extrude_polygon(poly, height=thick)
        except Exception:
            continue
        if len(m.faces) == 0:
            continue
        vs = np.asarray(m.vertices, dtype=float).copy()
        if bottom:
            X = x + vs[:, 0]
            Z = z + vs[:, 1]
            Y = y - vs[:, 2]
        else:
            X = x + vs[:, 0]
            Z = z - vs[:, 1]
            Y = y + vs[:, 2]
        vv = np.column_stack([X, Y, Z])
        p.add_mesh(trimesh.Trimesh(vertices=vv, faces=m.faces, process=False), mat)


def add_line(p: Part, x1: float, z1: float, x2: float, z2: float,
             width: float, mat: str, y: float = 0.804, bottom: bool = False,
             thick: float = 0.010):
    line = LineString([(x1, z1), (x2, z2)])
    poly = line.buffer(width / 2, cap_style=2, join_style=2)
    if bottom:
        add_extruded_poly(p, poly, y - thick, y, mat)
    else:
        add_extruded_poly(p, poly, y, y + thick, mat)


def add_datamatrix(p: Part, cx: float, cz: float, y: float, size: float,
                   mat: str, seed: int = 1):
    n = 10
    m = size / (n + 1.2)
    gap = m * 0.12
    rng = np.random.default_rng(seed)
    for i in range(n):
        for j in range(n):
            on = bool(rng.random() < 0.48)
            if i == 0 or j == n - 1:
                on = True
            if i == n - 1:
                on = (j % 2 == 0)
            if j == 0:
                on = True
            if on:
                add_box(p, cx - size / 2 + m * (i + 0.6),
                        cz - size / 2 + m * (j + 0.6),
                        m - gap, m - gap, y, y + 0.006, mat)


# ----------------------------------------------------------------------------
# layout / occupancy
# ----------------------------------------------------------------------------
OCC: list[tuple[str, float, float, float, float]] = []


def occupy(name: str, cx: float, cz: float, w: float, d: float,
           margin: float = 0.0):
    OCC.append((name, cx - w / 2 - margin, cx + w / 2 + margin,
                cz - d / 2 - margin, cz + d / 2 + margin))


def check_occ(name: str, cx: float, cz: float, w: float, d: float,
              margin: float = 0.0, warn: bool = True) -> bool:
    x0, x1 = cx - w / 2 - margin, cx + w / 2 + margin
    z0, z1 = cz - d / 2 - margin, cz + d / 2 + margin
    for nm, a0, a1, b0, b1 in OCC:
        if x0 < a1 and x1 > a0 and z0 < b1 and z1 > b0:
            if warn:
                print(f"  ! overlap {name} with {nm}: "
                      f"x[{x0:.2f},{x1:.2f}] z[{z0:.2f},{z1:.2f}] vs "
                      f"x[{a0:.2f},{a1:.2f}] z[{b0:.2f},{b1:.2f}]")
            return False
    return True


# ----------------------------------------------------------------------------
# board
# ----------------------------------------------------------------------------
PCB_L, PCB_W, PCB_T = 80.0, 22.0, 0.8
KEY_Z0, KEY_Z1 = 4.4, 8.6
KEY_X = 5.2
SCREW_C = (79.0, 0.0)
SCREW_R = 2.12


def build_pcb():
    p = part("PCB")
    outline = box(0, -PCB_W / 2, PCB_L, PCB_W / 2)
    outline = outline.buffer(-0.7, join_style=1, resolution=12).buffer(
        0.7, join_style=1, resolution=12)
    outline = outline.difference(box(-1, KEY_Z0, KEY_X, KEY_Z1))
    outline = outline.difference(Point(*SCREW_C).buffer(SCREW_R, resolution=64))
    outline = outline.buffer(0)
    if outline.geom_type != "Polygon":
        raise RuntimeError(f"bad PCB outline: {outline.geom_type}")
    add_extruded_poly(p, outline, 0.0, PCB_T, "PCB_Black", "PCB_Edge", "PCB_Black")
    return outline


def build_edge_contacts():
    top = part("J1_Contacts_Top")
    bot = part("J1_Contacts_Bottom")
    pitch = 0.48
    slots = 45
    for pp, y0, y1 in ((top, PCB_T + 0.001, PCB_T + 0.031),
                       (bot, -0.031, -0.001)):
        for i in range(slots):
            z = -pitch * (slots - 1) / 2 + i * pitch
            if KEY_Z0 - 0.05 < z < KEY_Z1 + 0.05:
                continue
            w = 0.335
            poly = Polygon([
                (0.02, z - w / 2), (4.10, z - w / 2),
                (4.36, z - w / 2 + 0.11), (4.36, z + w / 2 - 0.11),
                (4.10, z + w / 2), (0.02, z + w / 2),
            ])
            add_extruded_poly(pp, poly, y0, y1, "Gold", "Gold", "Gold")


def build_screw_ring():
    outer = Point(*SCREW_C).buffer(SCREW_R + 0.75, resolution=80)
    inner = Point(*SCREW_C).buffer(SCREW_R, resolution=80)
    ring = outer.difference(inner).intersection(box(0, -3.2, 80, 3.2))
    if ring.is_empty:
        return
    for name, y0, y1 in (("ScrewPad_Top", PCB_T + 0.001, PCB_T + 0.031),
                         ("ScrewPad_Bottom", -0.031, -0.001)):
        p = part(name)
        add_extruded_poly(p, ring, y0, y1, "Gold", "Gold_Dark", "Gold")


# ----------------------------------------------------------------------------
# components
# ----------------------------------------------------------------------------
CHIPS = {
    "U1": dict(name="U1_Controller", cx=18.5, cz=0.0, w=12.0, d=12.0, h=0.92,
               kind="controller"),
    "U2": dict(name="U2_DRAM", cx=31.0, cz=0.0, w=9.0, d=11.0, h=0.82,
               kind="dram"),
    "U3": dict(name="U3_NAND1", cx=45.5, cz=0.0, w=14.0, d=18.0, h=1.02,
               kind="nand"),
    "U4": dict(name="U4_NAND2", cx=61.5, cz=0.0, w=14.0, d=18.0, h=1.02,
               kind="nand"),
}


def chip_marking(ch: dict):
    ref = ch["name"].split("_")[0]
    p = part(ref + "_Marking")
    cx, cz = ch["cx"], ch["cz"]
    top = PCB_T + ch["h"]
    kind = ch["kind"]
    if kind == "controller":
        add_text(p, "SAMSUNG", cx, cz - 3.15, 1.00, "Marking_White", y=top + 0.003)
        add_text(p, "S4LV008", cx, cz - 1.10, 1.18, "Marking_White", y=top + 0.003)
        add_text(p, "KOREA 2342", cx, cz + 0.85, 0.62, "Marking_Gray", y=top + 0.003)
        add_text(p, "MZ-V9P1T0", cx, cz + 2.20, 0.52, "Marking_Gray", y=top + 0.003)
        add_datamatrix(p, cx + 4.15, cz + 4.15, top + 0.003, 0.86, "Marking_White", seed=11)
        add_cylinder(p, cx - 4.85, cz - 4.85, top, top + 0.008, 0.16, "Marking_Gray", 20)
    elif kind == "dram":
        add_text(p, "SEC 512", cx, cz - 2.85, 0.86, "Marking_White", y=top + 0.003)
        add_text(p, "K4F8E3S4HM", cx, cz - 1.10, 0.74, "Marking_White", y=top + 0.003)
        add_text(p, "MJG", cx, cz + 0.55, 0.52, "Marking_Gray", y=top + 0.003)
        add_datamatrix(p, cx + 2.85, cz + 3.85, top + 0.003, 0.62, "Marking_White", seed=22)
        add_cylinder(p, cx - 3.45, cz - 4.45, top, top + 0.008, 0.13, "Marking_Gray", 18)
    else:
        add_text(p, "SAMSUNG", cx, cz - 6.25, 1.28, "Marking_White", y=top + 0.003)
        add_text(p, "K9MKGY8J5A", cx, cz - 3.75, 1.02, "Marking_White", y=top + 0.003)
        add_text(p, "1TB", cx, cz - 1.15, 1.42, "Marking_White", y=top + 0.003)
        add_text(p, "MADE IN KOREA", cx, cz + 0.75, 0.62, "Marking_Gray", y=top + 0.003)
        add_text(p, "2348", cx, cz + 2.15, 0.55, "Marking_Gray", y=top + 0.003)
        add_datamatrix(p, cx + 5.05, cz + 7.05, top + 0.003, 1.05, "Marking_White", seed=33)
        add_cylinder(p, cx - 6.15, cz - 8.10, top, top + 0.008, 0.18, "Marking_Gray", 20)


def build_chips():
    for ref, ch in CHIPS.items():
        p = part(ch["name"])
        add_package(p, ch["cx"], ch["cz"], ch["w"], ch["d"], ch["h"],
                    "Chip_Black", corner=0.22, bevel=0.11)
        occupy(ch["name"], ch["cx"], ch["cz"], ch["w"], ch["d"], 0.15)
        chip_marking(ch)


def add_qfn(name: str, cx: float, cz: float, w: float, h: float = 0.56,
            pins: int = 8, seed: int = 1):
    p = part(name)
    add_package(p, cx, cz, w, w, h, "QFN_Body", corner=0.12, bevel=0.06)
    pin_w = 0.22
    pin_l = 0.52
    step = w / (pins + 1)
    for side in range(4):
        for i in range(pins):
            t = -w / 2 + step * (i + 1)
            if side == 0:
                add_box(p, cx + t, cz + w / 2 - 0.02, pin_w, pin_l,
                        PCB_T + 0.005, PCB_T + h - 0.06, "Solder")
            elif side == 1:
                add_box(p, cx + t, cz - w / 2 + 0.02, pin_w, pin_l,
                        PCB_T + 0.005, PCB_T + h - 0.06, "Solder")
            elif side == 2:
                add_box(p, cx - w / 2 + 0.02, cz + t, pin_l, pin_w,
                        PCB_T + 0.005, PCB_T + h - 0.06, "Solder")
            else:
                add_box(p, cx + w / 2 - 0.02, cz + t, pin_l, pin_w,
                        PCB_T + 0.005, PCB_T + h - 0.06, "Solder")
    occupy(name, cx, cz, w, w, 0.12)
    mk = part(name + "_Marking")
    top = PCB_T + h
    if w >= 4.2:
        add_text(mk, "S6AP", cx, cz - 0.55, 0.48, "Marking_White", y=top + 0.003)
        add_text(mk, "114A", cx, cz + 0.30, 0.42, "Marking_Gray", y=top + 0.003)
        add_datamatrix(mk, cx + w / 2 - 0.65, cz + w / 2 - 0.65,
                       top + 0.003, 0.42, "Marking_White", seed=seed)
    elif w >= 3.2:
        add_text(mk, "SIC", cx, cz - 0.25, 0.42, "Marking_White", y=top + 0.003)
        add_text(mk, "632", cx, cz + 0.35, 0.34, "Marking_Gray", y=top + 0.003)
    else:
        add_text(mk, "A1", cx, cz, 0.36, "Marking_White", y=top + 0.003)


def add_inductor(name: str, cx: float, cz: float, w: float = 3.5,
                 value: str = "2R2"):
    p = part(name)
    h = 1.65
    add_package(p, cx, cz, w, w, h, "Inductor_Body", corner=0.20, bevel=0.16,
                top_mat="Inductor_Top", side_mat="Inductor_Body")
    for s in (-1, 1):
        add_box(p, cx + s * (w / 2 - 0.13), cz, 0.34, w + 0.02,
                PCB_T + 0.01, PCB_T + h - 0.16, "Solder")
    occupy(name, cx, cz, w, w, 0.15)
    mk = part(name + "_Marking")
    add_text(mk, value, cx, cz, 0.62, "Marking_White", y=PCB_T + h + 0.003)
    add_line(mk, cx - 0.9, cz + 1.35, cx + 0.9, cz + 1.35, 0.08,
             "Marking_Gray", y=PCB_T + h + 0.003)


def add_mlcc(name: str, cx: float, cz: float, size: str = "0603",
             axis: str = "x"):
    dims = {"0402": (1.0, 0.5, 0.42), "0603": (1.6, 0.8, 0.62),
            "0805": (2.0, 1.25, 0.72), "1206": (3.2, 1.6, 0.85)}[size]
    w, d, h = dims
    if axis == "z":
        w, d = d, w
    p = part(name)
    term = max(0.18, w * 0.20)
    add_box(p, cx, cz, w - 2 * term + 0.02, d, PCB_T + 0.02, PCB_T + h, "Cap_Body")
    for s in (-1, 1):
        add_box(p, cx + s * (w / 2 - term / 2), cz, term, d,
                PCB_T + 0.005, PCB_T + h - 0.02, "Cap_Terminal")
    occupy(name, cx, cz, w, d, 0.10)


def add_resistor(name: str, cx: float, cz: float, size: str = "0402",
                 axis: str = "x", value: str | None = None):
    dims = {"0402": (1.0, 0.5, 0.40), "0603": (1.6, 0.8, 0.55)}[size]
    w, d, h = dims
    if axis == "z":
        w, d = d, w
    p = part(name)
    term = max(0.16, w * 0.22)
    add_box(p, cx, cz, w - 2 * term + 0.02, d, PCB_T + 0.02, PCB_T + h, "Res_Body")
    for s in (-1, 1):
        add_box(p, cx + s * (w / 2 - term / 2), cz, term, d,
                PCB_T + 0.005, PCB_T + h - 0.02, "Res_Terminal")
    if value and size == "0603":
        add_text(part(name + "_Marking"), value, cx, cz, 0.20,
                 "Marking_White", y=PCB_T + h + 0.002)
    occupy(name, cx, cz, w, d, 0.08)


def add_sot23(name: str, cx: float, cz: float, mark: str = "A1"):
    p = part(name)
    w, d, h = 2.9, 1.3, 1.0
    add_package(p, cx, cz, w, d, h, "Chip_Black", corner=0.10, bevel=0.06)
    for xoff in (-0.95, 0.95):
        add_box(p, cx + xoff, cz + d / 2 + 0.18, 0.42, 0.55,
                PCB_T + 0.01, PCB_T + 0.18, "Solder")
        add_box(p, cx + xoff, cz + d / 2 - 0.02, 0.42, 0.30,
                PCB_T + 0.01, PCB_T + 0.30, "Solder")
    add_box(p, cx, cz - d / 2 - 0.18, 0.55, 0.55,
            PCB_T + 0.01, PCB_T + 0.18, "Solder")
    add_box(p, cx, cz - d / 2 + 0.02, 0.30, 0.30,
            PCB_T + 0.01, PCB_T + 0.30, "Solder")
    occupy(name, cx, cz, w, d + 0.5, 0.10)
    add_text(part(name + "_Marking"), mark, cx, cz, 0.42,
             "Marking_White", y=PCB_T + h + 0.003)


def add_polymer(name: str, cx: float, cz: float, w: float = 4.0,
                d: float = 2.8):
    p = part(name)
    h = 1.05
    add_package(p, cx, cz, w, d, h, "Polymer_Body", corner=0.16, bevel=0.08,
                top_mat="Polymer_Top", side_mat="Polymer_Body")
    mk = part(name + "_Marking")
    add_text(mk, "220", cx, cz, 0.55, "Marking_Gray", y=PCB_T + h + 0.003)
    add_line(mk, cx - w / 2 + 0.55, cz - d / 2 + 0.35,
             cx + w / 2 - 0.55, cz - d / 2 + 0.35, 0.10,
             "Marking_Gray", y=PCB_T + h + 0.003)
    occupy(name, cx, cz, w, d, 0.12)


def add_crystal(name: str, cx: float, cz: float):
    p = part(name)
    w, d, h = 3.2, 2.5, 0.82
    add_package(p, cx, cz, w, d, h, "Crystal_Metal", corner=0.28, bevel=0.10)
    for s in (-1, 1):
        add_box(p, cx + s * (w / 2 - 0.20), cz, 0.40, d - 0.55,
                PCB_T + 0.005, PCB_T + 0.12, "Solder")
    occupy(name, cx, cz, w, d, 0.12)
    mk = part(name + "_Marking")
    add_text(mk, "24.000", cx, cz + 0.10, 0.46, "Marking_Gray",
             y=PCB_T + h + 0.003)
    add_cylinder(mk, cx - 1.15, cz - 0.82, PCB_T + h, PCB_T + h + 0.006,
                 0.11, "Marking_Gray", 16)


def add_testpoint(name: str, cx: float, cz: float, r: float = 0.58):
    p = part(name)
    add_cylinder(p, cx, cz, PCB_T + 0.001, PCB_T + 0.035, r, "Gold", 40)
    add_cylinder(p, cx, cz, PCB_T + 0.035, PCB_T + 0.039, r * 0.28,
                 "PCB_Dark", 20)
    occupy(name, cx, cz, 2 * r, 2 * r, 0.12)


def add_fiducial(name: str, cx: float, cz: float, r: float = 0.48):
    p = part(name)
    add_cylinder(p, cx, cz, PCB_T + 0.001, PCB_T + 0.022, r, "Gold", 40)
    occupy(name, cx, cz, 2 * r, 2 * r, 0.12)


def build_small_parts():
    add_qfn("U5_PMIC", 10.0, 7.5, 4.5, h=0.58, pins=8, seed=51)
    add_qfn("U6_PowerStage", 16.0, -8.6, 4.0, h=0.52, pins=7, seed=52)
    add_qfn("U7_Driver", 23.0, -8.8, 3.0, h=0.48, pins=6, seed=53)

    add_inductor("L1", 8.0, -7.8, 3.5, "2R2")
    add_inductor("L2", 11.6, -7.8, 3.5, "1R0")
    add_inductor("L3", 8.0, -1.5, 3.5, "2R2")
    add_inductor("L4", 8.0, 3.0, 3.5, "1R5")

    add_polymer("C1", 36.5, 8.0, 4.0, 2.8)
    add_polymer("C2", 36.5, -8.0, 4.0, 2.8)

    add_sot23("Q1", 15.0, 9.2, "A1")
    add_sot23("Q2", 18.5, 9.2, "A2")
    add_sot23("Q3", 22.0, 9.2, "A3")

    add_crystal("Y1", 27.0, 8.0)

    caps = [
        ("C3", 6.2, -10.3, "0603", "x"),
        ("C4", 6.2, -4.9, "0805", "x"),
        ("C6", 6.0, 10.1, "0603", "x"),
        ("C7", 13.0, 6.55, "0402", "x"),
        ("C8", 14.4, 6.55, "0402", "x"),
        ("C9", 15.8, 6.55, "0402", "x"),
        ("C10", 17.2, 6.55, "0402", "x"),
        ("C11", 18.6, 6.55, "0402", "x"),
        ("C12", 20.0, 6.55, "0402", "x"),
        ("C13", 21.4, 6.55, "0402", "x"),
        ("C14", 19.0, -6.65, "0402", "x"),
        ("C15", 20.3, -6.65, "0402", "x"),
        ("C16", 24.8, -6.65, "0402", "x"),
        ("C17", 26.0, -7.6, "0402", "x"),
        ("C18", 29.5, 6.25, "0402", "x"),
        ("C19", 31.0, 6.25, "0402", "x"),
        ("C20", 32.5, 6.25, "0402", "x"),
        ("C21", 40.0, 9.65, "0402", "x"),
        ("C22", 42.0, 9.65, "0402", "x"),
        ("C23", 56.0, 9.65, "0402", "x"),
        ("C24", 58.0, 9.65, "0402", "x"),
        ("C25", 69.8, -10.45, "0603", "x"),
        ("C26", 72.0, -10.45, "0603", "x"),
        ("C27", 10.4, 10.55, "0402", "x"),
        ("C28", 11.6, 10.55, "0402", "x"),
    ]
    dims = {"0402": (1.0, 0.5), "0603": (1.6, 0.8), "0805": (2.0, 1.25)}
    for nm, x, z, sz, ax in caps:
        w, d = dims[sz]
        if check_occ(nm, x, z, w, d, 0.1):
            add_mlcc(nm, x, z, sz, ax)

    res = [
        ("R1", 7.0, 6.15, "0402", "x", None),
        ("R2", 7.8, 10.45, "0402", "x", None),
        ("R3", 9.2, 10.45, "0402", "x", None),
        ("R4", 12.8, 10.45, "0402", "x", None),
        ("R5", 24.8, 10.45, "0402", "x", None),
        ("R6", 28.0, -6.55, "0402", "x", None),
        ("R7", 29.2, -6.55, "0402", "x", None),
        ("R8", 30.4, -6.55, "0402", "x", None),
        ("R9", 39.5, -9.65, "0402", "x", None),
        ("R10", 41.0, -9.65, "0402", "x", None),
        ("R11", 55.0, -9.65, "0402", "x", None),
        ("R12", 57.0, -9.65, "0402", "x", None),
        ("R13", 70.2, 9.65, "0603", "x", "103"),
        ("R14", 72.4, 9.65, "0603", "x", "472"),
    ]
    rdims = {"0402": (1.0, 0.5), "0603": (1.6, 0.8)}
    for nm, x, z, sz, ax, val in res:
        w, d = rdims[sz]
        if check_occ(nm, x, z, w, d, 0.08):
            add_resistor(nm, x, z, sz, ax, val)

    tps = [
        ("TP2", 26.0, -9.9), ("TP3", 75.0, 9.2),
        ("TP4", 69.8, -4.2), ("TP5", 75.6, 7.2), ("TP6", 74.2, -5.9),
    ]
    for nm, x, z in tps:
        if check_occ(nm, x, z, 1.16, 1.16, 0.1):
            add_testpoint(nm, x, z)
    fids = [("FID1", 5.4, -8.6), ("FID2", 37.0, 10.3), ("FID3", 76.8, -10.0)]
    for nm, x, z in fids:
        if check_occ(nm, x, z, 0.96, 0.96, 0.1):
            add_fiducial(nm, x, z)


# ----------------------------------------------------------------------------
# silkscreen
# ----------------------------------------------------------------------------
def outline_rect(p: Part, cx: float, cz: float, w: float, d: float,
                 mat: str = "Silkscreen", bottom: bool = False,
                 width: float = 0.10):
    y = -0.804 if bottom else 0.804
    x0, x1 = cx - w / 2, cx + w / 2
    z0, z1 = cz - d / 2, cz + d / 2
    add_line(p, x0, z0, x1, z0, width, mat, y=y, bottom=bottom)
    add_line(p, x1, z0, x1, z1, width, mat, y=y, bottom=bottom)
    add_line(p, x1, z1, x0, z1, width, mat, y=y, bottom=bottom)
    add_line(p, x0, z1, x0, z0, width, mat, y=y, bottom=bottom)


def build_silkscreen():
    top = part("Silkscreen_Top")
    bot = part("Silkscreen_Bottom")

    outline_rect(top, 18.5, 0, 12.9, 12.9)
    outline_rect(top, 31.0, 0, 9.9, 11.9)
    outline_rect(top, 45.5, 0, 14.9, 18.9)
    outline_rect(top, 61.5, 0, 14.9, 18.9)
    outline_rect(top, 10.0, 7.5, 5.4, 5.4)
    outline_rect(top, 16.0, -8.6, 4.5, 4.5)
    outline_rect(top, 23.0, -8.8, 3.9, 3.9)
    outline_rect(top, 27.0, 8.0, 3.9, 3.2)
    for x, z, w in ((8.0, -7.8, 3.5), (11.6, -7.8, 3.5),
                    (8.0, -1.5, 3.5), (8.0, 3.0, 3.5)):
        outline_rect(top, x, z, w + 0.5, w + 0.5)

    add_line(top, 4.95, -10.3, 4.95, KEY_Z0 - 0.25, 0.10, "Silkscreen")
    add_line(top, 4.95, KEY_Z1 + 0.25, 4.95, 10.3, 0.10, "Silkscreen")
    add_line(top, KEY_X + 0.12, KEY_Z0 - 0.05, KEY_X + 0.12, KEY_Z1 + 0.05,
             0.10, "Silkscreen")

    labels = [
        ("J1", 5.55, 10.55, 0.58, 0),
        ("U1", 12.1, -7.05, 0.68, 0),
        ("U2", 26.0, -6.75, 0.68, 0),
        ("U3", 38.0, -10.25, 0.68, 0),
        ("U4", 54.0, -10.25, 0.68, 0),
        ("U5", 7.6, 4.75, 0.60, 0),
        ("U6", 13.6, -10.55, 0.55, 0),
        ("U7", 20.6, -10.55, 0.55, 0),
        ("Y1", 29.4, 10.3, 0.55, 0),
        ("L1", 7.2, -5.95, 0.55, 0),
        ("L2", 11.2, -5.95, 0.55, 0),
        ("L3", 7.2, 0.45, 0.55, 0),
        ("L4", 7.2, 4.95, 0.55, 0),
        ("C1", 34.1, 9.9, 0.50, 0),
        ("C2", 34.1, -9.9, 0.50, 0),
    ]
    for txt, x, z, h, rot in labels:
        add_text(top, txt, x, z, h, "Silkscreen", y=0.804, bold=True,
                 align="center", rot=rot)

    add_text(top, "M.2 2280", 5.55, 0.0, 0.78, "Silkscreen", y=0.804,
             bold=True, align="center", rot=90)
    add_text(top, "PCIe Gen4 x4", 5.55, 7.4, 0.55, "Silkscreen", y=0.804,
             bold=True, align="center", rot=90)

    add_text(top, "SSD 990 PRO", 72.35, -8.55, 0.72, "Silkscreen", y=0.804,
             bold=True, align="center")
    add_text(top, "1TB", 72.35, -7.25, 0.82, "Silkscreen", y=0.804,
             bold=True, align="center")
    add_text(top, "M.2 2280", 72.15, 5.25, 0.50, "Silkscreen", y=0.804,
             bold=False, align="center")
    add_text(top, "PCIe Gen4 x4", 72.15, 6.05, 0.46, "Silkscreen", y=0.804,
             bold=False, align="center")
    add_text(top, "MADE IN KOREA", 72.15, 6.85, 0.42, "Silkscreen", y=0.804,
             bold=False, align="center")

    add_text(bot, "SAMSUNG", 40, -7.2, 2.6, "Silkscreen", y=-0.804,
             bold=True, align="center", bottom=True)
    add_text(bot, "SSD 990 PRO", 40, -3.4, 1.9, "Silkscreen", y=-0.804,
             bold=True, align="center", bottom=True)
    add_text(bot, "1TB", 40, 1.0, 2.7, "Silkscreen", y=-0.804,
             bold=True, align="center", bottom=True)
    add_text(bot, "M.2 2280   PCIe Gen4 x4", 40, 4.8, 0.95, "Silkscreen",
             y=-0.804, bold=False, align="center", bottom=True)
    add_text(bot, "MADE IN KOREA", 40, 6.7, 0.72, "Silkscreen", y=-0.804,
             bold=False, align="center", bottom=True)
    add_text(bot, "MZ-V9P1T0", 40, -9.6, 0.72, "Silkscreen", y=-0.804,
             bold=False, align="center", bottom=True)
    add_text(bot, "www.samsung.com/ssd", 40, 8.5, 0.62, "Silkscreen",
             y=-0.804, bold=False, align="center", bottom=True)
    add_text(bot, "CE", 70.0, 6.0, 1.05, "Silkscreen", y=-0.804,
             bold=True, align="center", bottom=True)
    add_text(bot, "FC", 74.5, 6.0, 0.95, "Silkscreen", y=-0.804,
             bold=True, align="center", bottom=True)
    add_text(bot, "M.2", 70.5, -6.2, 1.0, "Silkscreen", y=-0.804,
             bold=True, align="center", bottom=True)


# ----------------------------------------------------------------------------
# export
# ----------------------------------------------------------------------------
def _face_normal(verts, face):
    a = np.asarray(verts[face[0]])
    b = np.asarray(verts[face[1]])
    c = np.asarray(verts[face[2]])
    n = np.cross(b - a, c - a)
    ln = np.linalg.norm(n)
    if ln < 1e-12:
        return np.array([0.0, 1.0, 0.0])
    return n / ln


def write_obj_mtl(parts: dict[str, Part], obj_path: Path, mtl_path: Path):
    mtl_lines = ["# M.2 2280 NVMe SSD - procedural materials", ""]
    for name, (kd, ks, ns, metal) in MATERIALS.items():
        r, g, b = hex_rgb(kd)
        sr, sg, sb = hex_rgb(ks)
        mtl_lines += [
            f"newmtl {name}",
            f"Kd {r:.6f} {g:.6f} {b:.6f}",
            f"Ka {r*0.12:.6f} {g*0.12:.6f} {b*0.12:.6f}",
            f"Ks {sr:.6f} {sg:.6f} {sb:.6f}",
            f"Ns {ns:.3f}",
            "Ni 1.450000",
            "d 1.000000",
            "illum 2",
            "",
        ]
    mtl_path.write_text("\n".join(mtl_lines), encoding="utf-8")

    obj = [
        "# M.2 2280 NVMe SSD (bare PCB, no label sticker)",
        "# Units: millimetres. X length 0..80, Y thickness, Z width -11..11.",
        f"mtllib {mtl_path.name}",
        "",
    ]
    total_v = total_f = 0
    v_off = 0
    vn_off = 0
    for pname, p in parts.items():
        if not p.faces:
            continue
        obj.append(f"o {pname}")
        obj.append("s off")
        for v in p.verts:
            obj.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
        order = []
        groups: dict[str, list[tuple[int, ...]]] = {}
        for mat, face in p.faces:
            if mat not in groups:
                groups[mat] = []
                order.append(mat)
            groups[mat].append(face)
        vn_lines = []
        face_lines = []
        for mat in order:
            face_lines.append(f"usemtl {mat}")
            for face in groups[mat]:
                n = _face_normal(p.verts, face)
                vn_lines.append(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}")
                ni = vn_off + len(vn_lines)
                face_lines.append(
                    "f " + " ".join(f"{v_off + i + 1}//{ni}" for i in face))
                total_f += 1
        obj.extend(vn_lines)
        obj.extend(face_lines)
        obj.append("")
        total_v += len(p.verts)
        v_off += len(p.verts)
        vn_off += len(vn_lines)
    obj_path.write_text("\n".join(obj), encoding="utf-8")
    print(f"wrote {obj_path} ({obj_path.stat().st_size/1e6:.2f} MB), "
          f"{len(parts)} objects, {total_v} verts, {total_f} faces")


def main():
    build_pcb()
    build_edge_contacts()
    build_screw_ring()
    build_chips()
    build_small_parts()
    build_silkscreen()

    print("\nParts:")
    for name, p in PARTS.items():
        if not p.verts:
            continue
        lo, hi = p.bounds()
        print(f"  {name:24s} v={len(p.verts):7d} f={len(p.faces):7d} "
              f"x[{lo[0]:6.2f},{hi[0]:6.2f}] y[{lo[1]:6.3f},{hi[1]:6.3f}] "
              f"z[{lo[2]:6.2f},{hi[2]:6.2f}]")

    write_obj_mtl(PARTS, OUT / "m2_ssd_2280.obj", OUT / "m2_ssd_2280.mtl")


if __name__ == "__main__":
    main()
