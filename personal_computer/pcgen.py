#!/usr/bin/env python3
"""
Procedural high-detail desktop gaming PC generator.
Units: millimetres.  Coordinates: +X = right side (solid panel), -X = open side,
+Y = up, +Z = front, -Z = rear.
"""
from __future__ import annotations
import math, os, json
import numpy as np
import trimesh
from trimesh.creation import box as tm_box, cylinder as tm_cylinder
from trimesh.convex import convex_hull
from trimesh.transformations import rotation_matrix, translation_matrix
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

# ----------------------------------------------------------------------------- materials
MATERIALS = {
    'steel_black':   dict(kd=(0.030,0.032,0.038), ks=(0.38,0.39,0.42), ns=180, d=1.0),
    'steel_dark':    dict(kd=(0.035,0.037,0.042), ks=(0.28,0.29,0.32), ns=140, d=1.0),
    'steel_mid':     dict(kd=(0.095,0.100,0.110), ks=(0.40,0.40,0.42), ns=160, d=1.0),
    'steel_light':   dict(kd=(0.24,0.25,0.27),  ks=(0.55,0.56,0.58), ns=200, d=1.0),
    'aluminum':      dict(kd=(0.54,0.56,0.60),  ks=(0.80,0.80,0.82), ns=260, d=1.0),
    'brushed':       dict(kd=(0.30,0.31,0.34),  ks=(0.62,0.62,0.64), ns=220, d=1.0),
    'chrome':        dict(kd=(0.72,0.74,0.78),  ks=(1.00,1.00,1.00), ns=420, d=1.0),
    'nickel':        dict(kd=(0.52,0.54,0.57),  ks=(0.85,0.86,0.88), ns=320, d=1.0),
    'copper':        dict(kd=(0.66,0.32,0.15),  ks=(0.75,0.52,0.32), ns=240, d=1.0),
    'gold':          dict(kd=(0.86,0.62,0.18),  ks=(1.00,0.82,0.38), ns=260, d=1.0),
    'pcb':           dict(kd=(0.012,0.032,0.022), ks=(0.10,0.12,0.11), ns=60, d=1.0),
    'pcb_black':     dict(kd=(0.018,0.020,0.024), ks=(0.12,0.12,0.13), ns=60, d=1.0),
    'plastic_black': dict(kd=(0.034,0.036,0.042), ks=(0.24,0.24,0.26), ns=80, d=1.0),
    'plastic_dark':  dict(kd=(0.055,0.058,0.065), ks=(0.22,0.22,0.24), ns=80, d=1.0),
    'plastic_grey':  dict(kd=(0.14,0.145,0.155), ks=(0.28,0.28,0.30), ns=80, d=1.0),
    'rubber':        dict(kd=(0.009,0.009,0.011), ks=(0.04,0.04,0.04), ns=20, d=1.0),
    'glass':         dict(kd=(0.030,0.052,0.060), ks=(0.95,0.97,1.00), ns=420, d=0.26),
    'fan_blade':     dict(kd=(0.38,0.42,0.47), ks=(0.42,0.44,0.47), ns=120, d=0.92),
    'fan_blade_black':dict(kd=(0.035,0.038,0.044),ks=(0.22,0.22,0.24), ns=100, d=1.0),
    'rgb_cyan':      dict(kd=(0.00,0.78,0.95), ks=(0.2,0.8,1.0), ns=160, d=1.0, ke=(0.0,0.65,0.95)),
    'rgb_blue':      dict(kd=(0.02,0.18,1.00), ks=(0.2,0.4,1.0), ns=160, d=1.0, ke=(0.0,0.12,0.8)),
    'rgb_magenta':   dict(kd=(1.00,0.04,0.46), ks=(1.0,0.2,0.6), ns=160, d=1.0, ke=(0.8,0.0,0.3)),
    'rgb_white':     dict(kd=(0.95,0.95,1.00), ks=(1.0,1.0,1.0), ns=160, d=1.0, ke=(0.8,0.8,0.9)),
    'rgb_lime':      dict(kd=(0.55,1.00,0.10), ks=(0.6,1.0,0.2), ns=160, d=1.0, ke=(0.3,0.8,0.0)),
    'label_white':   dict(kd=(0.86,0.87,0.88), ks=(0.3,0.3,0.3), ns=60, d=1.0),
    'label_dark':    dict(kd=(0.06,0.06,0.07), ks=(0.2,0.2,0.2), ns=60, d=1.0),
    'label_red':     dict(kd=(0.72,0.03,0.03), ks=(0.4,0.05,0.05), ns=80, d=1.0),
    'sleeve_black':  dict(kd=(0.022,0.024,0.029), ks=(0.20,0.20,0.22), ns=90, d=1.0),
    'sleeve_grey':   dict(kd=(0.075,0.078,0.085), ks=(0.22,0.22,0.24), ns=90, d=1.0),
    'radiator':      dict(kd=(0.028,0.030,0.034), ks=(0.25,0.25,0.27), ns=120, d=1.0),
    'ssd':           dict(kd=(0.040,0.042,0.048), ks=(0.30,0.30,0.32), ns=120, d=1.0),
    'ssd_label':     dict(kd=(0.10,0.20,0.32), ks=(0.3,0.3,0.3), ns=80, d=1.0),
    'capacitor':     dict(kd=(0.055,0.058,0.065), ks=(0.4,0.4,0.42), ns=140, d=1.0),
    'socket':        dict(kd=(0.10,0.10,0.11), ks=(0.3,0.3,0.3), ns=100, d=1.0),
    'thermal_pad':   dict(kd=(0.16,0.19,0.24), ks=(0.1,0.1,0.1), ns=20, d=1.0),
    'vent_mesh':     dict(kd=(0.050,0.053,0.060), ks=(0.40,0.40,0.42), ns=120, d=1.0),
}

