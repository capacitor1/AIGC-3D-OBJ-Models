import math
import numpy as np
import trimesh
from pcgen import *

def add_pin_grid(mesh, x, y0, z0, rows, cols, pitch_y, pitch_z, mat='gold', pin_r=0.35, pin_h=0.8):
    for i in range(rows):
        for j in range(cols):
            y=y0+i*pitch_y; z=z0+j*pitch_z
            add_cylinder(mesh,pin_r,pin_h,(x,y,z),mat,axis='x',sections=6)

def build_motherboard():
    parts={}
    m=Mesh('motherboard')
    # PCB
    add_box(m,74,78,105,410,-212,32,'pcb_black',0.8)
    # gold edge traces
    add_box(m,73.9,74.15,108,407,-211,-210,'gold',0.1)
    add_box(m,73.9,74.15,108,407,30.8,31.8,'gold',0.1)
    add_box(m,73.9,74.15,105.2,106.2,-210,30,'gold',0.1)
    # board silkscreen stripes
    for z in (-200,-150,-100,-50,0):
        add_box(m,73.85,73.95,108,112,z,z+25,'label_white',0.05)
    # mounting screws
    for (y,z) in [(125,-190),(125,10),(395,-190),(395,10),(230,-110),(330,-190),(330,10),(150,-30),(380,-30)]:
        add_screw(m,(78.6,y,z),3.8,1.2,'nickel',axis='x',sections=20)
    # CPU socket assembly
    add_box(m,74,78,292,340,-136,-88,'socket',0.5)
    # socket frame bars
    add_box(m,73.5,78,292,340,-136,-132,'steel_dark',0.3)
    add_box(m,73.5,78,292,340,-92,-88,'steel_dark',0.3)
    add_box(m,73.5,78,292,296,-132,-92,'steel_dark',0.3)
    add_box(m,73.5,78,336,340,-132,-92,'steel_dark',0.3)
    # CPU IHS
    add_box(m,73.2,77.0,301,331,-125,-99,'nickel',0.6)
    add_box(m,73.1,73.4,303,329,-123,-101,'chrome',0.3)
    # retention arm
    add_box(m,73.0,73.6,288,292,-130,-94,'chrome',0.2)
    add_box(m,73.0,73.6,340,344,-130,-94,'chrome',0.2)
    add_box(m,73.0,73.4,288,344,-96,-94,'chrome',0.2)
    # VRM top bank
    add_box(m,74,56,356,402,-200,-62,'steel_black',1.2)
    for i in range(13):
        z=-196+i*10.6
        add_box(m,55.5,53.5,360,398,z,z+1.3,'steel_dark',0.15)
    # VRM rear bank
    add_box(m,74,56,268,352,-206,-174,'steel_black',1.2)
    for i in range(9):
        y=272+i*8.8
        add_box(m,55.5,53.5,y,y+1.2,-202,-178,'steel_dark',0.15)
    # heatpipe across VRM
    add_tube(m,[(58,358,-188),(58,354,-170),(58,352,-150),(58,352,-120),(58,354,-95),(58,358,-72)],3.2,'nickel',sides=12)
    # I/O shroud
    add_box(m,74,46,352,410,-216,-186,'plastic_dark',1.5)
    add_box(m,74,46,352,360,-216,-186,'plastic_black',0.5)
    add_box(m,46.2,45.6,356,406,-212,-190,'rgb_cyan',0.3)
    M=frame((45.4,382,-199),(0,0,1),(0,1,0))
    add_text(m,'NXV',8.0,'label_white',M,0.4)
    # rear I/O ports on board
    # USB-A pair
    for y in (354,366):
        add_box(m,56,72,y,y+8,-222,-210,'chrome',0.4)
        add_box(m,57,71,y+1,y+7,-223,-221.5,'label_dark',0.2)
        add_box(m,58,70,y+2,y+6,-222.5,-221.8,'plastic_grey',0.1)
    # USB-C
    add_box(m,42,50,354,362,-222,-210,'chrome',0.5)
    add_box(m,43.5,48.5,355.5,360.5,-223,-221.5,'label_dark',0.2)
    # HDMI
    add_box(m,56,72,380,390,-222,-210,'chrome',0.5)
    add_box(m,58,70,382,388,-223,-221.5,'label_dark',0.2)
    # DisplayPort
    add_box(m,42,54,380,390,-222,-210,'chrome',0.5)
    add_box(m,44,52,382,388,-223,-221.5,'label_dark',0.2)
    # RJ45
    add_box(m,56,72,396,406,-222,-210,'chrome',0.4)
    add_box(m,58,70,398,404,-223,-221.5,'label_dark',0.2)
    # audio jacks
    for y in (396,404):
        add_cylinder(m,3.5,10,(46,y,-216),'chrome',axis='z',sections=20)
        add_cylinder(m,2.2,1.2,(46,y,-221.5),'label_dark',axis='z',sections=16)
    # antenna connectors
    for y in (358,366):
        add_cylinder(m,2.0,8,(39,y,-216),'gold',axis='z',sections=16)
    # BIOS button
    add_cylinder(m,2.2,5,(46,350,-216),'label_red',axis='z',sections=16)
    # RAM slots
    ram_z=(-44,-34,-24,-14)
    for z in ram_z:
        add_box(m,74,78,232,376,z-4,z+4,'socket',0.3)
        add_box(m,73.7,74.1,236,372,z-2.2,z+2.2,'gold',0.1)
        add_box(m,74,78,230,236,z-4,z+4,'plastic_grey',0.4)
        add_box(m,74,78,370,376,z-4,z+4,'plastic_grey',0.4)
        # clips
        add_box(m,72.8,74.2,230,238,z-3,z+3,'plastic_black',0.4)
        add_box(m,72.8,74.2,368,376,z-3,z+3,'plastic_black',0.4)
    # RAM modules
    for i,z in enumerate(ram_z,1):
        x_out=34
        add_box(m,x_out,77.0,240,370,z-3.4,z+3.4,'steel_black',0.6)
        # heatspreader ridges
        for k in range(7):
            y=250+k*16
            add_box(m,x_out-0.5,x_out+0.2,y,y+2.0,z-3.5,z+3.5,'steel_dark',0.15)
        # silver top cap
        add_box(m,x_out,77,366,372,z-3.6,z+3.6,'aluminum',0.5)
        # RGB diffuser on the visible side
        add_box(m,x_out-0.7,x_out-0.2,246,364,z-1.2,z+1.2,('rgb_cyan' if i%2 else 'rgb_white'),0.1)
        # label
        M=frame((x_out-0.8,300,z-3.5),(0,0,1),(0,1,0))
        add_text(m,'NXV',3.2,'label_white',M,0.2)
    # PCIe slots
    pcie_y=(245,215,185,155)
    for idx,y in enumerate(pcie_y):
        add_box(m,74,78,y-3,y+3,-170,-78,'socket',0.3)
        add_box(m,73.7,74.1,y-1.2,y+1.2,-166,-82,'gold',0.1)
        add_box(m,74,78,y-4,y+4,-78,-70,'plastic_grey',0.4)
        add_box(m,74,78,y-4,y+4,-174,-170,'plastic_grey',0.4)
        if idx==0:
            # metal reinforced slot
            add_box(m,73.4,74.4,y-5,y+5,-175,-70,'nickel',0.3)
            add_box(m,73.2,73.6,y-5,y-3,-175,-70,'chrome',0.2)
            add_box(m,73.2,73.6,y+3,y+5,-175,-70,'chrome',0.2)
    # chipset heatsink
    add_box(m,74,48,145,205,-68,0,'steel_black',1.4)
    for i in range(9):
        y=150+i*5.8
        add_box(m,47.8,46.5,y,y+1.0,-62,-5,'steel_dark',0.15)
    add_box(m,47.6,46.8,160,190,-50,-15,'rgb_magenta',0.2)
    M=frame((46.5,174,-32),(0,0,1),(0,1,0))
    add_text(m,'NXV',8.0,'label_white',M,0.4)
    # M.2 shields
    add_box(m,74,66,126,160,-180,-92,'brushed',1.0)
    add_box(m,74,66,118,146,-34,20,'brushed',1.0)
    for y,z in [(130,-170),(130,-100),(122,-20)]:
        add_screw(m,(65.6,y,z),2.2,0.8,'chrome',axis='x',sections=16)
    M=frame((65.7,142,-136),(0,0,1),(0,1,0))
    add_text(m,'M.2',5.0,'label_dark',M,0.3)
    M=frame((65.7,130,-8),(0,0,1),(0,1,0))
    add_text(m,'M.2',5.0,'label_dark',M,0.3)
    # 24-pin header
    add_box(m,74,58,250,292,19,32,'plastic_black',0.5)
    add_box(m,74,60,254,288,32,34,'socket',0.2)
    add_pin_grid(m,58.4,255,21.5,12,2,3.0,5.2,'gold',0.3,0.8)
    # EPS 8-pin
    add_box(m,74,58,390,404,-146,-108,'plastic_black',0.5)
    add_pin_grid(m,58.4,393,-143,4,2,3.2,10.0,'gold',0.3,0.8)
    # SATA ports
    for i in range(4):
        z=8+i*6.0
        add_box(m,74,66,112,126,z,z+4.6,'plastic_black',0.3)
        add_box(m,73.5,74.0,114,124,z+1,z+3.6,'gold',0.1)
    # front panel header and USB headers
    add_box(m,74,66,108,122,-18,8,'plastic_black',0.3)
    add_pin_grid(m,66.5,111,-14,2,5,4.0,4.5,'gold',0.3,0.6)
    add_box(m,74,66,108,118,12,20,'plastic_black',0.3)
    add_box(m,74,66,128,138,12,20,'plastic_black',0.3)
    # fan headers
    for y in (130,200,330):
        add_box(m,74,70,y,y+5,-52,-46,'plastic_black',0.2)
        add_pin_grid(m,70.4,y+1,-50,1,4,0,1.4,'gold',0.25,0.6)
    # capacitors around VRM
    for (y,z) in [(270,-160),(280,-160),(290,-160),(300,-160),(310,-160),(320,-160),(340,-150),(350,-150)]:
        add_cylinder(m,4.0,10,(72,y,z),'capacitor',axis='x',sections=24)
        add_ring(m,4.0,3.2,0.6,(67.0,y,z),'chrome',axis='x',sections=24)
    # small SMD components
    for i in range(30):
        y=120+((i*37)%280)
        z=-205+((i*53)%225)
        if y>360 and z>-210: continue
        add_box(m,73.7,74.0,y,y+2.0,z,z+1.2,'label_dark',0.05)
    # board text
    M=frame((73.8,168,18),(0,0,1),(0,1,0))
    add_text(m,'NXV Z790',5.0,'label_white',M,0.25)
    parts['motherboard']=m

    # CPU (separate)
    c=Mesh('cpu')
    add_box(c,73.0,77.4,301,331,-125,-99,'nickel',0.6)
    add_box(c,72.9,73.2,303,329,-123,-101,'chrome',0.3)
    add_text(c,'NXV',3.0,'label_dark',frame((72.8,316,-112),(0,0,1),(0,1,0)),0.2)
    parts['cpu']=c
    return parts

if __name__=='__main__':
    parts=build_motherboard()
    for k,v in parts.items(): print(k,len(v.v),len(v.f))
