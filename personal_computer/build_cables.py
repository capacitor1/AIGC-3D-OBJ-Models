import math
import numpy as np
import trimesh
from pcgen import *

def cable(mesh, pts, radius, mat='sleeve_black', sides=18):
    add_tube(mesh,pts,radius,mat,sides=sides)

def connector_box(mesh,x0,x1,y0,y1,z0,z1,mat='plastic_black',pins=None):
    add_box(mesh,x0,x1,y0,y1,z0,z1,mat,0.5)
    # recessed face
    add_box(mesh,x0+0.7,x1-0.7,y0+0.7,y1-0.7,z1-0.8,z1+0.05,'label_dark',0.2)
    if pins:
        for i in range(pins[0]):
            for j in range(pins[1]):
                yy=y0+2.0+i*(y1-y0-4)/max(1,pins[0]-1)
                zz=z0+2.0+j*(z1-z0-4)/max(1,pins[1]-1)
                add_box(mesh,x0+1.2,x0+2.0,yy-0.5,yy+0.5,zz-0.5,zz+0.5,'gold',0.05)

def build_cables():
    parts={}
    # ---------------- 24-pin ATX
    m=Mesh('cable_24pin')
    pts=[(60,85,-58),(75,88,-52),(86,98,-38),(94,120,-18),(96,170,8),
         (96,235,45),(92,265,56),(84,272,52),(72,275,42),(58,274,33),(50,272,25)]
    cable(m,pts,7.2,'sleeve_grey',20)
    # connector at motherboard
    connector_box(m,50,58,252,290,19,32,'plastic_black',(12,2))
    # connector at PSU
    connector_box(m,58,88,82,104,-62,-54,'plastic_black',(12,2))
    # cable comb
    add_box(m,92.0,99.5,180,186,18,31,'brushed',1.0)
    add_box(m,92.0,99.5,225,231,42,55,'brushed',1.0)
    parts['cable_24pin']=m

    # ---------------- EPS 8-pin
    m=Mesh('cable_eps')
    pts=[(36,96,-58),(56,98,-52),(78,110,-36),(94,150,-18),(98,250,-32),
         (100,380,-55),(98,425,-78),(88,437,-98),(72,432,-116),(58,414,-126),(50,397,-127)]
    cable(m,pts,5.8,'sleeve_grey',18)
    connector_box(m,50,58,390,404,-146,-108,'plastic_black',(4,2))
    connector_box(m,28,54,88,104,-62,-54,'plastic_black',(4,2))
    add_box(m,95.0,101.0,300,306,-55,-43,'plastic_black',0.8)
    parts['cable_eps']=m

    # ---------------- 12V-2x6 GPU
    m=Mesh('cable_gpu')
    pts=[(10,78,-58),(30,88,-44),(50,105,-25),(62,130,5),(70,165,45),
         (72,195,95),(72,210,125),(70,238,135),(64,256,134),(58,267,124),
         (54,270,100),(52,266,70),(52,262,44)]
    cable(m,pts,6.5,'sleeve_grey',18)
    connector_box(m,28,54,260,268,28,46,'plastic_black',(6,2))
    connector_box(m,-5,24,70,86,-62,-54,'plastic_black',(6,2))
    add_box(m,80.5,87.5,180,186,8,20,'brushed',0.8)
    add_box(m,62,72,244,252,128,136,'brushed',0.8)
    parts['cable_gpu']=m

    # ---------------- SATA power + data
    m=Mesh('cable_sata')
    pwr=[(-30,62,-58),(-40,72,-45),(-52,92,-18),(-58,112,18),(-60,122,55),(-60,124,112),(-60,124,118)]
    cable(m,pwr,3.6,'sleeve_black',14)
    connector_box(m,-64,-56,122,127,112,118,'plastic_black',None)
    connector_box(m,-44,-20,62,80,-62,-54,'plastic_black',(5,2))
    data=[(-58,124,118),(-40,130,108),(-10,138,90),(20,140,68),(44,136,48),(60,130,34),(68,124,28),(70,120,20)]
    cable(m,data,3.2,'sleeve_grey',14)
    connector_box(m,-64,-56,123,127,114,119,'plastic_black',None)
    parts['cable_sata']=m

    # ---------------- front panel / USB / audio bundle
    m=Mesh('cable_front_panel')
    pts=[(-30,474,200),(-44,464,194),(-62,446,178),(-78,410,155),(-84,350,130),
         (-82,280,100),(-70,210,78),(-45,170,58),(-10,145,42),(24,132,28),(50,122,16),(62,116,6)]
    cable(m,pts,2.4,'sleeve_black',10)
    # front panel header
    connector_box(m,62,70,108,122,-18,8,'plastic_black',(2,5))
    # USB/audio headers
    add_box(m,62,68,108,118,12,20,'plastic_black',0.3)
    add_box(m,62,68,128,138,12,20,'plastic_black',0.3)
    parts['cable_front_panel']=m

    # ---------------- AIO pump fan/ARGB cable
    m=Mesh('cable_aio')
    pts=[(55,350,-145),(60,365,-160),(66,380,-175),(70,390,-165),(70,395,-150),(68,398,-145)]
    cable(m,pts,2.0,'sleeve_black',8)
    parts['cable_aio']=m
    return parts

if __name__=='__main__':
    for k,v in build_cables().items(): print(k,len(v.v),len(v.f))