# ----------------------------------------------------------------------------- mesh
class Mesh:
    def __init__(self, name='mesh'):
        self.name = name
        self.v = []
        self.f = []
        self.m = []
    def add_vertex(self, x, y, z):
        self.v.append((float(x),float(y),float(z)))
        return len(self.v)-1
    def add_face(self, idxs, mat):
        self.f.append(tuple(idxs)); self.m.append(mat)
    def add_tm(self, tm, mat):
        if tm is None: return
        off = len(self.v)
        for p in tm.vertices:
            self.v.append((float(p[0]),float(p[1]),float(p[2])))
        for tri in tm.faces:
            self.f.append((off+int(tri[0]), off+int(tri[1]), off+int(tri[2])))
            self.m.append(mat)
    def transform(self, M):
        out = Mesh(self.name)
        v = np.array(self.v, dtype=float)
        vh = np.column_stack([v, np.ones(len(v))])
        v2 = (M @ vh.T).T[:, :3]
        out.v = [tuple(p) for p in v2]
        out.f = list(self.f); out.m = list(self.m)
        return out
    def merged(self, other, M=None):
        out = Mesh(self.name)
        out.v = list(self.v); out.f = list(self.f); out.m = list(self.m)
        if M is not None:
            other = other.transform(M)
        off = len(out.v)
        out.v.extend(other.v)
        out.f.extend([(a+off,b+off,c+off) for a,b,c in other.f])
        out.m.extend(other.m)
        return out
    def bounds(self):
        v=np.array(self.v); return v.min(0),v.max(0)
    def tri_count(self):
        return len(self.f)

# ----------------------------------------------------------------------------- transforms
def T(x=0,y=0,z=0):
    return translation_matrix((x,y,z))
def Rx(deg):
    return rotation_matrix(math.radians(deg),(1,0,0))
def Ry(deg):
    return rotation_matrix(math.radians(deg),(0,1,0))
def Rz(deg):
    return rotation_matrix(math.radians(deg),(0,0,1))
def frame(origin, u, v):
    u=np.array(u,float); v=np.array(v,float)
    u/=np.linalg.norm(u); v/=np.linalg.norm(v)
    n=np.cross(u,v); n/=np.linalg.norm(n)
    v=np.cross(n,u)
    M=np.eye(4)
    M[:3,0]=u; M[:3,1]=v; M[:3,2]=n; M[:3,3]=origin
    return M

