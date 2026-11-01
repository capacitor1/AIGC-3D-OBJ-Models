#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procedural, fully-detailed 1" (DN25) brass water ball valve.
Outputs valve.obj + valve.mtl (millimetres).

Axes:  +X = flow axis, +Y = up (stem), +Z = lateral.
All profiles are generated as closed loops traced CLOCKWISE in the
(axial, radial) half-plane so that the computed normals face outward.
"""
import math, os, sys

TAU = math.pi * 2.0

# ----------------------------------------------------------------------------
# small vector helpers
# ----------------------------------------------------------------------------
def sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def add(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def mul(a, s): return (a[0]*s, a[1]*s, a[2]*s)
def dot(a, b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def norm(a):
    l = math.sqrt(dot(a, a))
    if l < 1e-12: return (0.0, 0.0, 0.0)
    return (a[0]/l, a[1]/l, a[2]/l)
def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t*t*(3.0-2.0*t)

# ----------------------------------------------------------------------------
# mesh part
# ----------------------------------------------------------------------------
class Part:
    def __init__(self, name, mat):
        self.name = name
        self.mat = mat
        self.pos = []
        self.nrm = []
        self.tris = []
        self._map = {}

    def _vid(self, p, n):
        key = (round(p[0], 5), round(p[1], 5), round(p[2], 5),
               round(n[0], 4), round(n[1], 4), round(n[2], 4))
        i = self._map.get(key)
        if i is None:
            i = len(self.pos)
            self.pos.append(p)
            self.nrm.append(n)
            self._map[key] = i
        return i

    def tri(self, p0, p1, p2, n0=None, n1=None, n2=None, force=None):
        if n0 is None:
            g = norm(cross(sub(p1, p0), sub(p2, p0)))
            n0 = n1 = n2 = g
        c = cross(sub(p1, p0), sub(p2, p0))
        if dot(c, c) < 1e-14:
            return
        ref = force if force is not None else add(add(n0, n1), n2)
        if dot(c, ref) < 0.0:
            p1, p2 = p2, p1
            n1, n2 = n2, n1
        self.tris.append((self._vid(p0, n0), self._vid(p1, n1), self._vid(p2, n2)))

    def quad(self, p00, p10, p11, p01, n00, n10, n11, n01):
        self.tri(p00, p10, p11, n00, n10, n11)
        self.tri(p00, p11, p01, n00, n11, n01)

    def quad_flat(self, p00, p10, p11, p01):
        n = norm(cross(sub(p10, p00), sub(p11, p00)))
        self.tri(p00, p10, p11, n, n, n)
        self.tri(p00, p11, p01, n, n, n)

# ----------------------------------------------------------------------------
# surface of revolution around X or Y.  profile = [(axial, radius), ...]
# closed loops get no caps; open profiles get flat end caps.
# ----------------------------------------------------------------------------
def revolve(part, prof, segs, axis='x', close=True, smooth_deg=34.0, cap=True):
    n = len(prof)
    sc = n if close else n - 1
    coslim = math.cos(math.radians(smooth_deg))

    segn = []
    for i in range(sc):
        a0, r0 = prof[i]
        a1, r1 = prof[(i + 1) % n]
        da, dr = a1 - a0, r1 - r0
        L = math.hypot(da, dr)
        if L < 1e-12:
            segn.append((0.0, 0.0))
        else:
            # (axial, radial) components of the outward normal
            segn.append((-dr / L, da / L))

    def ring(a, r, na, nr):
        out = []
        for j in range(segs + 1):
            th = TAU * j / segs
            ct, st = math.cos(th), math.sin(th)
            if axis == 'x':
                p = (a, r * ct, r * st)
                nn = (na, nr * ct, nr * st)
            else:
                p = (r * ct, a, r * st)
                nn = (nr * ct, na, nr * st)
            out.append((p, norm(nn)))
        return out

    rings = []          # list of ring data
    keyring = {}        # (point index, segment index) -> ring index

    def new_ring(a, r, na, nr):
        rings.append(ring(a, r, na, nr))
        return len(rings) - 1

    for i in range(n):
        prev = (i - 1) % n if (close or i > 0) else None
        nxt = i if i < sc else None
        if prev is not None and nxt is not None:
            pn, nn = segn[prev], segn[nxt]
            if dot((pn[0], pn[1], 0), (nn[0], nn[1], 0)) >= coslim:
                mx, my = pn[0] + nn[0], pn[1] + nn[1]
                L = math.hypot(mx, my)
                if L < 1e-9:
                    mx, my = nn
                else:
                    mx, my = mx / L, my / L
                ri = new_ring(prof[i][0], prof[i][1], mx, my)
                keyring[(i, prev)] = ri
                keyring[(i, nxt)] = ri
            else:
                keyring[(i, prev)] = new_ring(prof[i][0], prof[i][1], pn[0], pn[1])
                keyring[(i, nxt)] = new_ring(prof[i][0], prof[i][1], nn[0], nn[1])
        else:
            s = prev if prev is not None else nxt
            keyring[(i, s)] = new_ring(prof[i][0], prof[i][1], segn[s][0], segn[s][1])

    for i in range(sc):
        j = (i + 1) % n
        ra = rings[keyring[(i, i)]]
        rb = rings[keyring[(j, i)]]
        for k in range(segs):
            part.quad(ra[k][0], ra[k+1][0], rb[k+1][0], rb[k][0],
                      ra[k][1], ra[k+1][1], rb[k+1][1], rb[k][1])

    if (not close) and cap:
        for idx, sgn in ((0, -1.0), (n - 1, 1.0)):
            a, r = prof[idx]
            if r <= 1e-9:
                continue
            if axis == 'x':
                c = (a, 0.0, 0.0)
                nn = (sgn, 0.0, 0.0)
            else:
                c = (0.0, a, 0.0)
                nn = (0.0, sgn, 0.0)
            for k in range(segs):
                th0 = TAU * k / segs
                th1 = TAU * (k + 1) / segs
                if axis == 'x':
                    p0 = (a, r * math.cos(th0), r * math.sin(th0))
                    p1 = (a, r * math.cos(th1), r * math.sin(th1))
                else:
                    p0 = (r * math.cos(th0), a, r * math.sin(th0))
                    p1 = (r * math.cos(th1), a, r * math.sin(th1))
                part.tri(c, p0, p1, nn, nn, nn, force=nn)

# ----------------------------------------------------------------------------
# hexagonal prism / nut along X or Y
# ----------------------------------------------------------------------------
def hex_collar(part, axis, a0, a1, af, r_inner=0.0, chamfer=1.2, seg_inner=72):
    R = af / math.sqrt(3.0)
    c = min(chamfer, (a1 - a0) * 0.45)
    levels = [(a0, R - c), (a0 + c, R), (a1 - c, R), (a1, R - c)]
    angles = [math.radians(60.0 * k) for k in range(6)]

    def p3(a, u, v):
        return (a, u, v) if axis == 'x' else (u, a, v)

    def n3(nu, nv, na=0.0):
        return (na, nu, nv) if axis == 'x' else (nu, na, nv)

    def ring(level):
        a, rad = level
        return [p3(a, rad * math.cos(t), rad * math.sin(t)) for t in angles]

    rs = [ring(l) for l in levels]

    # side faces: 3 bands (chamfer / main / chamfer)
    for band in range(3):
        A, B = rs[band], rs[band + 1]
        for k in range(6):
            k2 = (k + 1) % 6
            p00, p10 = A[k], A[k2]
            p01, p11 = B[k], B[k2]
            n = norm(cross(sub(p10, p00), sub(p11, p00)))
            part.quad(p00, p10, p11, p01, n, n, n, n)

    # end faces
    for level_idx, sgn in ((0, -1.0), (3, 1.0)):
        a, rad = levels[level_idx]
        if r_inner > 1e-6:
            N = seg_inner
            for k in range(N):
                th0 = TAU * k / N
                th1 = TAU * (k + 1) / N
                # radius of the hex outline along a ray
                def hr(th):
                    alpha = math.radians(((math.degrees(th) + 30.0) % 60.0) - 30.0)
                    return (rad * math.cos(math.radians(30.0))) / math.cos(alpha)
                r0, r1 = hr(th0), hr(th1)
                o0 = p3(a, r0 * math.cos(th0), r0 * math.sin(th0))
                o1 = p3(a, r1 * math.cos(th1), r1 * math.sin(th1))
                i0 = p3(a, r_inner * math.cos(th0), r_inner * math.sin(th0))
                i1 = p3(a, r_inner * math.cos(th1), r_inner * math.sin(th1))
                nn = n3(0.0, 0.0, sgn)
                part.quad(o0, o1, i1, i0, nn, nn, nn, nn)
        else:
            center = p3(a, 0.0, 0.0)
            nn = n3(0.0, 0.0, sgn)
            for k in range(6):
                k2 = (k + 1) % 6
                part.tri(center, rs[level_idx][k], rs[level_idx][k2], nn, nn, nn, force=nn)

    # inner bore
    if r_inner > 1e-6:
        N = seg_inner
        for k in range(N):
            th0 = TAU * k / N
            th1 = TAU * (k + 1) / N
            c0, s0 = math.cos(th0), math.sin(th0)
            c1, s1 = math.cos(th1), math.sin(th1)
            p00 = p3(a0, r_inner * c0, r_inner * s0)
            p10 = p3(a0, r_inner * c1, r_inner * s1)
            p11 = p3(a1, r_inner * c1, r_inner * s1)
            p01 = p3(a1, r_inner * c0, r_inner * s0)
            n00 = n3(-c0, -s0)
            n10 = n3(-c1, -s1)
            n11 = n3(-c1, -s1)
            n01 = n3(-c0, -s0)
            part.quad(p00, p10, p11, p01, n00, n10, n11, n01)

# ----------------------------------------------------------------------------
# helical thread (BSPP), solid ridge swept along a helix
# ----------------------------------------------------------------------------
def thread(part, x0, x1, root, major, pitch, steps_per_turn=110, taper_turns=0.8):
    L = x1 - x0
    turns = L / pitch
    N = max(16, int(round(turns * steps_per_turn)))
    crest_half = 0.20
    root_half = pitch * 0.40
    prof2 = [(-root_half, root), (-crest_half, major), (crest_half, major), (root_half, root)]

    def sec(t):
        x = x0 + L * t
        th = TAU * (x - x0) / pitch
        # run-out at both ends
        u = min(x - x0, x1 - x) / (pitch * taper_turns)
        f = 0.06 + 0.94 * smoothstep(u)
        pts = []
        for s, r in prof2:
            rr = root + (r - root) * f
            pts.append((x + s, rr * math.cos(th), rr * math.sin(th)))
        return pts

    rings = [sec(i / N) for i in range(N + 1)]
    for i in range(N):
        A, B = rings[i], rings[i + 1]
        for k in range(4):
            k2 = (k + 1) % 4
            p00, p10, p11, p01 = A[k], A[k2], B[k2], B[k]
            part.quad_flat(p00, p10, p11, p01)
    # end caps
    for idx, force in ((0, (-1.0, 0.0, 0.0)), (N, (1.0, 0.0, 0.0))):
        A = rings[idx]
        part.tri(A[0], A[1], A[2], force=force)
        part.tri(A[0], A[2], A[3], force=force)

# ----------------------------------------------------------------------------
# torus around Y axis
# ----------------------------------------------------------------------------
def torus(part, cy, R, r, seg_u=72, seg_v=24):
    def P(u, v):
        cu, su = math.cos(u), math.sin(u)
        cv, sv = math.cos(v), math.sin(v)
        p = ((R + r * cv) * cu, cy + r * sv, (R + r * cv) * su)
        n = (cv * cu, sv, cv * su)
        return p, n
    for i in range(seg_u):
        u0 = TAU * i / seg_u
        u1 = TAU * (i + 1) / seg_u
        for j in range(seg_v):
            v0 = TAU * j / seg_v
            v1 = TAU * (j + 1) / seg_v
            p00, n00 = P(u0, v0)
            p10, n10 = P(u1, v0)
            p11, n11 = P(u1, v1)
            p01, n01 = P(u0, v1)
            part.quad(p00, p10, p11, p01, n00, n10, n11, n01)

# ----------------------------------------------------------------------------
# capsule with elliptical cross-section along X (handle grip)
# ----------------------------------------------------------------------------
def grip(part, cx, cy, L, a, b, c, seg_u=64, seg_t=18):
    def cyl(x, th):
        p = (x, cy + b * math.cos(th), c * math.sin(th))
        n = norm((0.0, math.cos(th) / b, math.sin(th) / c))
        return p, n

    def cap(xside, t, th):
        s = math.cos(t)
        x = xside * (L + a * math.sin(t))
        p = (cx + x, cy + b * s * math.cos(th), c * s * math.sin(th))
        n = norm((xside * math.sin(t) / a, s * math.cos(th) / b, s * math.sin(th) / c))
        return p, n

    # body
    for i in range(seg_u):
        th0 = TAU * i / seg_u
        th1 = TAU * (i + 1) / seg_u
        p00, n00 = cyl(cx - L, th0)
        p10, n10 = cyl(cx - L, th1)
        p11, n11 = cyl(cx + L, th1)
        p01, n01 = cyl(cx + L, th0)
        part.quad(p00, p10, p11, p01, n00, n10, n11, n01)

    for sx in (-1.0, 1.0):
        for j in range(seg_t):
            t0 = (math.pi / 2) * j / seg_t
            t1 = (math.pi / 2) * (j + 1) / seg_t
            for i in range(seg_u):
                th0 = TAU * i / seg_u
                th1 = TAU * (i + 1) / seg_u
                p00, n00 = cap(sx, t0, th0)
                p10, n10 = cap(sx, t0, th1)
                p11, n11 = cap(sx, t1, th1)
                p01, n01 = cap(sx, t1, th0)
                part.quad(p00, p10, p11, p01, n00, n10, n11, n01)

# ----------------------------------------------------------------------------
# flat handle bar: stadium outline extruded along Y with chamfered edges
# ----------------------------------------------------------------------------
def stadium_outline(x0, x1, w, d=0.0, arc_seg=40):
    x0 += d; x1 -= d; w -= d
    pts = []
    # right cap, bottom -> top
    for k in range(arc_seg + 1):
        ph = -math.pi / 2 + math.pi * k / arc_seg
        pts.append((x1 + w * math.cos(ph), w * math.sin(ph), math.cos(ph), math.sin(ph)))
    # left cap, top -> bottom (the straight top/bottom runs are implicit)
    for k in range(arc_seg + 1):
        ph = math.pi / 2 + math.pi * k / arc_seg
        pts.append((x0 + w * math.cos(ph), w * math.sin(ph), math.cos(ph), math.sin(ph)))
    return pts


def prism_y(part, poly, y0, y1):
    """Extrude a convex CCW polygon in XZ along Y, with flat caps."""
    n = len(poly)
    for k in range(n):
        k2 = (k + 1) % n
        x0, z0 = poly[k]; x1, z1 = poly[k2]
        p00 = (x0, y0, z0); p10 = (x1, y0, z1)
        p11 = (x1, y1, z1); p01 = (x0, y1, z0)
        part.quad_flat(p00, p10, p11, p01)
    for y, sgn in ((y0, -1.0), (y1, 1.0)):
        cx = sum(p[0] for p in poly) / n
        cz = sum(p[1] for p in poly) / n
        c = (cx, y, cz)
        nn = (0.0, sgn, 0.0)
        for k in range(n):
            k2 = (k + 1) % n
            p0 = (poly[k][0], y, poly[k][1])
            p1 = (poly[k2][0], y, poly[k2][1])
            part.tri(c, p0, p1, nn, nn, nn, force=nn)


def handle_bar(part, x0, x1, w, y0, y1, cham=0.8, arc_seg=40):
    lv = [(y0, cham), (y0 + cham, 0.0), (y1 - cham, 0.0), (y1, cham)]
    outs = [stadium_outline(x0, x1, w, d, arc_seg) for (_, d) in lv]
    rings = []
    for (y, d), out in zip(lv, outs):
        ring = []
        for (x, z, nx, nz) in out:
            ring.append(((x, y, z), (nx, 0.0, nz)))
        rings.append(ring)

    # main side wall (smooth normals)
    A, B = rings[1], rings[2]
    M = len(A)
    for k in range(M):
        k2 = (k + 1) % M
        part.quad(A[k][0], A[k2][0], B[k2][0], B[k][0],
                  A[k][1], A[k2][1], B[k2][1], B[k][1])

    # chamfer strips (flat)
    for (ra, rb) in ((rings[0], rings[1]), (rings[3], rings[2])):
        for k in range(M):
            k2 = (k + 1) % M
            part.quad_flat(ra[k][0], ra[k2][0], rb[k2][0], rb[k][0])

    # end caps
    for idx, sgn in ((0, -1.0), (3, 1.0)):
        out = outs[idx]
        y = lv[idx][0]
        cx = sum(p[0] for p in out) / len(out)
        cz = sum(p[1] for p in out) / len(out)
        c = (cx, y, cz)
        nn = (0.0, sgn, 0.0)
        for k in range(len(out)):
            p0 = (out[k][0], y, out[k][1])
            p1 = (out[(k+1) % len(out)][0], y, out[(k+1) % len(out)][1])
            part.tri(c, p0, p1, nn, nn, nn, force=nn)

# ----------------------------------------------------------------------------
# build the valve
# ----------------------------------------------------------------------------
def build():
    parts = []

    # ---- body (left half) -------------------------------------------------
    body = Part('Body', 'ChromeSatin')
    body_prof = [
        # outer surface, left end -> right end
        (-78.0, 14.20), (-77.2, 14.70), (-58.0, 14.70),
        (-58.0, 15.50), (-46.0, 15.50), (-45.5, 17.50),
        (-43.0, 20.20), (-41.0, 21.30), (-38.0, 21.60),
        (-35.0, 22.80), (-31.0, 24.40), (-27.0, 25.70),
        (-23.0, 26.60), (-19.0, 27.20), (-14.0, 27.55),
        (-8.0, 27.68), (0.0, 27.70), (7.0, 27.65),
        (13.0, 27.35), (17.0, 26.85), (20.0, 25.90),
        (22.0, 24.20), (23.0, 22.20), (23.7, 20.60),
        (24.0, 19.10), (25.9, 19.10),
        # right end face
        (25.9, 12.70),
        # inner surface, right -> left
        (19.0, 12.70), (19.0, 21.50), (15.0, 21.50),
        (15.0, 23.50), (-15.0, 23.50), (-15.0, 21.50),
        (-19.0, 21.50), (-19.0, 12.70),
        (-77.0, 12.70), (-78.0, 13.90),
    ]
    revolve(body, body_prof, 200, axis='x', close=True, smooth_deg=32)
    parts.append(body)

    # ---- right end cap ----------------------------------------------------
    cap = Part('EndCap', 'ChromeSatin')
    cap_prof = [
        (26.0, 20.50), (37.0, 20.50), (37.5, 19.50),
        (49.0, 19.50), (49.0, 20.20), (50.0, 18.20),
        (57.0, 18.20), (58.0, 15.60), (58.0, 14.70),
        (77.2, 14.70), (78.0, 14.20),
        (78.0, 13.90), (77.0, 12.70),
        (26.0, 12.70),
    ]
    revolve(cap, cap_prof, 200, axis='x', close=True, smooth_deg=32)
    parts.append(cap)

    # ---- threads ----------------------------------------------------------
    tl = Part('ThreadLeft', 'ChromeSatin')
    thread(tl, -77.2, -58.35, 14.55, 16.625, 2.309, steps_per_turn=120)
    parts.append(tl)

    tr = Part('ThreadRight', 'ChromeSatin')
    thread(tr, 58.35, 77.2, 14.55, 16.625, 2.309, steps_per_turn=120)
    parts.append(tr)

    # ---- hex wrench flats -------------------------------------------------
    hl = Part('HexLeft', 'ChromeSatin')
    hex_collar(hl, 'x', -58.0, -46.0, 41.0, r_inner=15.5, chamfer=1.4)
    parts.append(hl)

    hr = Part('HexRight', 'ChromeSatin')
    hex_collar(hr, 'x', 38.0, 49.0, 41.0, r_inner=19.5, chamfer=1.4)
    parts.append(hr)

    # ---- union nut --------------------------------------------------------
    nut = Part('UnionNut', 'ChromeSatin')
    hex_collar(nut, 'x', 24.0, 36.0, 46.0, r_inner=20.8, chamfer=1.2)
    parts.append(nut)

    # ---- ball -------------------------------------------------------------
    ball = Part('Ball', 'ChromeBright')
    Rb = 22.0
    Rh = 12.7
    xh = math.sqrt(Rb * Rb - Rh * Rh)
    ball_prof = []
    N = 84
    # 45-degree lead-in chamfers on both ends of the through bore
    x0 = -xh + 0.5
    x1 = xh - 0.5
    r0 = math.sqrt(max(0.0, Rb * Rb - x0 * x0))
    r1 = math.sqrt(max(0.0, Rb * Rb - x1 * x1))
    ball_prof.append((-xh + 1.2, Rh))
    ball_prof.append((x0, r0))
    for k in range(N + 1):
        x = x0 + (x1 - x0) * k / N
        r = math.sqrt(max(0.0, Rb * Rb - x * x))
        ball_prof.append((x, r))
    ball_prof.append((x1, r1))
    ball_prof.append((xh - 1.2, Rh))
    revolve(ball, ball_prof, 192, axis='x', close=True, smooth_deg=20)
    parts.append(ball)

    # ---- PTFE seats -------------------------------------------------------
    seatL = Part('SeatLeft', 'PTFE')
    seatL_prof = [(-18.9, 14.5), (-18.9, 21.4), (-15.0, 21.4),
                  (-15.0, 13.8), (-15.8, 12.9)]
    revolve(seatL, seatL_prof, 128, axis='x', close=True, smooth_deg=30)
    parts.append(seatL)

    seatR = Part('SeatRight', 'PTFE')
    seatR_prof = [(15.0, 12.9), (15.8, 12.9), (15.0, 13.8),
                  (15.0, 21.4), (18.9, 21.4), (18.9, 14.5)]
    revolve(seatR, seatR_prof, 128, axis='x', close=True, smooth_deg=30)
    parts.append(seatR)

    # ---- stem -------------------------------------------------------------
    stem = Part('Stem', 'ChromeBright')
    revolve(stem, [(17.0, 5.0), (51.2, 5.0)], 72, axis='y', close=False, cap=True)
    parts.append(stem)

    # ---- neck / bonnet ----------------------------------------------------
    neck = Part('Bonnet', 'ChromeSatin')
    neck_prof = [(24.0, 13.0), (25.5, 12.2), (27.0, 11.2),
                 (32.5, 10.6), (33.2, 10.1)]
    revolve(neck, neck_prof, 128, axis='y', close=False, cap=True)
    parts.append(neck)

    # ---- packing nut ------------------------------------------------------
    pnut = Part('PackingNut', 'ChromeSatin')
    hex_collar(pnut, 'y', 33.6, 40.0, 26.0, r_inner=6.2, chamfer=1.0, seg_inner=72)
    parts.append(pnut)

    # ---- O-ring -----------------------------------------------------------
    oring = Part('ORing', 'Rubber')
    torus(oring, 41.4, 6.0, 1.25, seg_u=72, seg_v=24)
    parts.append(oring)

    # ---- handle boss ------------------------------------------------------
    boss = Part('HandleBoss', 'ChromeBright')
    boss_prof = [(44.0, 15.0), (49.8, 15.0), (51.0, 13.6)]
    revolve(boss, boss_prof, 128, axis='y', close=False, cap=True)
    parts.append(boss)

    # ---- handle bar -------------------------------------------------------
    bar = Part('HandleBar', 'ChromeBright')
    handle_bar(bar, -82.0, 4.0, 10.0, 44.0, 50.0, cham=0.8, arc_seg=40)
    # embossed flow arrow on the exposed part of the lever
    prism_y(bar, [(-28.0, -2.0), (-21.0, -2.0), (-21.0, 2.0), (-28.0, 2.0)], 49.95, 50.55)
    prism_y(bar, [(-21.0, -3.6), (-16.2, 0.0), (-21.0, 3.6)], 49.95, 50.55)
    parts.append(bar)

    # ---- red grip ---------------------------------------------------------
    gr = Part('Grip', 'RedEnamel')
    grip(gr, -63.0, 47.0, 25.0, 9.0, 8.0, 12.5, seg_u=64, seg_t=18)
    parts.append(gr)

    # ---- washer -----------------------------------------------------------
    washer = Part('Washer', 'ChromeBright')
    revolve(washer, [(50.8, 6.2), (50.8, 12.0), (51.6, 12.0), (51.6, 6.2)],
            96, axis='y', close=True, smooth_deg=30)
    parts.append(washer)

    # ---- handle nut -------------------------------------------------------
    hnut = Part('HandleNut', 'ChromeBright')
    hex_collar(hnut, 'y', 51.6, 56.0, 19.0, r_inner=0.0, chamfer=0.8)
    parts.append(hnut)

    return parts

# ----------------------------------------------------------------------------
# OBJ / MTL writer
# ----------------------------------------------------------------------------
MTL = """# Materials for DN25 water ball valve
newmtl ChromeSatin
Ka 0.20 0.20 0.21
Kd 0.62 0.63 0.65
Ks 0.55 0.55 0.58
Ns 90
Ni 1.5
d 1.0
illum 2

