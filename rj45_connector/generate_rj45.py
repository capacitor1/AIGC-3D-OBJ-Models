#!/usr/bin/env python3
"""
Procedural, dimension-accurate RJ45 (8P8C) shielded PCB jack with two LEDs.
Units: millimetres.  Y is up, the port opening faces +Z, PCB plane is Y=0.

Outputs:
    rj45_connector.obj
    rj45_connector.mtl
"""
import math
import os

import numpy as np

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------------------
# Materials
# ----------------------------------------------------------------------------
MATERIALS = {
    # name:        (Kd,                    Ks,                  Ns,  d,   Ke)
    "Shield":      ((0.700, 0.715, 0.735), (0.95, 0.95, 0.95), 240, 1.0, (0.0, 0.0, 0.0)),
    "ShieldEdge":  ((0.560, 0.575, 0.595), (0.90, 0.90, 0.90), 180, 1.0, (0.0, 0.0, 0.0)),
    "ShieldInner": ((0.300, 0.310, 0.325), (0.60, 0.60, 0.60), 100, 1.0, (0.0, 0.0, 0.0)),
    "PlasticBlack":((0.030, 0.031, 0.034), (0.30, 0.30, 0.30),  55, 1.0, (0.0, 0.0, 0.0)),
    "PlasticDark": ((0.075, 0.076, 0.082), (0.25, 0.25, 0.25),  40, 1.0, (0.0, 0.0, 0.0)),
    "PlasticGrey": ((0.160, 0.162, 0.170), (0.30, 0.30, 0.30),  45, 1.0, (0.0, 0.0, 0.0)),
    "Gold":        ((0.930, 0.700, 0.270), (1.00, 0.92, 0.72), 420, 1.0, (0.0, 0.0, 0.0)),
    "GoldTip":     ((1.000, 0.820, 0.380), (1.00, 0.96, 0.82), 520, 1.0, (0.02, 0.015, 0.0)),
    "Tin":         ((0.800, 0.805, 0.815), (0.85, 0.85, 0.85), 260, 1.0, (0.0, 0.0, 0.0)),
    "LEDGreen":    ((0.180, 0.900, 0.320), (0.55, 0.90, 0.55), 300, 1.0, (0.030, 0.420, 0.070)),
    "LEDGreenHot": ((0.500, 1.000, 0.520), (0.70, 1.00, 0.70), 350, 1.0, (0.120, 0.900, 0.180)),
    "LEDAmber":    ((1.000, 0.520, 0.045), (0.90, 0.70, 0.35), 300, 1.0, (0.450, 0.160, 0.000)),
    "LEDAmberHot": ((1.000, 0.760, 0.240), (1.00, 0.85, 0.55), 350, 1.0, (1.000, 0.430, 0.030)),
    "ClearLens":   ((0.780, 0.850, 0.830), (0.80, 0.85, 0.85), 380, 1.0, (0.010, 0.020, 0.015)),
    "WireGreen":   ((0.070, 0.420, 0.120), (0.35, 0.45, 0.35),  80, 1.0, (0.0, 0.0, 0.0)),
    "WireAmber":   ((0.700, 0.300, 0.020), (0.45, 0.35, 0.25),  80, 1.0, (0.0, 0.0, 0.0)),
    "PCB":         ((0.035, 0.180, 0.090), (0.20, 0.30, 0.25),  60, 1.0, (0.0, 0.0, 0.0)),
}

MAT_ORDER = list(MATERIALS.keys())