# ----------------------------------------------------------------------------- primitives
def add_box(mesh, x0,x1,y0,y1,z0,z1, mat, bevel=0.0):
    x0,x1=sorted((x0,x1)); y0,y1=sorted((y0,y1)); z0,z1=sorted((z0,z1))
    if bevel <= 0:
        # direct box, six quads
        base=len(mesh.v)
        pts=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
             (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
        for p in pts: mesh.add_vertex(*p)
        quads=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        for q in quads:
            a,b,c,d=[base+i for i in q]
            mesh.add_face((a,b,c),mat); mesh.add_face((a,c,d),mat)
        return
    c=min(bevel, (x1-x0)/2.01, (y1-y0)/2.01, (z1-z0)/2.01)
    pts=[]
    # x faces
    for x in (x0,x1):
        for y in (y0+c,y1-c):
            for z in (z0+c,z1-c): pts.append((x,y,z))
    for y in (y0,y1):
        for x in (x0+c,x1-c):
            for z in (z0+c,z1-c): pts.append((x,y,z))
    for z in (z0,z1):
        for x in (x0+c,x1-c):
            for y in (y0+c,y1-c): pts.append((x,y,z))
    tm=convex_hull(np.array(pts))
    mesh.add_tm(tm, mat)

def add_tm_box(mesh, extents, center, mat, M=None):
    tm=tm_box(extents=extents)
    if M is not None: tm.apply_transform(M)
    tm.apply_translation(center)
    mesh.add_tm(tm,mat)

def add_cylinder(mesh, radius, height, center, mat, axis='z', sections=48, cap=True):
    tm=tm_cylinder(radius=radius,height=height,sections=sections,cap=cap)
    if axis=='x': tm.apply_transform(Ry(90))
    elif axis=='y': tm.apply_transform(Rx(-90))
    tm.apply_translation(center)
    mesh.add_tm(tm,mat)

def add_cone(mesh, radius, height, center, mat, axis='z', sections=40):
    tm=trimesh.creation.cone(radius=radius,height=height,sections=sections)
    if axis=='x': tm.apply_transform(Ry(90))
    elif axis=='y': tm.apply_transform(Rx(-90))
    tm.apply_translation(center)
    mesh.add_tm(tm,mat)

def ring_tm(outer, inner, height, sections=64):
    """annulus with axis z, centred at origin, z in [-h/2,h/2]"""
    h=height/2
    verts=[]; faces=[]
    for z in (-h,h):
        for r in (outer,inner):
            for i in range(sections):
                a=2*math.pi*i/sections
                verts.append((r*math.cos(a),r*math.sin(a),z))
    def idx(zl,ri,i): return (zl*2+ri)*sections + (i%sections)
    for i in range(sections):
        j=(i+1)%sections
        faces.append((idx(0,0,i),idx(0,0,j),idx(1,0,j),idx(1,0,i)))
        faces.append((idx(0,1,j),idx(0,1,i),idx(1,1,i),idx(1,1,j)))
        faces.append((idx(0,0,j),idx(0,0,i),idx(0,1,i),idx(0,1,j)))
        faces.append((idx(1,0,i),idx(1,0,j),idx(1,1,j),idx(1,1,i)))
    return trimesh.Trimesh(vertices=np.array(verts),faces=np.array(faces),process=False)

def add_ring(mesh, outer, inner, height, center, mat, axis='z', sections=64):
    tm=ring_tm(outer,inner,height,sections)
    if axis=='x': tm.apply_transform(Ry(90))
    elif axis=='y': tm.apply_transform(Rx(-90))
    tm.apply_translation(center)
    mesh.add_tm(tm,mat)

def add_tube(mesh, points, radius, mat, sides=20, caps=True, taper=None):
    pts=np.array(points,float)
    n=len(pts)
    tangents=[]
    for i in range(n):
        if i==0: t=pts[1]-pts[0]
        elif i==n-1: t=pts[-1]-pts[-2]
        else: t=pts[i+1]-pts[i-1]
        tangents.append(t/np.linalg.norm(t))
    t0=tangents[0]
    ref=np.array([0,1,0.0])
    if abs(np.dot(t0,ref))>0.9: ref=np.array([1,0,0.0])
    u=np.cross(t0,ref); u/=np.linalg.norm(u)
    frames=[]
    for i in range(n):
        if i>0:
            u=u-np.dot(u,tangents[i])*tangents[i]
            if np.linalg.norm(u)<1e-6:
                ref=np.array([1,0,0.0]) if abs(tangents[i][0])<0.9 else np.array([0,0,1.0])
                u=np.cross(tangents[i],ref)
            u/=np.linalg.norm(u)
        v=np.cross(tangents[i],u); v/=np.linalg.norm(v)
        frames.append((u.copy(),v.copy()))
    base=len(mesh.v)
    for i,p in enumerate(pts):
        u,v=frames[i]
        rr=radius if taper is None else radius*taper[i]
        for k in range(sides):
            a=2*math.pi*k/sides
            q=p + rr*(math.cos(a)*u + math.sin(a)*v)
            mesh.add_vertex(*q)
    for i in range(n-1):
        for k in range(sides):
            j=(k+1)%sides
            a=base+i*sides+k; b=base+i*sides+j
            c=base+(i+1)*sides+j; d=base+(i+1)*sides+k
            mesh.add_face((a,b,c),mat); mesh.add_face((a,c,d),mat)
    if caps:
        c0=len(mesh.v); mesh.add_vertex(*pts[0])
        c1=len(mesh.v); mesh.add_vertex(*pts[-1])
        for k in range(sides):
            j=(k+1)%sides
            mesh.add_face((c0,base+j,base+k),mat)
            a=base+(n-1)*sides
            mesh.add_face((c1,a+k,a+j),mat)

def add_disc(mesh, radius, center, mat, axis='z', sections=48):
    add_cylinder(mesh,radius,0.2,center,mat,axis=axis,sections=sections)

def add_text(mesh, text, size, mat, M, depth=0.35, fontweight='bold'):
    fp=FontProperties(family='DejaVu Sans',weight=fontweight)
    tp=TextPath((0,0),text,size=size,prop=fp)
    paths=tp.to_polygons()
    polys=[]
    for p in paths:
        if len(p)>=3:
            poly=Polygon(p)
            if poly.is_valid and poly.area>1e-8:
                polys.append(poly)
    if not polys: return
    solids=[]
    outers=[p for p in polys if not p.exterior.is_ccw]
    holes=[p for p in polys if p.exterior.is_ccw]
    if not outers:
        outers, holes = polys, []
    for p in outers:
        inner=[h for h in holes if p.contains(h.representative_point())]
        try:
            solids.append(Polygon(p.exterior,[h.exterior for h in inner]))
        except Exception:
            solids.append(p)
    for poly in solids:
        try:
            tm=trimesh.creation.extrude_polygon(poly,height=depth)
        except Exception:
            continue
        tm.apply_transform(M)
        mesh.add_tm(tm,mat)

def add_screw(mesh, center, radius, height, mat, axis='x', socket=True, sections=20):
    add_cylinder(mesh,radius,height,center,mat,axis=axis,sections=sections)
    if socket:
        c=list(center)
        if axis=='x': c[0] += height*0.51
        elif axis=='y': c[1] += height*0.51
        else: c[2] += height*0.51
        add_cylinder(mesh,radius*0.55,height*0.16,c,'label_dark',axis=axis,sections=16)

def add_hex_screw(mesh, center, radius, height, mat, axis='x'):
    add_cylinder(mesh,radius,height,center,mat,axis=axis,sections=6)

def tm_chamfer_box(x0,x1,y0,y1,z0,z1,c):
    c=min(c,(x1-x0)/2.01,(y1-y0)/2.01,(z1-z0)/2.01)
    pts=[]
    for x in (x0,x1):
        for y in (y0+c,y1-c):
            for z in (z0+c,z1-c): pts.append((x,y,z))
    for y in (y0,y1):
        for x in (x0+c,x1-c):
            for z in (z0+c,z1-c): pts.append((x,y,z))
    for z in (z0,z1):
        for x in (x0+c,x1-c):
            for y in (y0+c,y1-c): pts.append((x,y,z))
    return convex_hull(np.array(pts))

def csg_difference(base, cutters, mat, mesh):
    try:
        res=base.difference(trimesh.util.concatenate(cutters),engine='manifold')
    except Exception:
        res=base
        for c in cutters:
            res=res.difference(c,engine='manifold')
    mesh.add_tm(res,mat)

def cutter_box(x0,x1,y0,y1,z0,z1):
    return tm_box(extents=(x1-x0,y1-y0,z1-z0)).apply_translation(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))

def cutter_cyl(radius,height,center,axis='z',sections=48):
    tm=tm_cylinder(radius=radius,height=height,sections=sections)
    if axis=='x': tm.apply_transform(Ry(90))
    elif axis=='y': tm.apply_transform(Rx(-90))
    tm.apply_translation(center)
    return tm
