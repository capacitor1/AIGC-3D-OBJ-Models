import math
import numpy as np
import trimesh
from pcgen import *

def build_gpu():
    parts={}
    m=Mesh('gpu')
    # PCB
    add_box(m,-55,78,243.5,246.5,-206,120,'pcb_black',0.4)
    # gold fingers
    add_box(m,72.5,78,244.0,246.0,-164,-78,'gold',0.1)
    for i in range(18):
        z=-162+i*4.8
        add_box(m,72.4,78,243.7,246.3,z,z+0.8,'pcb_black',0.05)
    # shroud lower body (side rails / front / rear)
    # open-sided outer shroud with a framed window over the heatsink
    add_box(m,-55,-50,240,245,-205,120,'plastic_black',1.2)
    add_box(m,-55,-50,210,217,-205,120,'plastic_black',1.2)
    add_box(m,-55,-50,217,240,-205,-197,'plastic_black',1.2)
    add_box(m,-55,-50,217,240,112,120,'plastic_black',1.2)
    add_box(m,-55,-50,217,240,-47,-39,'plastic_black',1.0)
    # brushed window frame
    add_box(m,-55.3,-54.6,238,240,-197,112,'brushed',0.35)
    add_box(m,-55.3,-54.6,217,219,-197,112,'brushed',0.35)
    add_box(m,-55.3,-54.6,217,240,-197,-195,'brushed',0.35)
    add_box(m,-55.3,-54.6,217,240,110,112,'brushed',0.35)
    add_box(m,65,70,210,245,-205,120,'plastic_black',1.4)
    add_box(m,-55,70,210,216,-205,-200,'plastic_black',1.2)
    add_box(m,-55,70,210,245,115,120,'plastic_black',1.2)
    add_box(m,-55,70,240,245,-205,120,'plastic_black',1.2)
    # bottom shroud plate with 3 fan holes
    base=tm_chamfer_box(-54,69,210,216,-204,119,1.0)
    cuts=[cutter_cyl(44.5,20,(8,213,z),axis='y',sections=72) for z in (-130,-20,90)]
    res=base
    for c in cuts:
        res=res.difference(c,engine='manifold')
    m.add_tm(res,'plastic_black')
    # fan rings
    for z in (-130,-20,90):
        add_ring(m,46.0,43.8,1.2,(8,210.2,z),'steel_dark',axis='y',sections=72)
        add_ring(m,44.8,43.5,1.0,(8,215.0,z),'plastic_dark',axis='y',sections=72)
    # slim RGB accents on the rails, not across the window
    add_box(m,-55.7,-55.2,241.0,243.2,-190,104,'rgb_magenta',0.15)
    add_box(m,-55.7,-55.2,211.0,213.2,-190,104,'rgb_blue',0.15)
    # illuminated side branding on the window
    M=frame((-54.25,226,-178),(0,0,1),(0,1,0))
    add_text(m,'NXV',8.5,'rgb_cyan',M,0.3)
    M=frame((-54.25,220,-178),(0,0,1),(0,1,0))
    add_text(m,'5090 24GB',4.4,'label_white',M,0.22)
    # small model badge on lower rail
    add_box(m,-55.9,-55.5,213.6,216.2,-188,-162,'brushed',0.15)
    # heatsink fins (dense stack visible through the side window)
    for i in range(92):
        z=-192+i*3.28
        add_box(m,-46,62,217,241,z,z+0.55,'aluminum',0.05)
    # heatpipes
    for x in (-38,-22,-6,10,26,42):
        pts=[(x,228,-196),(x,228,-186),(x,228,-160),(x,228,80),(x,228,100),(x,228,108),
             (x+4,228,114),(x+8,228,108),(x+8,228,100),(x+8,228,-160),(x+8,228,-186),(x+8,228,-196)]
        add_tube(m,pts,2.5,'nickel',sides=10)
    # copper coldplate
    add_box(m,20,68,238,243,-45,25,'copper',0.5)
    # backplate
    add_box(m,-55,70,246,249,-206,120,'steel_black',1.2)
    # backplate vents
    for i in range(12):
        z=-185+i*24
        add_box(m,-45,55,249.0,249.5,z,z+12,'label_dark',0.1)
    for x in (-45,55):
        for z in (-195,105):
            add_screw(m,(x,249.6,z),2.4,0.8,'chrome',axis='y',sections=16)
    # backplate text
    M=frame((-42,249.8,35),(0,0,1),(1,0,0))
    add_text(m,'NXV 5090',7.0,'label_white',M,0.3)
    # rear bracket, extended through the rear panel so the ports are visible
    add_box(m,0,76,194,275,-211,-206,'brushed',0.8)
    add_box(m,-5,72,194,275,-229,-211,'brushed',0.8)
    add_box(m,-5,72,194,275,-232,-229,'aluminum',0.8)
    # bracket vent slots
    for i in range(6):
        y=252+i*3.2
        add_box(m,6,70,y,y+1.4,-232.4,-231.9,'label_dark',0.05)
    # display outputs on the external bracket face
    ports=[(10,'DP'),(26,'DP'),(42,'DP'),(58,'HDMI')]
    for x,name in ports:
        add_box(m,x,x+10,214,222,-212,-208,'chrome',0.3)
        add_box(m,x+1,x+9,215,221,-212.5,-211.2,'label_dark',0.1)
        add_box(m,x+1.5,x+8.5,216,220,-211.8,-211.4,'plastic_grey',0.05)
        add_box(m,x,x+10,214,222,-232.5,-231.3,'chrome',0.3)
        add_box(m,x+1,x+9,215,221,-232.7,-231.6,'label_dark',0.1)
        add_box(m,x+1.5,x+8.5,216,220,-232.8,-232.1,'plastic_grey',0.05)
    M=frame((66,198,-232.6),(-1,0,0),(0,1,0))
    add_text(m,'NXV 5090',4.6,'label_white',M,0.2)
    for x in (-1,70):
        for y in (198,270):
            add_screw(m,(x,y,-232.7),2.2,0.9,'chrome',axis='z',sections=16)
    # 12V-2x6 connector on top
    add_box(m,28,54,249,260,28,46,'plastic_black',0.6)
    add_box(m,30,52,260,262,30,44,'socket',0.3)
    for i in range(6):
        for j in range(2):
            add_box(m,32+i*3.2,33.8+i*3.2,260.2,261.2,31+j*6.2,34+j*6.2,'gold',0.05)
    # screw heads on shroud
    for x in (-48,62):
        for z in (-195,110):
            add_screw(m,(x,211.2,z),2.4,0.9,'chrome',axis='y',sections=16)
    parts['gpu']=m
    return parts

def build_gpu_support():
    m=Mesh('gpu_support')
    # base on PSU shroud
    add_box(m,28,52,121,124,88,108,'steel_dark',0.6)
    add_cylinder(m,4.5,86,(40,164,98),'aluminum',axis='y',sections=28)
    add_cylinder(m,2.6,90,(40,164,98),'steel_light',axis='y',sections=20)
    add_box(m,30,50,205,210,90,106,'rubber',0.8)
    add_ring(m,5.5,3.5,1.2,(40,123,98),'chrome',axis='y',sections=24)
    parts={'gpu_support':m}
    return parts

if __name__=='__main__':
    for k,v in {**build_gpu(),**build_gpu_support()}.items(): print(k,len(v.v),len(v.f))