# ----------------------------------------------------------------------------
# Mesh container
# ----------------------------------------------------------------------------
class Mesh:
    def __init__(self):
        self.verts = []
        self.vindex = {}
        self.faces = []          # (tuple_of_vertex_indices, material)

    def _v(self, p):
        key = (round(float(p[0]), 6), round(float(p[1]), 6), round(float(p[2]), 6))
        idx = self.vindex.get(key)
        if idx is None:
            idx = len(self.verts)
            self.vindex[key] = idx
            self.verts.append((float(p[0]), float(p[1]), float(p[2])))
        return idx

    @staticmethod
    def _normal(pts):
        n = np.zeros(3)
        for i, p in enumerate(pts):
            q = pts[(i + 1) % len(pts)]
            n[0] += (p[1] - q[1]) * (p[2] + q[2])
            n[1] += (p[2] - q[2]) * (p[0] + q[0])
            n[2] += (p[0] - q[0]) * (p[1] + q[1])
        ln = np.linalg.norm(n)
        if ln < 1e-12:
            return None
        return n / ln

    def add_poly(self, pts, mat, ref=None):
        pts = [np.asarray(p, dtype=float) for p in pts]
        n = self._normal(pts)
        if n is None:
            return
        if ref is not None:
            c = np.mean(pts, axis=0)
            if np.dot(n, c - np.asarray(ref, dtype=float)) < 0.0:
                pts.reverse()
        idx = [self._v(p) for p in pts]
        if len(set(idx)) < 3:
            return
        self.faces.append((tuple(idx), mat))

    # ------------------------------------------------------------------
    def box(self, center, size, mat, bevel=0.0, rot=None):
        """Beveled box (truncated-cube topology).  rot = (rx,ry,rz) degrees."""
        cx, cy, cz = center
        ax, ay, az = (s * 0.5 for s in size)
        t = float(bevel)
        if t <= 0.0:
            t = 0.0
        if t > 0.0:
            t = min(t, ax * 0.49, ay * 0.49, az * 0.49)
            faces = []
            # six inset faces
            for axis in range(3):
                others = [j for j in range(3) if j != axis]
                for s in (-1.0, 1.0):
                    pts = []
                    for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                        p = [0.0, 0.0, 0.0]
                        p[axis] = s * (ax, ay, az)[axis]
                        p[others[0]] = u * ((ax, ay, az)[others[0]] - t)
                        p[others[1]] = v * ((ax, ay, az)[others[1]] - t)
                        pts.append(p)
                    faces.append(pts)
            # twelve edge bevels
            for i in range(3):
                for j in range(i + 1, 3):
                    k = 3 - i - j
                    for si in (-1.0, 1.0):
                        for sj in (-1.0, 1.0):
                            pts = []
                            for sk in (-1.0, 1.0):
                                p1 = [0.0, 0.0, 0.0]
                                p1[i] = si * (ax, ay, az)[i]
                                p1[j] = sj * ((ax, ay, az)[j] - t)
                                p1[k] = sk * ((ax, ay, az)[k] - t)
                                p2 = [0.0, 0.0, 0.0]
                                p2[i] = si * ((ax, ay, az)[i] - t)
                                p2[j] = sj * (ax, ay, az)[j]
                                p2[k] = sk * ((ax, ay, az)[k] - t)
                                if sk < 0:
                                    pts.extend([p1, p2])
                                else:
                                    pts.extend([p2, p1])
                            faces.append(pts)
            # eight corner triangles
            for sx in (-1.0, 1.0):
                for sy in (-1.0, 1.0):
                    for sz in (-1.0, 1.0):
                        faces.append([
                            (sx * (ax - t), sy * ay, sz * az),
                            (sx * ax, sy * (ay - t), sz * az),
                            (sx * ax, sy * ay, sz * (az - t)),
                        ])
        else:
            faces = []
            for axis in range(3):
                others = [j for j in range(3) if j != axis]
                for s in (-1.0, 1.0):
                    pts = []
                    for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                        p = [0.0, 0.0, 0.0]
                        p[axis] = s * (ax, ay, az)[axis]
                        p[others[0]] = u * (ax, ay, az)[others[0]]
                        p[others[1]] = v * (ax, ay, az)[others[1]]
                        pts.append(p)
                    faces.append(pts)

        if rot is not None:
            rx, ry, rz = (math.radians(a) for a in rot)
            Rx = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
            Ry = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
            Rz = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
            R = Rz @ Ry @ Rx
        else:
            R = None
        for f in faces:
            out = []
            for p in f:
                q = np.array(p)
                if R is not None:
                    q = R @ q
                out.append(q + np.array((cx, cy, cz)))
            self.add_poly(out, mat, ref=(cx, cy, cz))

    # ------------------------------------------------------------------
    def cylinder(self, p0, p1, r0, mat, seg=20, r1=None, cap_mat=None, bevel=0.0):
        p0 = np.asarray(p0, dtype=float)
        p1 = np.asarray(p1, dtype=float)
        if r1 is None:
            r1 = r0
        axis = p1 - p0
        L = np.linalg.norm(axis)
        if L < 1e-9:
            return
        axis = axis / L
        helper = np.array([0.0, 1.0, 0.0])
        if abs(np.dot(axis, helper)) > 0.95:
            helper = np.array([1.0, 0.0, 0.0])
        u = np.cross(axis, helper)
        u /= np.linalg.norm(u)
        v = np.cross(axis, u)
        ref = (p0 + p1) * 0.5
        ring0 = []
        ring1 = []
        for i in range(seg):
            a = 2.0 * math.pi * i / seg
            d = math.cos(a) * u + math.sin(a) * v
            ring0.append(p0 + d * r0)
            ring1.append(p1 + d * r1)
        for i in range(seg):
            j = (i + 1) % seg
            self.add_poly([ring0[i], ring0[j], ring1[j], ring1[i]], mat, ref=ref)
        if cap_mat is not False:
            cm = cap_mat if cap_mat is not None else mat
            self.add_poly(list(reversed(ring0)), cm, ref=ref)
            self.add_poly(list(ring1), cm, ref=ref)

    # ------------------------------------------------------------------
    def wedge(self, center, size, mat, bevel=0.0):
        """Simple triangular prism, long axis X, for the latch tooth."""
        cx, cy, cz = center
        ax, ay, az = (s * 0.5 for s in size)
        pts = [
            (-ax, -ay, -az), (-ax, -ay, az), (-ax, ay, az),
            (ax, -ay, -az), (ax, -ay, az), (ax, ay, az),
        ]
        faces = [
            [pts[0], pts[1], pts[2]],
            [pts[3], pts[5], pts[4]],
            [pts[0], pts[3], pts[4], pts[1]],
            [pts[1], pts[4], pts[5], pts[2]],
            [pts[0], pts[2], pts[5], pts[3]],
        ]
        for f in faces:
            self.add_poly([np.array(p) + np.array((cx, cy, cz)) for p in f], mat, ref=(cx, cy, cz))

    # ------------------------------------------------------------------
    def write_obj(self, obj_path, mtl_name):
        lines = ["# RJ45 (8P8C) shielded jack with dual LEDs",
                 "# units: millimetres, Y-up, port faces +Z",
                 "mtllib " + mtl_name]
        for v in self.verts:
            lines.append("v %.5f %.5f %.5f" % v)
        # flat per-face normals
        normals = []
        face_vn = []
        for idxs, mat in self.faces:
            pts = [np.array(self.verts[i]) for i in idxs]
            n = self._normal(pts)
            if n is None:
                face_vn.append(None)
                continue
            normals.append(n)
            face_vn.append(len(normals))
        for n in normals:
            lines.append("vn %.5f %.5f %.5f" % tuple(n))
        cur = None
        for (idxs, mat), vn in zip(self.faces, face_vn):
            if vn is None:
                continue
            if mat != cur:
                lines.append("usemtl " + mat)
                cur = mat
            lines.append("f " + " ".join("%d//%d" % (i + 1, vn) for i in idxs))
        with open(obj_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def write_mtl(self, path):
        out = ["# RJ45 materials"]
        for name in MAT_ORDER:
            kd, ks, ns, d, ke = MATERIALS[name]
            out.append("newmtl " + name)
            out.append("Ka %.4f %.4f %.4f" % tuple(x * 0.35 for x in kd))
            out.append("Kd %.4f %.4f %.4f" % kd)
            out.append("Ks %.4f %.4f %.4f" % ks)
            out.append("Ns %.1f" % ns)
            out.append("Ke %.4f %.4f %.4f" % ke)
            out.append("Ni 1.45")
            out.append("d %.3f" % d)
            out.append("illum 2")
            out.append("")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(out))


