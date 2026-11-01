import math
import numpy as np
import trimesh
from pcgen import *

_frame_cache={}

def fan_frame_tm(size=120, thickness=25, hole_r=55.5, screw_r=52.5, screw_hole=2.2, mat=None):
    key=(size,thickness,hole_r,screw_r,screw_hole)
    if key in _frame_cache:
        return _frame_cache[key]
    s=size/2; t=thickness/2
    base=tm_chamfer_box(-s,s,-s,s,-t,t,min(3.2,size*0.035))
    cutters=[cutter_cyl(hole_r,thickness+4,(0,0,0),axis='z',sections=72)]
    for x in (-screw_r,screw_r):
        for y in (-screw_r,screw_r):
            cutters.append(cutter_cyl(screw_hole,thickness+4,(x,y,0),axis='z',sections=16))
    res=base
    for c in cutters:
        res=res.difference(c,engine='manifold')
    _frame_cache[key]=res
    return res

def add_blade(mesh, theta0, hub_r, tip_r, z_pitch, mat, steps=9, chord_root=8.0, chord_tip=12.5, thick=0.75):
    # local fan axis z.  Curved, pitched blade as a thin shell.
    # sample radial sections and three chord positions
    grid=[]
    for i in range(steps+1):
        u=i/steps
        r=hub_r+(tip_r-hub_r)*u
        sweep=0.52*u
        chord=chord_root+(chord_tip-chord_root)*u
        da=(chord*0.5)/r
        row=[]
        for v in (-1.0,0.0,1.0):
            ang=theta0+sweep+v*da
            zc=v*(2.2+2.3*u)
            row.append((r*math.cos(ang),r*math.sin(ang),zc))
        grid.append(row)
    # surfaces + thickness
    base=len(mesh.v)
    for side in (-1,1):
        for row in grid:
            for (x,y,z) in row:
                mesh.add_vertex(x,y,z+side*thick*0.5)
    def idx(side,i,j):
        return base + side*((steps+1)*3) + i*3 + j
    for side in (-1,1):
        for i in range(steps):
            for j in range(2):
                a=idx(side,i,j); b=idx(side,i,j+1); c=idx(side,i+1,j+1); d=idx(side,i+1,j)
                if side==1: mesh.add_face((a,b,c,d),mat)
                else: mesh.add_face((a,d,c,b),mat)
    # side walls: leading/trailing edges and root/tip
    for i in range(steps):
        for j in (0,2):
            a=idx(-1,i,j); b=idx(1,i,j); c=idx(1,i+1,j); d=idx(-1,i+1,j)
            mesh.add_face((a,b,c,d),mat)
    for j in range(2):
        a=idx(-1,0,j); b=idx(1,0,j); c=idx(1,0,j+1); d=idx(-1,0,j+1)
        mesh.add_face((a,d,c,b),mat)
        a=idx(-1,steps,j); b=idx(1,steps,j); c=idx(1,steps,j+1); d=idx(-1,steps,j+1)
        mesh.add_face((a,b,c,d),mat)

