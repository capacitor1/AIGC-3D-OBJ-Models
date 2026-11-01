import math
import numpy as np
import trimesh
from pcgen import *

def build_psu():
    parts={}
    m=Mesh('psu')
    # main body
    add_box(m,-55,95,28,114,-218,-58,'steel_black',1.5)
    # side label plate
    add_box(m,-56.2,-55.5,48,104,-205,-70,'brushed',0.8)
    M=frame((-56.4,92,-196),(0,0,1),(0,1,0))
    add_text(m,'NXV',8.0,'label_white',M,0.35)
    M=frame((-56.4,80,-196),(0,0,1),(0,1,0))
    add_text(m,'TITAN 1000W',5.6,'label_white',M,0.3)
    M=frame((-56.4,62,-196),(0,0,1),(0,1,0))
    add_text(m,'80+ PLATINUM',3.6,'label_white',M,0.25)
    # small rating badge
    add_box(m,-56.5,-55.8,52,58,-110,-80,'label_white',0.2)
    # bottom fan grille
    add_ring(m,58,55,1.2,(20,27.2,-138),'steel_dark',axis='y',sections=64)
    for rad in (18,30,42):
        add_ring(m,rad,rad-1.0,1.0,(20,27.2,-138),'chrome',axis='y',sections=48)
    for k in range(7):
        a=math.radians(k*360/7)
        x=20+34*math.cos(a); z=-138+34*math.sin(a)
        add_box(m,x-1.2,x+1.2,26.8,27.8,z-1.2,z+1.2,'chrome')
    add_cylinder(m,14,2.0,(20,27.0,-138),'label_dark',axis='y',sections=32)
    # rear face
    add_box(m,-55,95,28,114,-220,-218,'steel_dark',0.8)
    # IEC socket
    add_box(m,58,88,42,76,-221.5,-218.5,'plastic_black',0.6)
    add_box(m,62,84,48,70,-222,-220.8,'label_dark',0.2)
    for y in (53,61,69):
        add_box(m,66,80,y-1.2,y+1.2,-222.4,-221.2,'gold',0.05)
    # switch
    add_box(m,42,54,52,68,-221.8,-218.5,'plastic_black',0.4)
    add_box(m,45,51,55,65,-222.0,-221.6,'label_red',0.1)
    # rear label plate
    add_box(m,-52,44,82,112,-222.4,-221.9,'brushed',0.3)
    M=frame((36,103,-222.6),(-1,0,0),(0,1,0))
    add_text(m,'NXV',8.0,'label_white',M,0.2)
    M=frame((36,94,-222.6),(-1,0,0),(0,1,0))
    add_text(m,'TITAN 1000W',8.0,'label_white',M,0.2)
    M=frame((36,86,-222.6),(-1,0,0),(0,1,0))
    add_text(m,'80+ PLATINUM',6.0,'label_white',M,0.2)
    # lower rear vent plate
    add_box(m,-50,34,56,82,-222.3,-221.9,'brushed',0.2)
    for i in range(7):
        y=58+i*3.3
        add_box(m,-47,31,y,y+1.6,-222.45,-222.15,'label_dark',0.05)
    # rear vent honeycomb-ish slots
    for i in range(8):
        y=30+i*3.0
        add_box(m,-48,32,y,y+1.4,-221.5,-219.0,'label_dark',0.05)
    # modular panel
    add_box(m,-52,92,31,111,-58,-55,'plastic_black',0.5)
    # sockets
    def socket(x0,x1,y0,y1,cols,rows,label):
        add_box(m,x0,x1,y0,y1,-55.2,-54.0,'socket',0.3)
        add_box(m,x0+1,x1-1,y0+1,y1-1,-54.6,-54.1,'label_dark',0.1)
        for i in range(cols):
            for j in range(rows):
                add_box(m,x0+2.0+i*(x1-x0-4)/max(1,cols-1)-0.6,
                        x0+2.6+i*(x1-x0-4)/max(1,cols-1),
                        y0+2.0+j*(y1-y0-4)/max(1,rows-1)-0.6,
                        y0+2.6+j*(y1-y0-4)/max(1,rows-1),
                        -54.8,-54.2,'gold',0.03)
    socket(58,88,82,104,12,2,'24pin')
    socket(28,54,88,104,8,2,'eps1')
    socket(28,54,70,86,8,2,'eps2')
    socket(-5,24,88,104,6,2,'pcie1')
    socket(-5,24,70,86,6,2,'pcie2')
    socket(-5,24,52,68,6,2,'pcie3')
    socket(-48,-20,82,100,5,2,'sata1')
    socket(-48,-20,62,80,5,2,'sata2')
    socket(-48,-20,42,60,5,2,'sata3')
    # small labels
    M=frame((60,105.0,-54.5),(1,0,0),(0,1,0))
    add_text(m,'ATX 24P',3.0,'label_white',M,0.2)
    M=frame((30,105.0,-54.5),(1,0,0),(0,1,0))
    add_text(m,'CPU',3.0,'label_white',M,0.2)
    # feet
    for x in (-45,85):
        for z in (-208,-68):
            add_box(m,x-6,x+6,24,28,z-6,z+6,'rubber',1.0)
    # rear screws
    for x in (-48,88):
        for y in (34,108):
            add_screw(m,(x,y,-220.5),2.6,1.0,'chrome',axis='z',sections=16)
    parts['psu']=m
    return parts

def build_storage():
    parts={}
    s=Mesh('ssd_2_5')
    # 2.5-inch SSD on PSU shroud
    add_box(s,-90,10,121,128,45,115,'ssd',0.8)
    add_box(s,-88,8,128.0,128.8,47,113,'ssd_label',0.4)
    M=frame((-80,129.0,105),(0,0,1),(1,0,0))
    add_text(s,'NXV SSD 4TB',5.0,'label_white',M,0.25)
    M=frame((-90.15,124.6,52),(0,0,1),(0,1,0))
    add_text(s,'NXV SSD 4TB',3.8,'label_white',M,0.2)
    add_box(s,-90.2,-89.9,121.2,122.0,46,114,'aluminum',0.1)
    # SATA connectors on rear edge
    add_box(s,-68,-54,123,127,115,118,'plastic_black',0.3)
    add_box(s,-46,-32,123,127,115,118,'plastic_black',0.3)
    for x in (-62,-40):
        add_box(s,x-4,x+4,124,126,116.5,118.0,'gold',0.05)
    for x in (-84,4):
        for z in (52,108):
            add_screw(s,(x,128.4,z),2.2,0.8,'chrome',axis='y',sections=16)
    parts['ssd_2_5']=s

    h=Mesh('hdd_3_5')
    # 3.5-inch HDD in basement, visible from open side
    add_box(h,-45,55,30,56,45,135,'steel_black',1.0)
    add_box(h,-43,53,56,57,47,133,'brushed',0.4)
    M=frame((-36,57.2,120),(0,0,1),(1,0,0))
    add_text(h,'NXV 8TB HDD',4.5,'label_white',M,0.25)
    M=frame((-45.15,42,52),(0,0,1),(0,1,0))
    add_text(h,'NXV 8TB HDD',4.0,'label_white',M,0.2)
    add_box(h,-45.2,-44.9,31,32,46,134,'aluminum',0.1)
    add_box(h,0,30,32,54,133,136,'plastic_black',0.3)
    for x in (4,18):
        add_box(h,x,x+10,36,50,135.5,137,'gold',0.1)
    parts['hdd_3_5']=h
    return parts

if __name__=='__main__':
    for k,v in {**build_psu(),**build_storage()}.items(): print(k,len(v.v),len(v.f))