# ----------------------------------------------------------------------------
# Model constants
# ----------------------------------------------------------------------------
W = 13.60            # overall width
H = 13.50            # overall height
D = 16.20            # overall depth
HX = W / 2.0
T = 0.28             # sheet metal thickness

OPEN_HX = 5.55       # half width of front opening
OPEN_Y0 = 1.45
OPEN_Y1 = 9.00
Z_FRONT = 0.0
Z_BACK = -D

CAV_HX = 5.55
CAV_Y0 = 1.45
CAV_Y1 = 9.00
CAV_BACK = -8.35
CAV_FRONT = -0.62

PITCH = 1.27


def build():
    m = Mesh()

    # =====================================================================
    # 1.  Outer nickel-plated steel shield
    # =====================================================================
    # ---- front frame -----------------------------------------------------
    m.box((0, OPEN_Y0 / 2, -T / 2), (W, OPEN_Y0, T), "Shield", 0.10)
    m.box((0, (OPEN_Y1 + H) / 2, -T / 2), (W, H - OPEN_Y1, T), "Shield", 0.10)
    side_w = HX - OPEN_HX
    for s in (-1, 1):
        m.box((s * (OPEN_HX + side_w / 2), (OPEN_Y0 + OPEN_Y1) / 2, -T / 2),
              (side_w, OPEN_Y1 - OPEN_Y0, T), "Shield", 0.10)

    # folded returns at the top and bottom of the opening
    m.box((0, OPEN_Y1 - 0.11, -0.48), (2 * OPEN_HX, 0.22, 0.62), "ShieldEdge", 0.05)
    m.box((0, OPEN_Y0 + 0.11, -0.48), (2 * OPEN_HX, 0.22, 0.62), "ShieldEdge", 0.05)

    # small folded latch tab hanging from the top edge of the opening
    m.box((0, OPEN_Y1 - 0.24, -0.19), (1.42, 0.48, 0.22), "Shield", 0.05)
    m.box((0, OPEN_Y1 - 0.49, -0.28), (1.16, 0.12, 0.20),
          "ShieldEdge", 0.03, rot=(28, 0, 0))
    m.box((0, OPEN_Y1 - 0.31, -0.40), (1.72, 0.64, 0.06), "PlasticBlack", 0.02)

    # ---- side walls ------------------------------------------------------
    for s in (-1, 1):
        m.box((s * (HX - T / 2), H / 2, Z_BACK / 2), (T, H, D), "Shield", 0.09)
        # panel seam (front / rear stamping)
        m.box((s * (HX + 0.006), 6.55, -6.55), (0.02, 12.9, 0.075), "ShieldEdge", 0.0)
        # small side latch window near the bottom rear (flush, framed)
        m.box((s * (HX + 0.006), 1.55, -12.85), (0.012, 0.98, 1.62), "PlasticBlack", 0.0)
        for dz in (-0.86, 0.86):
            m.box((s * (HX + 0.012), 1.55, -12.85 + dz), (0.016, 1.10, 0.10), "ShieldEdge", 0.0)
        for dy in (-0.54, 0.54):
            m.box((s * (HX + 0.012), 1.55 + dy, -12.85), (0.016, 0.10, 1.82), "ShieldEdge", 0.0)
        m.box((s * (HX + 0.018), 1.55, -12.85), (0.012, 0.42, 0.92), "ShieldInner", 0.0)
        m.box((s * (HX + 0.026), 1.55, -12.85), (0.010, 0.24, 0.62), "PlasticBlack", 0.0)

    # ---- top (two stampings with a visible seam / step) ------------------
    m.box((0, H - 0.16, -11.35), (W, 0.32, 9.55), "Shield", 0.10)
    m.box((0, H - 0.13, -3.31), (W, 0.34, 6.48), "Shield", 0.10)
    m.box((0, H + 0.005, -6.56), (W - 0.12, 0.045, 0.13), "ShieldInner", 0.0)
    # two little folded tabs on the top near the front
    for s in (-1, 1):
        m.box((s * 2.65, H + 0.035, -1.25), (1.35, 0.10, 1.35), "ShieldEdge", 0.04)
    # fold / seam line around the front face
    for s in (-1, 1):
        m.box((s * 6.685, H / 2, 0.008), (0.020, H - 0.30, 0.010), "ShieldInner", 0.0)
    m.box((0, H - 0.155, 0.008), (W - 0.30, 0.020, 0.010), "ShieldInner", 0.0)
    m.box((0, H - 0.36, 0.008), (W - 0.55, 0.016, 0.010), "ShieldInner", 0.0)
    # folded front lip of the top stamping
    m.box((0, H - 0.16, 0.035), (W - 0.05, 0.32, 0.09), "Shield", 0.06)
    m.box((0, H - 0.33, 0.012), (W - 0.20, 0.05, 0.020), "ShieldInner", 0.0)
    # rear seam lip
    m.box((0, H - 0.30, -15.93), (W - 0.15, 0.10, 0.18), "ShieldEdge", 0.0)

    # ---- back wall -------------------------------------------------------
    m.box((0, H / 2, Z_BACK + T / 2), (W, H, T), "Shield", 0.10)
    m.box((0, H / 2, Z_BACK + T + 0.02), (W - 0.30, H - 0.30, 0.06), "ShieldInner", 0.0)

    # ---- bottom flanges --------------------------------------------------
    for s in (-1, 1):
        m.box((s * (HX - 0.44), 0.16, Z_BACK / 2 + 0.1), (0.88, 0.32, D - 0.2), "Shield", 0.08)
    m.box((0, 0.16, Z_BACK + 0.62), (W - 0.4, 0.32, 1.05), "Shield", 0.08)

    # ---- board hold-down legs -------------------------------------------
    for s in (-1, 1):
        for z in (-2.05, -14.45):
            m.box((s * (HX - T / 2), -1.10, z), (T, 2.9, 1.55), "Shield", 0.05)
            m.box((s * (HX - T / 2 - 0.12), -2.52, z + 0.28), (T + 0.24, 0.16, 1.05), "ShieldEdge", 0.02)
    for s in (-1, 1):
        m.box((s * 2.85, -0.90, Z_BACK + T / 2), (1.35, 2.6, T), "Shield", 0.05)

    # ---- side spring (grounding) tabs ------------------------------------
    for s in (-1, 1):
        m.box((s * (HX + 0.16), 6.55, -10.60), (0.115, 1.05, 2.55),
              "ShieldEdge", 0.035, rot=(0, -s * 11.0, 0))
        m.box((s * (HX + 0.045), 6.55, -9.42), (0.10, 0.95, 0.55), "ShieldEdge", 0.02)
        m.box((s * (HX + 0.10), 6.55, -8.00), (0.10, 0.78, 0.95),
              "ShieldEdge", 0.03, rot=(0, -s * 8.0, 0))

    # =====================================================================
    # 2.  Black plastic housing / inner cavity
    # =====================================================================
    wall_x = 0.90
    # side walls
    for s in (-1, 1):
        m.box((s * (CAV_HX + wall_x / 2), H / 2, (Z_BACK + 0.3 + CAV_FRONT) / 2),
              (wall_x, H - 0.3, abs(Z_BACK + 0.3 - CAV_FRONT)), "PlasticBlack", 0.12)
    # cavity floor
    m.box((0, (0.28 + CAV_Y0) / 2, (Z_BACK + 0.3 + CAV_FRONT) / 2),
          (2 * CAV_HX, CAV_Y0 - 0.28, abs(Z_BACK + 0.3 - CAV_FRONT)), "PlasticBlack", 0.10)
    # cavity ceiling
    m.box((0, (CAV_Y1 + H - 0.28) / 2, (Z_BACK + 0.3 + CAV_FRONT) / 2),
          (2 * CAV_HX, H - 0.28 - CAV_Y1, abs(Z_BACK + 0.3 - CAV_FRONT)), "PlasticBlack", 0.10)
    # cavity back wall
    m.box((0, (CAV_Y0 + CAV_Y1) / 2, CAV_BACK - 0.28),
          (2 * CAV_HX, CAV_Y1 - CAV_Y0, 0.56), "PlasticBlack", 0.10)
    # solid rear body (mostly hidden by shield)
    m.box((0, H / 2 - 0.05, (Z_BACK + 0.5 + CAV_BACK) / 2),
          (W - 0.7, H - 0.55, abs(Z_BACK + 0.5 - CAV_BACK)), "PlasticBlack", 0.18)

    # front black bezel just behind the metal return
    for s in (-1, 1):
        m.box((s * (CAV_HX - 0.16), (CAV_Y0 + CAV_Y1) / 2, CAV_FRONT + 0.08),
              (0.32, CAV_Y1 - CAV_Y0, 0.16), "PlasticBlack", 0.03)
    m.box((0, CAV_Y1 - 0.10, CAV_FRONT + 0.08), (2 * CAV_HX, 0.20, 0.16), "PlasticBlack", 0.03)
    m.box((0, CAV_Y0 + 0.10, CAV_FRONT + 0.08), (2 * CAV_HX, 0.20, 0.16), "PlasticBlack", 0.03)

    # cavity floor top skin + contact separating ridges
    m.box((0, CAV_Y0 + 0.030, (CAV_FRONT + CAV_BACK) / 2),
          (2 * CAV_HX, 0.060, abs(CAV_FRONT - CAV_BACK)), "PlasticBlack", 0.02)
    for i in range(9):
        x = -5.08 + i * PITCH
        m.box((x, CAV_Y0 + 0.060, -5.10), (0.090, 0.12, 4.60), "PlasticBlack", 0.020)
    # a shallow wire channel at the back of the floor
    m.box((0, CAV_Y0 + 0.06, -7.55), (2 * CAV_HX - 0.25, 0.12, 0.95), "PlasticDark", 0.03)

    # latch tooth at the top centre of the port
    m.box((0, 8.08, -0.78), (1.88, 1.10, 0.86), "PlasticBlack", 0.15)
    m.box((0, 7.60, -0.66), (1.34, 0.26, 0.58), "PlasticDark", 0.07)


    # =====================================================================
    # 3.  LED light pipes / lenses  (green left, amber right)
    # =====================================================================
    lens_y0, lens_y1 = 7.52, 8.80
    lens_specs = [
        (-1, -5.42, -3.98, "LEDGreen", "LEDGreenHot", "WireGreen"),
        (1, 3.98, 5.42, "LEDAmber", "LEDAmberHot", "WireAmber"),
    ]
    # recessed black header between the two windows
    m.box((0, (lens_y0 + lens_y1) / 2, -0.78), (7.96, lens_y1 - lens_y0, 0.34),
          "PlasticBlack", 0.05)
    for s, x0, x1, lensmat, hotmat, wiremat in lens_specs:
        cx = (x0 + x1) / 2
        w = x1 - x0
        h = lens_y1 - lens_y0
        cy = (lens_y0 + lens_y1) / 2
        # black bezel frame (four thin strips, slightly proud)
        for dx in (-w / 2 + 0.05, w / 2 - 0.05):
            m.box((cx + dx, cy, -0.030), (0.10, h, 0.09), "PlasticBlack", 0.02)
        for dy in (-h / 2 + 0.05, h / 2 - 0.05):
            m.box((cx, cy + dy, -0.030), (w - 0.18, 0.10, 0.09), "PlasticBlack", 0.02)
        # dark rim behind the diffuser
        m.box((cx, cy, -0.39), (w - 0.22, h - 0.22, 0.06), wiremat, 0.02)
        # coloured diffuser
        m.box((cx, cy, -0.35), (w - 0.30, h - 0.30, 0.11), lensmat, 0.055)
        # bright die behind the diffuser
        m.box((cx, cy, -0.48), (0.54, 0.54, 0.10), hotmat, 0.04)
        # light pipe running back into the housing
        m.box((cx, cy, -1.06), (w - 0.30, h - 0.30, 0.92), "ClearLens", 0.09)
        # LED package inside
        m.box((cx, cy, -1.57), (0.66, 0.46, 0.28), "PlasticBlack", 0.04)
        m.box((cx, cy, -1.57), (0.50, 0.32, 0.31), hotmat, 0.035)
        # two hair-thin gold bond wires
        for dx in (-0.18, 0.18):
            m.cylinder((cx + dx, cy, -1.70), (cx + dx, cy, -1.42), 0.032, "Gold", 8)
        # short coloured lead stubs disappearing into the plastic ceiling
        m.cylinder((cx - 0.24, 8.52, -1.55), (cx - 0.24, 9.22, -1.55), 0.09, wiremat, 8)
        m.cylinder((cx + 0.24, 8.52, -1.55), (cx + 0.24, 9.22, -1.55), 0.09, wiremat, 8)

    # =====================================================================
    # 4.  Eight gold-plated spring contacts
    # =====================================================================
    for i in range(8):
        x = -4.445 + i * PITCH
        hw = 0.170

        # rising section (22.6 deg)
        m.box((x, 2.175, -3.925), (2 * hw, 0.110, 3.96),
              "Gold", 0.026, rot=(22.6, 0, 0))
        # slightly upturned rounded contact tip
        m.box((x, 2.965, -2.02), (2 * hw - 0.06, 0.090, 0.20),
              "Gold", 0.045, rot=(22.6, 0, 0))


    # =====================================================================
    # 5.  Through-hole pins
    # =====================================================================
    # --- 8 signal pins, two staggered rows ---
    sig = [(-3.81, -13.35), (-1.27, -13.35), (1.27, -13.35), (3.81, -13.35),
           (-5.08, -14.62), (-2.54, -14.62), (0.00, -14.62), (2.54, -14.62)]
    for x, z in sig:
        m.box((x, -1.18, z), (0.55, 3.25, 0.55), "Tin", 0.07)
        m.box((x, 0.12, z), (0.72, 0.42, 0.72), "Tin", 0.06)
        m.box((x, -2.72, z), (0.42, 0.30, 0.42), "Tin", 0.07)
        # tiny solder fillet ring at board level
        m.cylinder((x, -0.05, z), (x, 0.20, z), 0.40, "Tin", 14, r1=0.30)

    # --- 4 LED pins, coloured at the top to identify the two LEDs ---
    led_pins = [(-4.60, "WireGreen"), (-3.33, "WireGreen"),
                (3.33, "WireAmber"), (4.60, "WireAmber")]
    for x, colmat in led_pins:
        m.cylinder((x, -2.48, -15.25), (x, -0.25, -15.25), 0.275, "Tin", 14)
        m.cylinder((x, -0.25, -15.25), (x, 0.16, -15.25), 0.315, colmat, 14)
        m.cylinder((x, 0.16, -15.25), (x, 0.42, -15.25), 0.36, "PlasticBlack", 14)
        m.cylinder((x, -2.48, -15.25), (x, -2.62, -15.25), 0.22, "Tin", 12, r1=0.16)

    # =====================================================================
    # 6.  Plastic mounting posts (board locating pegs)
    # =====================================================================
    for s in (-1, 1):
        x = s * 4.95
        m.cylinder((x, 0.50, -2.30), (x, -2.20, -2.30), 1.45, "PlasticBlack", 24, r1=1.22)
        m.cylinder((x, -2.20, -2.30), (x, -2.42, -2.30), 1.22, "PlasticBlack", 24, r1=0.98)
        m.cylinder((x, 0.50, -2.30), (x, 0.62, -2.30), 1.56, "PlasticDark", 24, r1=1.45)
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            m.box((x + math.cos(a) * 1.30, -0.55, -2.30 + math.sin(a) * 1.30),
                  (0.18, 1.15, 0.18), "PlasticDark", 0.03)

    # =====================================================================
    # 7.  Small internal / assembly details
    # =====================================================================
    # rear contact block with 8 small ridges
    for i in range(8):
        x = -4.445 + i * PITCH
        m.box((x, 1.78, -8.02), (0.34, 0.30, 0.42), "PlasticGrey", 0.03)
    # small shield contact fingers just inside the port sides
    for s in (-1, 1):
        m.box((s * (CAV_HX - 0.025), 2.55, -1.02), (0.06, 1.75, 0.55), "ShieldInner", 0.02)
    # strain relief ribs on the bottom rear
    for i in range(4):
        m.box((-2.55 + i * 1.70, 0.30, -15.45), (0.28, 0.22, 0.80), "PlasticDark", 0.02)

    return m


def main():
    m = build()
    # The front lip of the floor / keying ledge should read as black plastic,
    # not gold; strip any stray gold facing at the very front of the cavity.
    for i, (idxs, mat) in enumerate(m.faces):
        if mat != "Gold":
            continue
        pts = [m.verts[j] for j in idxs]
        if all(p[1] < 2.2 and p[2] > -2.5 for p in pts):
            m.faces[i] = (idxs, "PlasticBlack")
    obj_path = os.path.join(OUT_DIR, "rj45_connector.obj")
    mtl_path = os.path.join(OUT_DIR, "rj45_connector.mtl")
    m.write_obj(obj_path, "rj45_connector.mtl")
    m.write_mtl(mtl_path)
    print("vertices:", len(m.verts))
    print("faces   :", len(m.faces))
    print("materials:", len(MATERIALS))
    print("wrote", obj_path)
    print("wrote", mtl_path)


if __name__ == "__main__":
    main()