newmtl ChromeBright
Ka 0.30 0.30 0.31
Kd 0.80 0.81 0.83
Ks 0.95 0.95 0.98
Ns 420
Ni 1.5
d 1.0
illum 2

newmtl PTFE
Ka 0.70 0.70 0.68
Kd 0.94 0.94 0.91
Ks 0.10 0.10 0.10
Ns 30
Ni 1.35
d 1.0
illum 2

newmtl RedEnamel
Ka 0.22 0.01 0.01
Kd 0.62 0.035 0.03
Ks 0.45 0.10 0.08
Ns 110
Ni 1.5
d 1.0
illum 2

newmtl Rubber
Ka 0.01 0.01 0.01
Kd 0.025 0.025 0.028
Ks 0.12 0.12 0.13
Ns 40
Ni 1.5
d 1.0
illum 2
"""

def write_obj(parts, path):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write("# DN25 / G1\" full-port water ball valve\n")
        f.write("# Procedurally generated. Units: millimetres.\n")
        f.write("# +X flow axis, +Y up (stem), +Z lateral.  No textures.\n")
        f.write("mtllib valve.mtl\n\n")
        off = 1
        for p in parts:
            f.write("o %s\n" % p.name)
            f.write("usemtl %s\n" % p.mat)
            for v in p.pos:
                f.write("v %.6f %.6f %.6f\n" % v)
            for n in p.nrm:
                f.write("vn %.6f %.6f %.6f\n" % n)
            for (a, b, c) in p.tris:
                f.write("f %d//%d %d//%d %d//%d\n" %
                        (a + off, a + off, b + off, b + off, c + off, c + off))
            f.write("\n")
            off += len(p.pos)
    with open(os.path.join(os.path.dirname(path), 'valve.mtl'), 'w',
              encoding='utf-8', newline='\n') as f:
        f.write(MTL)

def main():
    parts = build()
    tot_v = sum(len(p.pos) for p in parts)
    tot_t = sum(len(p.tris) for p in parts)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'valve.obj')
    write_obj(parts, out)
    print("parts:", len(parts), " verts:", tot_v, " tris:", tot_t)
    for p in parts:
        print("  %-12s %-13s v=%6d t=%6d" % (p.name, p.mat, len(p.pos), len(p.tris)))
    print("wrote", out, os.path.getsize(out), "bytes")

if __name__ == '__main__':
    main()
