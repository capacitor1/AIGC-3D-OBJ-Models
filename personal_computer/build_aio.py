import math
import numpy as np
import trimesh
from pcgen import *

def build_aio():
    parts={}
    # ---------------- pump block
    p=Mesh('aio_pump')
    add_cylinder(p,39,2.0,(76.5,315,-110),'nickel',axis='x',sections=64)
    add_cylinder(p,37,32,(60,315,-110),'plastic_black',axis='x',sections=64)
    add_ring(p,38,35,2.0,(44.2,315,-110),'chrome',axis='x',sections=64)
    add_cylinder(p,33,2.2,(43.0,315,-110),'glass',axis='x',sections=64)
    add_ring(p,34.5,30.0,1.6,(43.4,315,-110),'rgb_cyan',axis='x',sections=64)
    add_ring(p,27,24,1.0,(42.4,315,-110),'rgb_magenta',axis='x',sections=64)
    add_cylinder(p,23,0.8,(42.2,315,-110),'label_dark',axis='x',sections=64)
    M=frame((41.8,315,-110),(0,0,1),(0,1,0))
    add_text(p,'NXV',7.5,'label_white',M,0.4)
    # mounting ears
    for y in (283,347):
        for z in (-142,-78):
            add_box(p,43,78,y-5,y+5,z-5,z+5,'steel_dark',0.6)
            add_screw(p,(42.5,y,z),2.8,1.0,'chrome',axis='x',sections=16)
    # rotary fittings at front side
    for y in (334,296):
        add_cylinder(p,9.0,18,(54,y,-70),'chrome',axis='z',sections=28)
        add_ring(p,9.0,7.2,2.0,(54,y,-62),'nickel',axis='z',sections=28)
        add_cylinder(p,7.2,10,(54,y,-72),'sleeve_black',axis='z',sections=20)
    parts['aio_pump']=p

    # ---------------- radiator
    r=Mesh('aio_radiator')
    # side tanks
    add_box(r,-63,-57,84,448,187,211,'radiator',1.0)
    add_box(r,57,63,84,448,187,211,'radiator',1.0)
    # end tanks
    add_box(r,-63,63,84,102,187,211,'radiator',1.2)
    add_box(r,-63,63,430,448,187,211,'radiator',1.2)
    # fin stack
    for i in range(76):
        y=104+i*4.28
        add_box(r,-56,56,y,y+0.55,190,208,'aluminum',0.05)
    # outer frame rails
    add_box(r,-64,-62,100,432,188,210,'steel_dark',0.4)
    add_box(r,62,64,100,432,188,210,'steel_dark',0.4)
    # fan mounting plate with three 120 mm apertures, in front of the core
    base=tm_chamfer_box(-63,63,84,448,176,187,1.0)
    cuts=[cutter_cyl(56,18,(0,y,181),axis='z',sections=72) for y in (143,263,383)]
    res=base
    for c in cuts:
        res=res.difference(c,engine='manifold')
    r.add_tm(res,'steel_dark')
    for y in (143,263,383):
        add_ring(r,58,56,0.8,(0,y,176.2),'aluminum',axis='z',sections=72)
    # top logo
    M=frame((-50,448.4,199),(0,0,1),(1,0,0))
    add_text(r,'AQUA 360',6.0,'label_white',M,0.3)
    # side RGB strip
    add_box(r,-63.4,-62.8,115,420,189,190,'rgb_cyan',0.1)
    add_box(r,62.8,63.4,115,420,189,190,'rgb_cyan',0.1)
    # ports on rear face of top tank
    for x in (55,48):
        add_cylinder(r,9.0,18,(x,440,182),'chrome',axis='z',sections=28)
        add_ring(r,9.0,7.0,2.0,(x,440,174),'nickel',axis='z',sections=28)
        add_cylinder(r,7.0,8,(x,440,190),'sleeve_black',axis='z',sections=20)
    # mounting screws
    for x in (-60,60):
        for y in (105,215,325,425):
            add_screw(r,(x,y,211.2),2.8,1.0,'chrome',axis='z',sections=16)
    parts['aio_radiator']=r

    # ---------------- tubes
    t1=Mesh('aio_tube_1')
    pts1=[(54,334,-70),(54,346,-68),(52,365,-66),(51,382,-52),(51,392,-20),
          (52,398,20),(54,412,70),(57,430,120),(58,442,160),(56,444,184)]
    add_tube(t1,pts1,7.8,'sleeve_grey',sides=20)
    add_ring(t1,9.2,7.6,2.4,pts1[-1],'chrome',axis='z',sections=28)
    parts['aio_tube_1']=t1

    t2=Mesh('aio_tube_2')
    pts2=[(54,296,-70),(52,300,-68),(46,320,-66),(42,350,-62),(40,372,-50),
          (40,388,-15),(42,398,25),(46,415,85),(51,435,135),(52,443,170),(49,444,184)]
    add_tube(t2,pts2,7.8,'sleeve_grey',sides=20)
    add_ring(t2,9.2,7.6,2.4,pts2[-1],'chrome',axis='z',sections=28)
    parts['aio_tube_2']=t2
    return parts

if __name__=='__main__':
    for k,v in build_aio().items(): print(k,len(v.v),len(v.f))
