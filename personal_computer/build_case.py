import math
import numpy as np
import trimesh
from pcgen import *

def add_hex_grille(mesh, x0,x1,y0,y1,z0,z1, R=6.2, wall=0.9, mat='vent_mesh'):
    """Open honeycomb lattice in the XY plane, extruded through Z."""
    dx=math.sqrt(3.0)*R
    dy=1.5*R
    rows=int((y1-y0)/dy)+2
    cols=int((x1-x0)/dx)+2
    for r in range(-1,rows):
        cy=y0+r*dy
        ox=(r%2)*dx*0.5
        for c in range(-1,cols):
            cx=x0+ox+c*dx
            if cx < x0-R or cx > x1+R or cy < y0-R or cy > y1+R:
                continue
            for k in range(6):
                a0=math.radians(30+60*k)
                a1=math.radians(30+60*(k+1))
                p=[]
                for z in (z0,z1):
                    for rad in (R,R-wall):
                        p.append((cx+rad*math.cos(a0),cy+rad*math.sin(a0),z))
                        p.append((cx+rad*math.cos(a1),cy+rad*math.sin(a1),z))
                base=len(mesh.v)
                for q in p: mesh.add_vertex(*q)
                mesh.add_face((base+0,base+1,base+5,base+4),mat)
                mesh.add_face((base+3,base+2,base+6,base+7),mat)
                mesh.add_face((base+4,base+5,base+7,base+6),mat)
                mesh.add_face((base+2,base+3,base+1,base+0),mat)

def add_rect_grille(mesh, x0,x1,z0,z1,y, pitch_x=8.0, pitch_z=8.0, bar=1.4, height=2.0, mat='vent_mesh'):
    n_x=max(1,int((x1-x0)/pitch_x))
    n_z=max(1,int((z1-z0)/pitch_z))
    for i in range(n_x+1):
        x=x0+i*(x1-x0)/n_x
        add_box(mesh,x-bar/2,x+bar/2,y,y+height,z0,z1,mat)
    for j in range(n_z+1):
        z=z0+j*(z1-z0)/n_z
        add_box(mesh,x0,x1,y,y+height,z-bar/2,z+bar/2,mat)

def add_rounded_rect_grommet(mesh, x, y0,y1,z0,z1, mat='rubber', t=3.0, depth=2.5):
    add_box(mesh,x,x+depth,y0,y0+t,z0,z1,mat,0.6)
    add_box(mesh,x,x+depth,y1-t,y1,z0,z1,mat,0.6)
    add_box(mesh,x,x+depth,y0+t,y1-t,z0,z0+t,mat,0.6)
    add_box(mesh,x,x+depth,y0+t,y1-t,z1-t,z1,mat,0.6)