def make_fan(size=120, thickness=25, blades=9, hub_r=18, tip_r=53.5, rgb='rgb_cyan',
             blade_mat='fan_blade', frame_mat='plastic_black', gpu=False, cable=True):
    m=Mesh('fan')
    hole_r=tip_r+2.0
    screw_r=size/2-7.5 if not gpu else size/2-5
    # frame
    frame_mesh=fan_frame_tm(size,thickness,hole_r,screw_r,2.2)
    m.add_tm(frame_mesh,frame_mat)
    # front and rear lips
    lip_mat='steel_dark' if not gpu else frame_mat
    add_ring(m,hole_r+2.0,hole_r,1.8,(0,0,thickness/2-0.9),lip_mat,axis='z',sections=72)
    add_ring(m,hole_r+2.0,hole_r,1.8,(0,0,-thickness/2+0.9),lip_mat,axis='z',sections=72)
    add_ring(m,hole_r+2.1,hole_r+1.3,0.45,(0,0,thickness/2+0.05),'aluminum',axis='z',sections=72)
    if not gpu:
        s2=size/2
        for (x0,x1,y0,y1) in ((-s2,s2,s2-2.0,s2),(-s2,s2,-s2,-s2+2.0),(-s2,-s2+2.0,-s2,s2),(s2-2.0,s2,-s2,s2)):
            add_box(m,x0,x1,y0,y1,thickness/2-0.15,thickness/2+0.35,'steel_dark',0.25)
    # blades
    for b in range(blades):
        add_blade(m,2*math.pi*b/blades,hub_r,tip_r,0,blade_mat,steps=9,
                  chord_root=7.5 if not gpu else 6.5,chord_tip=12.5 if not gpu else 10.5,
                  thick=0.8)
    # hub
    add_cylinder(m,hub_r,thickness*0.88,(0,0,0),frame_mat,axis='z',sections=48)
    add_ring(m,hub_r+0.3,hub_r-2.2,1.2,(0,0,thickness/2-0.4),frame_mat,axis='z',sections=48)
    add_cylinder(m,hub_r-2.6,0.8,(0,0,thickness/2+0.15),rgb,axis='z',sections=48)
    add_text(m,'NXV',hub_r*0.55,'label_dark',frame((0,-hub_r*0.3,thickness/2+0.6),(1,0,0),(0,1,0)),0.3)
    # ARGB diffuser ring
    if not gpu:
        add_ring(m,hole_r-1.2,hole_r-4.0,1.4,(0,0,thickness/2+0.55),rgb,axis='z',sections=72)
        add_ring(m,hole_r-1.2,hole_r-4.0,1.4,(0,0,-thickness/2-0.55),rgb,axis='z',sections=72)
    else:
        add_ring(m,hub_r+0.5,hub_r-1.2,1.0,(0,0,thickness/2+0.35),rgb,axis='z',sections=48)
    # screws
    for x in (-screw_r,screw_r):
        for y in (-screw_r,screw_r):
            add_screw(m,(x,y,thickness/2+0.4),2.8,1.2,'chrome',axis='z',sections=16)
    if cable:
        pts=[(screw_r+2, -screw_r, -thickness/2+1),(screw_r+8,-screw_r-3,-thickness/2-1),
             (screw_r+12,-screw_r-9,-thickness/2-2),(screw_r+10,-screw_r-16,-thickness/2-1)]
        add_tube(m,pts,1.2,'sleeve_black',sides=8)
    return m

def build_fans():
    parts={}
    # AIO 120 fans, local axis +Z, front toward +Z
    for i,y in enumerate((143,263,383),1):
        f=make_fan(120,25,9,18,53.5,'rgb_cyan','fan_blade','aluminum',False,True)
        parts[f'aio_fan_{i}']=f.transform(T(0,y,163.5))
    # rear exhaust 120, front toward -Z (inside case)
    f=make_fan(120,25,9,18,53.5,'rgb_magenta','fan_blade','aluminum',False,True)
    parts['rear_fan']=f.transform(T(-30,385,-211.5) @ Rz(180))
    # top exhaust 140 fans, local +Z -> world +Y
    for i,z in enumerate((-125,15),1):
        f=make_fan(140,25,9,21,63.5,'rgb_cyan','fan_blade','aluminum',False,True)
        parts[f'top_fan_{i}']=f.transform(T(0,444.5,z) @ Rx(-90))
    # GPU fans, local +Z -> world -Y, front facing down
    for i,z in enumerate((-130,-20,90),1):
        f=make_fan(90,14,9,14,41.5,'rgb_blue','fan_blade_black','plastic_black',True,True)
        parts[f'gpu_fan_{i}']=f.transform(T(8,217,z) @ Rx(90))
    return parts

if __name__=='__main__':
    parts=build_fans()
    for k,v in parts.items(): print(k,len(v.v),len(v.f))
