#!/usr/bin/env python3
import os, json, shutil
from collections import OrderedDict
from pcgen import MATERIALS
from build_case import build_case
from build_motherboard import build_motherboard
from build_gpu import build_gpu, build_gpu_support
from build_fans import build_fans
from build_aio import build_aio
from build_psu import build_psu, build_storage
from build_cables import build_cables

ROOT=os.path.dirname(os.path.abspath(__file__))
COMP=os.path.join(ROOT,'components')

def write_mtl(path):
    lines=['# NXV desktop PC procedural materials','# Units: millimetres','']
    for name,p in MATERIALS.items():
        lines.append(f'newmtl {name}')
        kd=p['kd']; ks=p['ks']
        lines.append('Ka %.6f %.6f %.6f'%(kd[0]*0.25,kd[1]*0.25,kd[2]*0.25))
        lines.append('Kd %.6f %.6f %.6f'%kd)
        lines.append('Ks %.6f %.6f %.6f'%ks)
        lines.append('Ns %.2f'%p['ns'])
        lines.append('d %.4f'%p.get('d',1.0))
        if 'ke' in p:
            ke=p['ke']; lines.append('Ke %.4f %.4f %.4f'%ke)
        lines.append('illum 2')
        lines.append('')
    open(path,'w',encoding='utf-8').write('\n'.join(lines))

def write_obj(path, parts, mtl_name):
    out=['# NXV high-detail desktop gaming PC','# Units: millimetres  +Y up, +Z front, -X open side','mtllib '+mtl_name,'']
    offset=1
    for name,mesh in parts.items():
        if len(mesh.v)==0 or len(mesh.f)==0: continue
        out.append(f'o {name}')
        out.append(f'g {name}')
        for v in mesh.v:
            out.append('v %.5f %.5f %.5f'%v)
        # group faces by material in first-use order
        groups=OrderedDict()
        for f,m in zip(mesh.f,mesh.m):
            groups.setdefault(m,[]).append(f)
        for mat,faces in groups.items():
            out.append('usemtl '+mat)
            for face in faces:
                idx=[a+offset for a in face]
                for i in range(1,len(idx)-1):
                    out.append(f'f {idx[0]} {idx[i]} {idx[i+1]}')
        out.append('')
        offset += len(mesh.v)
    open(path,'w',encoding='utf-8').write('\n'.join(out))
    return len(out)

def main():
    os.makedirs(COMP,exist_ok=True)
    parts=OrderedDict()
    for d in (build_case(),build_motherboard(),build_gpu(),build_gpu_support(),
              build_fans(),build_aio(),build_psu(),build_storage(),build_cables()):
        parts.update(d)
    # side panel is stored but excluded from the open assembly
    side=parts.pop('side_panel_glass')
    open_parts=OrderedDict(parts)
    closed_parts=OrderedDict(parts)
    closed_parts['side_panel_glass']=side
    # place closed side panel at the case
    write_mtl(os.path.join(ROOT,'desktop_pc.mtl'))
    write_obj(os.path.join(ROOT,'desktop_pc_open.obj'),open_parts,'desktop_pc.mtl')
    write_obj(os.path.join(ROOT,'desktop_pc_closed.obj'),closed_parts,'desktop_pc.mtl')
    # individual components
    shutil.copyfile(os.path.join(ROOT,'desktop_pc.mtl'),os.path.join(COMP,'desktop_pc.mtl'))
    for name,mesh in list(open_parts.items())+[('side_panel_glass',side)]:
        write_obj(os.path.join(COMP,name+'.obj'),OrderedDict([(name,mesh)]),'desktop_pc.mtl')
    # assembly manifest
    manifest={
        'name':'NXV ATX Gaming Desktop',
        'units':'millimetres',
        'orientation':{'up':'+Y','front':'+Z','removable_panel':'-X'},
        'overall':{'width':234,'height':478,'depth':464},
        'files':{
            'open':'desktop_pc_open.obj',
            'closed':'desktop_pc_closed.obj',
            'materials':'desktop_pc.mtl',
            'components':'components/*.obj'
        },
        'components':[{'name':k,'vertices':len(v.v),'triangles':len(v.f)} for k,v in list(closed_parts.items())]
    }
    open(os.path.join(ROOT,'assembly.json'),'w',encoding='utf-8').write(json.dumps(manifest,indent=2))
    total_v=sum(len(v.v) for v in closed_parts.values()); total_t=sum(len(v.f) for v in closed_parts.values())
    print('parts',len(closed_parts),'vertices',total_v,'triangles',total_t)
    for k,v in closed_parts.items(): print(f'  {k:22s} {len(v.v):7d} v  {len(v.f):7d} t')

if __name__=='__main__':
    main()