def build_case():
    parts={}
    # ============================================================ main frame
    m=Mesh('case_frame')
    add_box(m,-112,112,20,25,-226,226,'steel_black',2.0)
    add_box(m,-112,-104,25,34,-226,226,'steel_dark',1.0)
    add_box(m,104,112,25,34,-226,226,'steel_dark',1.0)
    for x0,x1 in ((-112,-106),(106,112)):
        for z0,z1 in ((-226,-220),(220,226)):
            add_box(m,x0,x1,25,465,z0,z1,'steel_black',1.2)
    add_box(m,-112,-88,458,465,-226,226,'steel_black',1.2)
    add_box(m,88,112,458,465,-226,226,'steel_black',1.2)
    add_box(m,-88,88,458,465,-226,-195,'steel_black',1.2)
    add_box(m,-88,88,458,465,55,226,'steel_black',1.2)
    add_box(m,-112,-93,25,458,214,224,'steel_black',1.0)
    add_box(m,93,112,25,458,214,224,'steel_black',1.0)
    add_box(m,-93,93,25,55,214,224,'steel_black',1.0)
    add_box(m,-93,93,420,458,214,224,'steel_black',1.0)
    for x in (-68,64):
        add_box(m,x,x+4,80,450,178,216,'steel_dark',0.6)
        for y in (105,215,325,415):
            add_screw(m,(x+4.2,y,196),2.0,1.0,'chrome',axis='x')
    add_box(m,-112,-100,25,465,-224,-214,'steel_black',1.0)
    add_box(m,100,112,25,465,-224,-214,'steel_black',1.0)
    add_box(m,-100,100,440,465,-224,-214,'steel_black',1.0)
    add_box(m,-100,100,25,40,-224,-214,'steel_black',1.0)
    add_box(m,-60,100,25,30,-220,-56,'steel_dark',0.6)
    add_box(m,-60,-55,25,116,-220,-210,'steel_dark',0.8)
    add_box(m,-60,-55,25,116,-66,-56,'steel_dark',0.8)
    add_box(m,-60,-55,25,30,-220,-56,'steel_dark',0.8)
    add_box(m,95,100,25,116,-220,-56,'steel_dark',0.8)
    for z in (-190,-50,55):
        add_box(m,-100,100,452,458,z-2,z+2,'steel_dark',0.5)
    for x in (-70,70):
        add_box(m,x-2,x+2,452,458,-190,55,'steel_dark',0.5)
    add_ring(m,62,56,4,(-30,385,-222),'steel_dark',axis='z',sections=64)
    for a in (45,135,225,315):
        x=-30+52*math.cos(math.radians(a)); y=385+52*math.sin(math.radians(a))
        add_screw(m,(x,y,-223.5),2.4,1.0,'chrome',axis='z')
    # tray with cutouts
    tray=tm_chamfer_box(84,88,24,462,-224,222,1.5)
    cuts=[
        cutter_box(80,92,270,360,-170,-50),
        cutter_box(80,92,90,180,35,78),
        cutter_box(80,92,220,310,35,78),
        cutter_box(80,92,420,450,-135,-70),
        cutter_box(80,92,30,80,25,80),
    ]
    res=tray
    for c in cuts:
        res=res.difference(c,engine='manifold')
    m.add_tm(res,'steel_black')
    add_rounded_rect_grommet(m,82.0,90,180,35,78,'rubber',3.0,2.4)
    add_rounded_rect_grommet(m,82.0,220,310,35,78,'rubber',3.0,2.4)
    add_rounded_rect_grommet(m,82.0,420,450,-135,-70,'rubber',3.0,2.4)
    add_rounded_rect_grommet(m,82.0,30,80,25,80,'rubber',3.0,2.4)
    board_screws=[(80,125,-190),(80,125,10),(80,395,-190),(80,395,10),
                  (80,230,-110),(80,330,-190),(80,330,10),(80,150,-30),(80,380,-30)]
    for (x,y,z) in board_screws:
        add_hex_screw(m,(80,y,z),4.5,4.0,'nickel',axis='x')
    add_box(m,-108,108,116,121,-222,140,'steel_black',1.6)
    for i in range(18):
        z=-205+i*7.2
        if z>-60: break
        add_box(m,-45,45,121.2,122.2,z,z+3.6,'label_dark',0.2)
    add_box(m,-108,108,20,116,140,145,'steel_black',1.6)
    add_box(m,-108,-104,116,121,-222,140,'aluminum',0.8)
    add_box(m,-108,-104,20,116,140,145,'aluminum',0.8)
    M=frame((-103.8,92,100),(0,0,1),(0,1,0))
    add_text(m,'NXV',7.0,'label_white',M,0.4)
    for y in (40,200,440):
        add_box(m,-100,-94,y-4,y+4,218,224,'steel_dark',0.5)
        add_box(m,94,100,y-4,y+4,218,224,'steel_dark',0.5)
    parts['case_frame']=m

    # ============================================================ right side panel
    m=Mesh('right_panel')
    add_box(m,111,115,24,462,-226,226,'steel_black',2.2)
    add_box(m,114.7,115.5,80,420,-200,200,'steel_dark',0.6)
    for y in (55,430):
        for z in (-195,195):
            add_screw(m,(115.2,y,z),2.8,1.2,'chrome',axis='x')
    parts['right_panel']=m

    # ============================================================ front panel
    m=Mesh('front_panel')
    add_box(m,-115,115,420,465,222,230,'steel_black',2.0)
    add_box(m,-115,115,20,55,222,230,'steel_black',2.0)
    add_box(m,-115,-95,55,420,222,230,'steel_black',2.0)
    add_box(m,95,115,55,420,222,230,'steel_black',2.0)
    add_box(m,-116,-114,55,420,228,233,'aluminum',0.8)
    add_box(m,114,116,55,420,228,233,'aluminum',0.8)
    add_box(m,-116,116,419,421,228,233,'aluminum',0.8)
    add_box(m,-116,116,54,56,228,233,'aluminum',0.8)
    add_hex_grille(m,-93,93,57,418,224.0,229.0,R=6.1,wall=0.85,mat='vent_mesh')
    add_box(m,-95,-91,55,420,223,230,'steel_dark',0.5)
    add_box(m,91,95,55,420,223,230,'steel_dark',0.5)
    add_box(m,-95,95,54,58,223,230,'steel_dark',0.5)
    add_box(m,-95,95,417,421,223,230,'steel_dark',0.5)
    add_box(m,-30,30,426,452,230.0,230.5,'aluminum',0.5)
    M=frame((-20,443,230.6),(1,0,0),(0,1,0))
    add_text(m,'NXV',9.0,'rgb_white',M,0.3)
    M=frame((-20,432,230.6),(1,0,0),(0,1,0))
    add_text(m,'ATX',3.6,'label_dark',M,0.2)
    add_box(m,93.4,95.0,80,400,230.0,230.4,'rgb_cyan',0.1)
    add_box(m,-95.0,-93.4,80,400,230.0,230.4,'rgb_cyan',0.1)
    add_box(m,-24,24,31,43,230,232,'brushed',0.8)
    M=frame((0,37,232.2),(1,0,0),(0,1,0))
    add_text(m,'NXV',6.2,'label_dark',M,0.4)
    add_box(m,-96.5,-94.5,80,400,222.5,224.0,'rgb_cyan',0.2)
    add_box(m,94.5,96.5,80,400,222.5,224.0,'rgb_cyan',0.2)
    for x in (-108,108):
        for y in (30,455):
            add_screw(m,(x,y,230.2),2.8,1.0,'chrome',axis='z')
    parts['front_panel']=m

    # ============================================================ top panel
    m=Mesh('top_panel')
    add_box(m,-115,-88,465,470,-230,230,'steel_black',2.0)
    add_box(m,88,115,465,470,-230,230,'steel_black',2.0)
    add_box(m,-88,88,465,470,-230,-195,'steel_black',2.0)
    add_box(m,-88,88,465,470,90,230,'steel_black',2.0)
    add_rect_grille(m,-86,86,-193,88,467.0,pitch_x=7.0,pitch_z=7.0,bar=1.2,height=2.6,mat='vent_mesh')
    add_box(m,-88,88,470.2,471.2,-195,-193,'brushed',0.4)
    add_box(m,-88,88,470.2,471.2,88,90,'brushed',0.4)
    add_box(m,-88,-86,470.2,471.2,-195,90,'brushed',0.4)
    add_box(m,86,88,470.2,471.2,-195,90,'brushed',0.4)
    # top fan mounting plate with two 140 mm apertures
    base=tm_chamfer_box(-88,88,457,465,-195,90,1.0)
    cuts=[cutter_cyl(68,12,(0,461,z),axis='y',sections=72) for z in (-125,15)]
    res=base
    for c in cuts:
        res=res.difference(c,engine='manifold')
    m.add_tm(res,'steel_black')
    add_box(m,-115,-113,469,472,-230,230,'aluminum',0.8)
    add_box(m,113,115,469,472,-230,230,'aluminum',0.8)
    add_box(m,-115,115,469,472,-230,-228,'aluminum',0.8)
    add_box(m,-115,115,469,472,228,230,'aluminum',0.8)
    add_box(m,-58,58,470,474,150,222,'steel_dark',1.5)
    add_box(m,-52,52,474,475,156,216,'plastic_dark',1.0)
    add_box(m,-24,24,475.0,475.4,176,204,'brushed',0.25)
    M=frame((-19,475.5,199),(1,0,0),(0,0,-1))
    add_text(m,'NXV',7.0,'label_white',M,0.25)
    M=frame((-19,475.5,188),(1,0,0),(0,0,-1))
    add_text(m,'ATX',3.2,'label_dark',M,0.2)
    for x in (-108,108):
        for z in (-220,220):
            add_screw(m,(x,470.5,z),2.8,1.0,'chrome',axis='y')
    parts['top_panel']=m

    # ============================================================ rear panel
    m=Mesh('rear_panel')
    base=tm_chamfer_box(-115,115,20,465,-230,-224,1.8)
    cuts=[
        cutter_cyl(61,20,(-30,385,-227),axis='z',sections=72),
        cutter_box(38,109,330,420,-240,-220),
        cutter_box(-6,72,145,302,-240,-220),
        cutter_box(-58,98,24,116,-240,-220),
    ]
    res=base
    for c in cuts:
        res=res.difference(c,engine='manifold')
    m.add_tm(res,'steel_black')
    add_box(m,-100,-94,25,465,-230,-226,'steel_dark',0.6)
    add_box(m,94,100,25,465,-230,-226,'steel_dark',0.6)
    add_box(m,-100,100,455,465,-230,-226,'steel_dark',0.6)
    add_box(m,-100,100,20,30,-230,-226,'steel_dark',0.6)
    for rad in (16,26,36,46,55):
        add_ring(m,rad,rad-1.1,1.4,(-30,385,-232.2),'chrome',axis='z',sections=64)
    for k in range(8):
        a=math.radians(k*45)
        x=-30+28*math.cos(a); y=385+28*math.sin(a)
        add_box(m,x-0.7,x+0.7,y-0.7,y+0.7,-232.2,-230.8,'chrome')
    add_box(m,36,40,330,420,-232,-226,'brushed',0.4)
    add_box(m,107,111,330,420,-232,-226,'brushed',0.4)
    add_box(m,36,111,420,424,-232,-226,'brushed',0.4)
    add_box(m,36,111,326,330,-232,-226,'brushed',0.4)
    M=frame((105,434,-232.5),(-1,0,0),(0,1,0))
    add_text(m,'USB 3.2',4.0,'label_white',M,0.2)
    M=frame((105,428,-232.5),(-1,0,0),(0,1,0))
    add_text(m,'HDMI / DP',4.0,'label_white',M,0.2)
    M=frame((105,322,-232.5),(-1,0,0),(0,1,0))
    add_text(m,'2.5G LAN',3.6,'label_white',M,0.2)
    M=frame((105,316,-232.5),(-1,0,0),(0,1,0))
    add_text(m,'Wi-Fi 7',3.6,'label_white',M,0.2)
    for i in range(7):
        y0=145+i*21.5
        add_box(m,-5,72,y0,y0+18,-231.5,-226.5,'brushed',0.5)
        for j in range(4):
            add_box(m,6+j*15,16+j*15,y0+5,y0+13,-231.8,-231.2,'label_dark',0.1)
        add_screw(m,(68,y0+9,-231.9),2.0,0.8,'chrome',axis='z')
    add_box(m,-58,-54,24,116,-232,-226,'brushed',0.4)
    add_box(m,94,98,24,116,-232,-226,'brushed',0.4)
    add_box(m,-58,98,24,28,-232,-226,'brushed',0.4)
    M=frame((102,444,-232.5),(-1,0,0),(0,1,0))
    add_text(m,'NXV',6.5,'label_white',M,0.25)
    M=frame((102,437,-232.5),(-1,0,0),(0,1,0))
    add_text(m,'SYSTEM',3.0,'label_dark',M,0.2)
    for y in (35,220,450):
        for x in (-108,108):
            add_screw(m,(x,y,-230.3),2.6,1.0,'chrome',axis='z')
    parts['rear_panel']=m

    # ============================================================ side panel
    m=Mesh('side_panel_glass')
    add_box(m,-119,-114,20,30,-230,230,'steel_black',1.2)
    add_box(m,-119,-114,455,465,-230,230,'steel_black',1.2)
    add_box(m,-119,-114,30,455,-230,-222,'steel_black',1.2)
    add_box(m,-119,-114,30,455,222,230,'steel_black',1.2)
    add_box(m,-117.2,-115.8,30,455,-222,222,'glass',0.4)
    for y in (33,452):
        for z in (-219,219):
            add_box(m,-118.5,-114.8,y-4,y+4,z-8,z+8,'steel_dark',0.6)
            add_screw(m,(-118.8,y,z),3.0,1.0,'chrome',axis='x')
    add_box(m,-119.5,-118.5,440,455,210,220,'aluminum',0.6)
    add_box(m,-119.6,-119.0,30,455,228.4,230.0,'aluminum',0.25)
    add_box(m,-119.6,-119.0,454.0,455.2,-230,230,'aluminum',0.25)
    parts['side_panel_glass']=m

    # ============================================================ feet
    m=Mesh('feet')
    for x in (-92,92):
        for z in (-190,190):
            add_cylinder(m,18,14,(x,7,z),'rubber',axis='y',sections=32)
            add_ring(m,19,15.5,3,(x,16,z),'aluminum',axis='y',sections=40)
            add_box(m,x-14,x+14,14,18,z-14,z+14,'steel_dark',3.0)
    parts['feet']=m

    # ============================================================ front IO
    m=Mesh('front_io')
    add_cylinder(m,9.5,3.0,(-30,476,198),'chrome',axis='y',sections=40)
    add_ring(m,8.0,6.4,1.2,(-30,477.8,198),'rgb_white',axis='y',sections=40)
    add_cylinder(m,6.2,1.4,(-30,478.6,198),'plastic_black',axis='y',sections=40)
    add_cylinder(m,3.0,2.0,(0,476,210),'steel_dark',axis='y',sections=20)
    for x in (14,30):
        add_box(m,x-6,x+6,475,477,204,212,'chrome',0.5)
        add_box(m,x-4.5,x+4.5,476.2,477.2,205.2,210.8,'label_dark',0.2)
        add_box(m,x-4.0,x+4.0,477.0,477.4,206.0,210.0,'plastic_grey',0.1)
    add_box(m,43,53,475,477,204,212,'chrome',0.6)
    add_box(m,45,51,476.0,477.2,205.6,210.4,'label_dark',0.2)
    for x in (-50,-42):
        add_ring(m,3.2,2.0,1.4,(x,476.5,198),'chrome',axis='y',sections=24)
        add_cylinder(m,2.0,1.6,(x,477.0,198),'label_dark',axis='y',sections=20)
    add_box(m,-55,55,475.8,476.4,218,219.2,'label_dark',0.1)
    parts['front_io']=m
    return parts

if __name__=='__main__':
    parts=build_case()
    for k,v in parts.items():
        print(k,len(v.v),len(v.f))
