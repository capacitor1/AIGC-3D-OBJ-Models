import bpy
import bmesh
import math
import os
from math import pi, sin, cos, radians
from mathutils import Vector

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_OBJ = os.path.join(ROOT, "subwoofer_SW12.obj")
OUT_MTL = os.path.join(ROOT, "subwoofer_SW12.mtl")

# ----------------------------------------------------------------------------
# Scene / collections
# ----------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene.render.engine = 'BLENDER_EEVEE_NEXT'

col = bpy.data.collections.new("Subwoofer_SW12")
scene.collection.children.link(col)

# ----------------------------------------------------------------------------
# Materials
# ----------------------------------------------------------------------------
def make_mat(name, color, metallic=0.0, roughness=0.5, emission=None, emission_strength=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    mat.diffuse_color = (*color, 1.0)
    return mat

M = {}
M['cabinet']       = make_mat("Cabinet_Matte_Black", (0.010, 0.010, 0.012), 0.0, 0.38)
M['baffle']        = make_mat("Baffle_Satin_Black", (0.006, 0.006, 0.008), 0.0, 0.24)
M['gloss_black']   = make_mat("Gloss_Black", (0.004, 0.004, 0.006), 0.0, 0.14)
M['rubber']        = make_mat("Rubber_Surround", (0.016, 0.016, 0.018), 0.0, 0.72)
M['cone']          = make_mat("Coated_Paper_Cone", (0.022, 0.020, 0.018), 0.0, 0.82)
M['cone_rib']      = make_mat("Cone_Rib", (0.040, 0.036, 0.032), 0.0, 0.72)
M['dust']          = make_mat("Dust_Cap_Gloss", (0.006, 0.006, 0.008), 0.05, 0.18)
M['spider']        = make_mat("Spider_Fabric", (0.060, 0.043, 0.026), 0.0, 0.92)
M['kapton']        = make_mat("Voice_Coil_Former", (0.22, 0.09, 0.025), 0.0, 0.58)
M['copper']        = make_mat("Copper", (0.56, 0.22, 0.07), 1.0, 0.28)
M['gold']          = make_mat("Gold_Terminal", (0.82, 0.55, 0.18), 1.0, 0.18)
M['aluminum']      = make_mat("Cast_Aluminum", (0.48, 0.50, 0.52), 1.0, 0.30)
M['aluminum_dark'] = make_mat("Dark_Aluminum", (0.22, 0.23, 0.25), 1.0, 0.38)
M['steel']         = make_mat("Brushed_Steel", (0.34, 0.35, 0.37), 1.0, 0.32)
M['dark_metal']    = make_mat("Dark_Metal", (0.055, 0.055, 0.060), 0.75, 0.34)
M['screw']         = make_mat("Screw_Black", (0.012, 0.012, 0.014), 0.55, 0.30)
M['magnet']        = make_mat("Ferrite_Magnet", (0.028, 0.028, 0.032), 0.15, 0.62)
M['plastic']       = make_mat("Black_Plastic", (0.008, 0.008, 0.010), 0.0, 0.42)
M['red']           = make_mat("Red_Terminal", (0.42, 0.012, 0.010), 0.0, 0.38)
M['well']          = make_mat("Internal_Black", (0.0025, 0.0025, 0.003), 0.0, 0.88)
M['led']           = make_mat("LED_Blue", (0.02, 0.15, 0.8), 0.0, 0.2, emission=(0.05, 0.35, 1.0), emission_strength=4.0)

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def assign_mat(obj, mat):
    if mat is not None:
        obj.data.materials.append(mat)

def apply_mod(obj, mod):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)

def bevel(obj, width, segments=3, angle=30.0, apply=True):
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    mod.angle_limit = radians(angle)
    if apply:
        apply_mod(obj, mod)

def shade_smooth(obj, angle=35.0):
    for p in obj.data.polygons:
        p.use_smooth = True
    mod = obj.modifiers.new("EdgeSplit", "EDGE_SPLIT")
    mod.split_angle = radians(angle)
    mod.use_edge_angle = True
    mod.use_edge_sharp = True
    apply_mod(obj, mod)

def add_mesh_obj(name, verts, faces, mat, smooth=True, smooth_angle=35.0):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate(verbose=False)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    assign_mat(obj, mat)
    if smooth:
        shade_smooth(obj, smooth_angle)
    return obj

def revolve_y(name, profile, segments, mat, smooth_angle=35.0, closed=True):
    """Revolve a (radius, y) profile around Y. Driver front is -Y."""
    verts = []
    rings = []
    for r, y in profile:
        if abs(r) < 1e-9:
            idx = len(verts)
            verts.append((0.0, y, 0.0))
            rings.append(('pole', idx))
        else:
            ring = []
            for j in range(segments):
                a = 2.0 * pi * j / segments
                ring.append(len(verts))
                verts.append((r * cos(a), y, r * sin(a)))
            rings.append(('ring', ring))
    faces = []
    n = len(profile)
    limit = n if closed else n - 1
    for i in range(limit):
        j = (i + 1) % n
        t1, d1 = rings[i]
        t2, d2 = rings[j]
        if t1 == 'ring' and t2 == 'ring':
            for k in range(segments):
                k2 = (k + 1) % segments
                faces.append((d1[k], d1[k2], d2[k2], d2[k]))
        elif t1 == 'pole' and t2 == 'ring':
            for k in range(segments):
                k2 = (k + 1) % segments
                faces.append((d1, d2[k], d2[k2]))
        elif t1 == 'ring' and t2 == 'pole':
            for k in range(segments):
                k2 = (k + 1) % segments
                faces.append((d1[k], d1[k2], d2))
    return add_mesh_obj(name, verts, faces, mat, True, smooth_angle)

def rounded_box(name, size, loc, radius, mat, segments=3, rot=(0, 0, 0), smooth_angle=30.0):
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (size[0] / 2.0, size[1] / 2.0, size[2] / 2.0)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel(obj, radius, segments=segments, angle=30.0, apply=True)
    shade_smooth(obj, smooth_angle)
    obj.location = loc
    obj.rotation_euler = rot
    assign_mat(obj, mat)
    return obj

def cylinder(name, radius, depth, loc, mat, verts=64, rot=(0, 0, 0), bevel_width=0.0, bevel_segments=3, smooth_angle=30.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth,
                                        end_fill_type='NGON', location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    if bevel_width > 0:
        bevel(obj, bevel_width, segments=bevel_segments, angle=30.0, apply=True)
    shade_smooth(obj, smooth_angle)
    obj.location = loc
    obj.rotation_euler = rot
    assign_mat(obj, mat)
    return obj

def torus(name, major, minor, loc, mat, major_segments=128, minor_segments=18,
          rot=(0, 0, 0), axial_scale=1.0, smooth_angle=35.0):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=major_segments,
                                     minor_segments=minor_segments,
                                     location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    if abs(axial_scale - 1.0) > 1e-9:
        obj.scale = (1.0, 1.0, axial_scale)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    shade_smooth(obj, smooth_angle)
    obj.location = loc
    obj.rotation_euler = rot
    assign_mat(obj, mat)
    return obj

def cutter_cylinder(radius, depth, loc, verts=48, rot=(pi / 2.0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth,
                                        end_fill_type='NGON', location=loc,
                                        rotation=rot)
    return bpy.context.object

def cutter_rounded_box(size, loc, radius, segments=3):
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
    obj = bpy.context.object
    obj.scale = (size[0] / 2.0, size[1] / 2.0, size[2] / 2.0)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel(obj, radius, segments=segments, angle=30.0, apply=True)
    obj.location = loc
    return obj

def boolean_diff(target, cutter):
    bpy.context.view_layer.objects.active = target
    mod = target.modifiers.new("Boolean", "BOOLEAN")
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = cutter
    apply_mod(target, mod)
    bpy.data.objects.remove(cutter, do_unlink=True)

def tube_curve(name, points, radius, mat, resolution=2):
    cu = bpy.data.curves.new(name, type='CURVE')
    cu.dimensions = '3D'
    cu.resolution_u = 2
    cu.bevel_depth = radius
    cu.bevel_resolution = resolution
    cu.use_fill_caps = True
    sp = cu.splines.new('POLY')
    sp.points.add(len(points) - 1)
    for i, p in enumerate(points):
        sp.points[i].co = (p[0], p[1], p[2], 1.0)
    obj = bpy.data.objects.new(name, cu)
    col.objects.link(obj)
    assign_mat(obj, mat)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target='MESH')
    obj = bpy.context.object
    shade_smooth(obj, 45.0)
    return obj

def bezier_points(p0, p1, p2, p3, n=36):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1.0 - t
        x = u**3 * p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0]
        y = u**3 * p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]
        z = u**3 * p0[2] + 3*u*u*t*p1[2] + 3*u*t*t*p2[2] + t**3*p3[2]
        pts.append((x, y, z))
    return pts

def text_mesh(name, body, size, loc, mat, extrude=0.0015, align='CENTER'):
    cu = bpy.data.curves.new(name, type='FONT')
    cu.body = body
    cu.size = size
    cu.align_x = align
    cu.align_y = 'CENTER'
    cu.extrude = extrude
    cu.resolution_u = 8
    obj = bpy.data.objects.new(name, cu)
    col.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = (pi / 2.0, 0.0, 0.0)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target='MESH')
    obj = bpy.context.object
    assign_mat(obj, mat)
    shade_smooth(obj, 25.0)
    return obj

def beam(name, path, width_outer, width_inner, thickness, mat, theta, bevel_width=0.0018, bevel_segments=3):
    """Curved rectangular cast spoke. path = [(r,y), ...] in the r/y plane."""
    n = len(path)
    verts = []
    rings = []
    for i, (r, y) in enumerate(path):
        t = i / (n - 1)
        w = width_outer + (width_inner - width_outer) * t
        if i == 0:
            dr = path[1][0] - path[0][0]
            dy = path[1][1] - path[0][1]
        elif i == n - 1:
            dr = path[-1][0] - path[-2][0]
            dy = path[-1][1] - path[-2][1]
        else:
            dr = path[i + 1][0] - path[i - 1][0]
            dy = path[i + 1][1] - path[i - 1][1]
        ur = Vector((cos(theta), 0.0, sin(theta)))
        ut = Vector((-sin(theta), 0.0, cos(theta)))
        T = (dr * ur + dy * Vector((0.0, 1.0, 0.0))).normalized()
        N = T.cross(ut).normalized()
        C = Vector((r * cos(theta), y, r * sin(theta)))
        ring = []
        for sw, sn in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
            p = C + ut * (sw * w / 2.0) + N * (sn * thickness / 2.0)
            ring.append(len(verts))
            verts.append(tuple(p))
        rings.append(ring)
    faces = []
    for i in range(n - 1):
        a = rings[i]
        b = rings[i + 1]
        for k in range(4):
            k2 = (k + 1) % 4
            faces.append((a[k], a[k2], b[k2], b[k]))
    faces.append((rings[0][0], rings[0][1], rings[0][2], rings[0][3]))
    faces.append((rings[-1][3], rings[-1][2], rings[-1][1], rings[-1][0]))
    obj = add_mesh_obj(name, verts, faces, mat, True, 30.0)
    if bevel_width > 0:
        bevel(obj, bevel_width, segments=bevel_segments, angle=30.0, apply=True)
        shade_smooth(obj, 30.0)
    return obj

# ----------------------------------------------------------------------------
# CABINET
# ----------------------------------------------------------------------------
cab = rounded_box("Cabinet_Body", (0.54, 0.58, 0.68), (0, 0, 0), 0.020, M['cabinet'], segments=6)
baf = rounded_box("Front_Baffle", (0.515, 0.018, 0.655), (0, -0.298, 0.0), 0.008, M['baffle'], segments=5)

for target in (baf, cab):
    c = cutter_cylinder(0.188, 0.13, (0, -0.25, 0.12), verts=128)
    boolean_diff(target, c)

well_profile = [(0.181, -0.290), (0.188, -0.290), (0.188, 0.020), (0.181, 0.020)]
well = revolve_y("Driver_Recess_Well", well_profile, 160, M['well'], smooth_angle=30.0)
# The revolve helper builds around the world Y axis; the driver bore is at z=0.12.
for v in well.data.vertices:
    v.co.z += 0.12
well.data.update()
cylinder("Recess_Back_Cap", 0.188, 0.008, (0, 0.024, 0.12), M['well'], verts=128, rot=(pi/2, 0, 0))
torus("Baffle_Roundover_Trim", 0.190, 0.0032, (0, -0.3075, 0.12), M['gloss_black'],
      major_segments=192, minor_segments=10, rot=(pi/2, 0, 0))

for target in (baf, cab):
    c = cutter_rounded_box((0.300, 0.115, 0.065), (0, -0.267, -0.235), 0.012, segments=4)
    boolean_diff(target, c)

duct_outer = rounded_box("Port_Duct_Outer", (0.306, 0.210, 0.068), (0, -0.200, -0.235), 0.008, M['well'], segments=4)
duct_inner = cutter_rounded_box((0.292, 0.220, 0.054), (0, -0.200, -0.235), 0.008, segments=4)
boolean_diff(duct_outer, duct_inner)
rounded_box("Port_Back_Wall", (0.306, 0.008, 0.068), (0, -0.092, -0.235), 0.003, M['well'], segments=3)

lip_outer = rounded_box("Port_Front_Lip", (0.322, 0.020, 0.084), (0, -0.311, -0.235), 0.008, M['gloss_black'], segments=4)
lip_inner = cutter_rounded_box((0.300, 0.030, 0.065), (0, -0.311, -0.235), 0.006, segments=4)
boolean_diff(lip_outer, lip_inner)

rounded_box("Top_Cap", (0.512, 0.552, 0.012), (0, 0, 0.346), 0.006, M['gloss_black'], segments=4)
rounded_box("Bottom_Plinth", (0.512, 0.552, 0.012), (0, 0, -0.346), 0.006, M['cabinet'], segments=4)

for ix in (-1, 1):
    for iy in (-1, 1):
        x = ix * 0.200
        y = iy * 0.200
        cylinder(f"Foot_{ix}_{iy}_Rubber", 0.036, 0.030, (x, y, -0.367), M['rubber'],
                 verts=48, bevel_width=0.004, bevel_segments=3)
        cylinder(f"Foot_{ix}_{iy}_Trim", 0.039, 0.006, (x, y, -0.3535), M['aluminum_dark'],
                 verts=48, bevel_width=0.0015, bevel_segments=2)

for sx in (-1, 1):
    rounded_box(f"Side_Grip_Plate_{sx}", (0.008, 0.180, 0.075), (sx * 0.2735, 0.0, 0.02),
                0.008, M['baffle'], segments=4)
    rounded_box(f"Side_Grip_Bar_{sx}", (0.012, 0.118, 0.018), (sx * 0.2815, 0.0, 0.02),
                0.005, M['steel'], segments=4)

rounded_box("Front_Badge_Plate", (0.138, 0.006, 0.040), (0, -0.3095, -0.130), 0.004,
            M['aluminum_dark'], segments=3)
text_mesh("Badge_SW12_Text", "SW-12", 0.017, (0, -0.3132, -0.1235), M['steel'], extrude=0.0012)
text_mesh("Badge_Subwoofer_Text", "SUBWOOFER", 0.0048, (0, -0.3132, -0.1405), M['steel'], extrude=0.0008)

for ix in (-1, 1):
    for iz in (-1, 1):
        x = ix * 0.232
        z = iz * 0.298
        cylinder(f"Baffle_Screw_{ix}_{iz}", 0.0045, 0.004, (x, -0.3095, z), M['screw'],
                 verts=24, rot=(pi/2, 0, 0), bevel_width=0.0008, bevel_segments=2)
        cylinder(f"Baffle_Screw_Socket_{ix}_{iz}", 0.0024, 0.002, (x, -0.3120, z), M['dark_metal'],
                 verts=6, rot=(pi/2, 0, 0))

# ----------------------------------------------------------------------------
# REAR AMPLIFIER PANEL
# ----------------------------------------------------------------------------
rounded_box("Amp_Panel", (0.430, 0.020, 0.380), (0, 0.300, 0.03), 0.012, M['baffle'], segments=4)
rounded_box("Amp_Panel_Inset", (0.396, 0.006, 0.346), (0, 0.3105, 0.03), 0.008, M['gloss_black'], segments=4)

rounded_box("Heatsink_Base", (0.210, 0.018, 0.250), (0.095, 0.320, 0.085), 0.004, M['dark_metal'], segments=3)
for i in range(10):
    x = 0.005 + i * 0.020
    rounded_box(f"Heatsink_Fin_{i:02d}", (0.0055, 0.040, 0.232), (x, 0.338, 0.085),
                0.0015, M['dark_metal'], segments=2)

knob_x, knob_z = -0.135, 0.105
cylinder("Volume_Knob", 0.036, 0.030, (knob_x, 0.330, knob_z), M['plastic'],
         verts=64, rot=(pi/2, 0, 0), bevel_width=0.003, bevel_segments=3)
for i in range(24):
    a = 2 * pi * i / 24
    x = knob_x + 0.0355 * cos(a)
    z = knob_z + 0.0355 * sin(a)
    rounded_box(f"Knurl_{i:02d}", (0.004, 0.024, 0.0055), (x, 0.332, z), 0.0012,
                M['plastic'], segments=2, rot=(0, -a, 0))
rounded_box("Volume_Indicator", (0.0022, 0.002, 0.016), (knob_x, 0.3465, knob_z + 0.012),
            0.0006, M['steel'], segments=2)
cylinder("Volume_Knob_Cap", 0.026, 0.003, (knob_x, 0.3465, knob_z), M['dark_metal'],
         verts=48, rot=(pi/2, 0, 0), bevel_width=0.001, bevel_segments=2)

knob2_x, knob2_z = -0.135, 0.015
cylinder("Crossover_Knob", 0.025, 0.024, (knob2_x, 0.328, knob2_z), M['plastic'],
         verts=48, rot=(pi/2, 0, 0), bevel_width=0.002, bevel_segments=3)
for i in range(18):
    a = 2 * pi * i / 18
    x = knob2_x + 0.0245 * cos(a)
    z = knob2_z + 0.0245 * sin(a)
    rounded_box(f"Knurl2_{i:02d}", (0.003, 0.019, 0.0045), (x, 0.330, z), 0.001,
                M['plastic'], segments=2, rot=(0, -a, 0))
rounded_box("Crossover_Indicator", (0.002, 0.002, 0.012), (knob2_x, 0.3405, knob2_z + 0.008),
            0.0005, M['steel'], segments=2)

for i, z in enumerate((-0.105, -0.135)):
    cylinder(f"RCA_Jack_{i}", 0.0085, 0.020, (-0.155, 0.324, z), M['gold'],
             verts=32, rot=(pi/2, 0, 0), bevel_width=0.001, bevel_segments=2)
    cylinder(f"RCA_Ring_{i}", 0.0135, 0.008, (-0.155, 0.316, z), M['plastic'],
             verts=32, rot=(pi/2, 0, 0), bevel_width=0.001, bevel_segments=2)
    cylinder(f"RCA_Hole_{i}", 0.0045, 0.003, (-0.155, 0.3345, z), M['well'],
             verts=24, rot=(pi/2, 0, 0))

cylinder("XLR_Connector", 0.019, 0.020, (-0.055, 0.322, -0.105), M['plastic'],
         verts=48, rot=(pi/2, 0, 0), bevel_width=0.002, bevel_segments=2)
for i, (dx, dz) in enumerate(((-0.007, 0.005), (0.007, 0.005), (0.0, -0.007))):
    cylinder(f"XLR_Pin_{i}", 0.0022, 0.006, (-0.055 + dx, 0.333, -0.105 + dz), M['gold'],
             verts=16, rot=(pi/2, 0, 0))

rounded_box("IEC_Socket", (0.062, 0.010, 0.044), (0.115, 0.317, -0.125), 0.004, M['plastic'], segments=3)
for i, dx in enumerate((-0.015, 0.0, 0.015)):
    rounded_box(f"IEC_Slot_{i}", (0.007, 0.004, 0.020), (0.115 + dx, 0.323, -0.125),
                0.0015, M['well'], segments=2)
rounded_box("Power_Switch", (0.030, 0.012, 0.020), (0.190, 0.320, -0.125), 0.003,
            M['plastic'], segments=3)
rounded_box("Power_Switch_Rocker", (0.018, 0.004, 0.010), (0.190, 0.327, -0.121),
            0.0015, M['dark_metal'], segments=2)
cylinder("Status_LED_Ring", 0.006, 0.005, (0.035, 0.319, -0.155), M['steel'],
         verts=32, rot=(pi/2, 0, 0), bevel_width=0.0008, bevel_segments=2)
cylinder("Status_LED", 0.0035, 0.004, (0.035, 0.322, -0.155), M['led'],
         verts=24, rot=(pi/2, 0, 0))

for ix in (-1, 1):
    for iz in (-1, 1):
        x = ix * 0.195
        z = 0.03 + iz * 0.170
        cylinder(f"Amp_Screw_{ix}_{iz}", 0.005, 0.004, (x, 0.312, z), M['screw'],
                 verts=24, rot=(pi/2, 0, 0), bevel_width=0.0008, bevel_segments=2)
        cylinder(f"Amp_Screw_Socket_{ix}_{iz}", 0.0028, 0.002, (x, 0.3145, z), M['dark_metal'],
                 verts=6, rot=(pi/2, 0, 0))

# ----------------------------------------------------------------------------
# DRIVER
# ----------------------------------------------------------------------------
driver_objects = []
def d_add(obj):
    driver_objects.append(obj)
    return obj

d_add(revolve_y("Driver_Gasket", [(0.181, 0.000), (0.208, 0.000), (0.208, 0.004), (0.181, 0.004)],
                160, M['rubber'], smooth_angle=30.0))

flange = revolve_y("Driver_Mounting_Flange",
                   [(0.181, -0.013), (0.208, -0.013), (0.208, 0.000), (0.181, 0.000)],
                   192, M['aluminum'], smooth_angle=32.0)
bevel(flange, 0.0018, segments=3, angle=28.0, apply=True)
shade_smooth(flange, 30.0)
d_add(flange)

for i in range(8):
    a = radians(22.5 + 45.0 * i)
    r = 0.195
    x, z = r * cos(a), r * sin(a)
    c = cutter_cylinder(0.0062, 0.060, (x, -0.007, z), verts=40)
    boolean_diff(flange, c)

for i in range(8):
    a = radians(22.5 + 45.0 * i)
    r = 0.195
    x, z = r * cos(a), r * sin(a)
    d_add(torus(f"Mount_Trim_{i}", 0.0077, 0.0011, (x, -0.0127, z), M['aluminum_dark'],
                major_segments=40, minor_segments=8, rot=(pi/2, 0, 0)))
    d_add(cylinder(f"Mount_Screw_{i}", 0.0062, 0.0042, (x, -0.0150, z), M['screw'],
                   verts=32, rot=(pi/2, 0, 0), bevel_width=0.0008, bevel_segments=2))
    d_add(cylinder(f"Mount_Socket_{i}", 0.0034, 0.0018, (x, -0.0172, z), M['dark_metal'],
                   verts=6, rot=(pi/2, 0, 0)))

surround_profile = []
for i in range(32):
    a = 2 * pi * i / 32
    surround_profile.append((0.174 + 0.021 * cos(a), -0.023 + 0.021 * 1.25 * sin(a)))
d_add(revolve_y("Rubber_Surround", surround_profile, 192, M['rubber'], smooth_angle=38.0))

cone_outer = []
cone_inner = []
for i in range(33):
    t = i / 32.0
    r = 0.158 + (0.068 - 0.158) * t
    y = -0.013 + (0.075 + 0.013) * t + 0.0065 * 4.0 * t * (1.0 - t)
    cone_outer.append((r, y))
for i in range(32, -1, -1):
    r, y = cone_outer[i]
    cone_inner.append((r, y + 0.0035))
d_add(revolve_y("Cone_Body", cone_outer + cone_inner, 192, M['cone'], smooth_angle=38.0))

for i in range(12):
    a = 2 * pi * i / 12 + radians(15)
    pts = []
    for k in range(24):
        t = 0.08 + 0.86 * k / 23.0
        r = 0.158 + (0.068 - 0.158) * t
        y = -0.013 + (0.075 + 0.013) * t + 0.0065 * 4.0 * t * (1.0 - t) - 0.0018
        pts.append((r * cos(a), y, r * sin(a)))
    d_add(tube_curve(f"Cone_Rib_{i:02d}", pts, 0.00125, M['cone_rib'], resolution=1))

d_add(torus("Cone_Seam_Ring", 0.158, 0.0018, (0, -0.013, 0), M['rubber'],
            major_segments=192, minor_segments=8, rot=(pi/2, 0, 0)))

cap_outer = []
cap_inner = []
for i in range(25):
    t = i / 24.0
    r = 0.072 * cos(pi * 0.5 * t)
    y = 0.068 - 0.086 * sin(pi * 0.5 * t)
    cap_outer.append((r, y))
for i in range(24, -1, -1):
    r, y = cap_outer[i]
    cap_inner.append((r, y + 0.004))
d_add(revolve_y("Dust_Cap", cap_outer + cap_inner, 192, M['dust'], smooth_angle=40.0))
d_add(torus("Dust_Cap_Base_Ring", 0.072, 0.0022, (0, 0.068, 0), M['rubber'],
            major_segments=192, minor_segments=8, rot=(pi/2, 0, 0)))
d_add(torus("Dust_Cap_Logo_Ring", 0.021, 0.0009, (0, 0.0035, 0), M['steel'],
            major_segments=96, minor_segments=6, rot=(pi/2, 0, 0)))

spider_outer = []
spider_inner = []
for i in range(41):
    t = i / 40.0
    r = 0.172 + (0.075 - 0.172) * t
    y = 0.085 + (0.075 - 0.085) * t + 0.0038 * sin(2 * pi * 4.0 * t) * sin(pi * t)
    spider_outer.append((r, y))
for i in range(40, -1, -1):
    r, y = spider_outer[i]
    spider_inner.append((r, y + 0.0016))
d_add(revolve_y("Corrugated_Spider", spider_outer + spider_inner, 160, M['spider'], smooth_angle=35.0))
d_add(revolve_y("Spider_Mount_Ring", [(0.170, 0.083), (0.185, 0.083), (0.185, 0.093), (0.170, 0.093)],
                160, M['aluminum_dark'], smooth_angle=30.0))

d_add(cylinder("Voice_Coil_Former", 0.047, 0.080, (0, 0.115, 0), M['kapton'],
               verts=96, bevel_width=0.001, bevel_segments=2))
for i in range(10):
    d_add(torus(f"Voice_Coil_Turn_{i:02d}", 0.049, 0.0013, (0, 0.083 + i * 0.0065, 0), M['copper'],
                major_segments=128, minor_segments=6, rot=(pi/2, 0, 0)))

basket_ring = revolve_y("Basket_Outer_Ring",
                        [(0.195, 0.012), (0.208, 0.012), (0.208, 0.045), (0.195, 0.045)],
                        192, M['aluminum'], smooth_angle=32.0)
bevel(basket_ring, 0.0018, segments=3, angle=28.0, apply=True)
shade_smooth(basket_ring, 30.0)
d_add(basket_ring)

for i in range(8):
    theta = radians(22.5 + 45.0 * i)
    path = []
    for k in range(18):
        t = k / 17.0
        r = 0.197 - 0.107 * t + 0.010 * sin(pi * t)
        y = 0.025 + 0.140 * t
        path.append((r, y))
    d_add(beam(f"Basket_Spoke_{i}", path, 0.034, 0.022, 0.012, M['aluminum'], theta,
               bevel_width=0.0020, bevel_segments=3))
    inlay_path = []
    for k in range(18):
        t = k / 17.0
        r = 0.197 - 0.107 * t + 0.010 * sin(pi * t)
        y = 0.025 + 0.140 * t - 0.0065
        inlay_path.append((r, y))
    d_add(beam(f"Basket_Spoke_Inlay_{i}", inlay_path, 0.0065, 0.0045, 0.0015, M['dark_metal'], theta,
               bevel_width=0.0004, bevel_segments=2))

d_add(revolve_y("Basket_Inner_Hub",
                [(0.078, 0.155), (0.100, 0.155), (0.100, 0.175), (0.078, 0.175)],
                160, M['aluminum'], smooth_angle=30.0))

d_add(cylinder("Magnet_Top_Plate", 0.105, 0.020, (0, 0.185, 0), M['aluminum'],
               verts=128, bevel_width=0.0022, bevel_segments=3))
d_add(cylinder("Ferrite_Magnet", 0.115, 0.090, (0, 0.240, 0), M['magnet'],
               verts=128, bevel_width=0.004, bevel_segments=4))
d_add(cylinder("Magnet_Bottom_Plate", 0.105, 0.020, (0, 0.295, 0), M['aluminum'],
               verts=128, bevel_width=0.0022, bevel_segments=3))
d_add(torus("Magnet_Center_Band", 0.116, 0.0026, (0, 0.240, 0), M['dark_metal'],
            major_segments=192, minor_segments=8, rot=(pi/2, 0, 0)))
d_add(cylinder("Rear_Pole_Vent", 0.040, 0.022, (0, 0.316, 0), M['dark_metal'],
               verts=96, bevel_width=0.0015, bevel_segments=2))
d_add(torus("Rear_Vent_Rim", 0.040, 0.0030, (0, 0.326, 0), M['aluminum_dark'],
            major_segments=96, minor_segments=8, rot=(pi/2, 0, 0)))
for i in range(8):
    a = 2 * pi * i / 8
    d_add(rounded_box(f"Rear_Vent_Bar_{i}", (0.078, 0.003, 0.0028),
                      (0, 0.327, 0), 0.001, M['dark_metal'], segments=2, rot=(0, -a, 0)))
for i in range(4):
    a = radians(45 + 90 * i)
    x, z = 0.075 * cos(a), 0.075 * sin(a)
    d_add(cylinder(f"Magnet_Bolt_{i}", 0.0050, 0.007, (x, 0.307, z), M['screw'],
                   verts=24, rot=(pi/2, 0, 0), bevel_width=0.0008, bevel_segments=2))
    d_add(cylinder(f"Magnet_Bolt_Socket_{i}", 0.0028, 0.002, (x, 0.310, z), M['dark_metal'],
                   verts=6, rot=(pi/2, 0, 0)))

d_add(rounded_box("Terminal_Pod", (0.016, 0.018, 0.040), (0.208, -0.006, 0.0),
                  0.004, M['plastic'], segments=3))
for i, (z, collar_mat, name) in enumerate(((-0.012, M['red'], 'Red'), (0.012, M['plastic'], 'Black'))):
    d_add(cylinder(f"Terminal_Post_{name}", 0.0032, 0.014, (0.208, -0.019, z), M['gold'],
                   verts=24, rot=(pi/2, 0, 0), bevel_width=0.0005, bevel_segments=2))
    d_add(cylinder(f"Terminal_Collar_{name}", 0.0058, 0.006, (0.208, -0.015, z), collar_mat,
                   verts=32, rot=(pi/2, 0, 0), bevel_width=0.0008, bevel_segments=2))
    d_add(cylinder(f"Terminal_Cap_{name}", 0.0036, 0.002, (0.208, -0.027, z), M['gold'],
                   verts=24, rot=(pi/2, 0, 0), bevel_width=0.0004, bevel_segments=2))

for i, z in enumerate((-0.012, 0.012)):
    p0 = (0.200, 0.006, z)
    p1 = (0.175, 0.025, z * 1.5)
    p2 = (0.115, 0.065, z * 1.8)
    p3 = (0.072, 0.076, z * 0.8)
    pts = bezier_points(p0, p1, p2, p3, 44)
    d_add(tube_curve(f"Tinsel_Lead_{i}", pts, 0.00135, M['copper'], resolution=2))

DRIVER_ORIGIN = Vector((0.0, -0.311, 0.12))
for obj in driver_objects:
    obj.location = obj.location + DRIVER_ORIGIN

# ----------------------------------------------------------------------------
# Final stats and OBJ export
# ----------------------------------------------------------------------------
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
total_verts = 0
total_tris = 0
for obj in col.objects:
    if obj.type != 'MESH':
        continue
    ev = obj.evaluated_get(depsgraph)
    mesh = ev.to_mesh()
    total_verts += len(mesh.vertices)
    mesh.calc_loop_triangles()
    total_tris += len(mesh.loop_triangles)
    ev.to_mesh_clear()
print(f"STATS objects={len(col.objects)} verts={total_verts} tris={total_tris}")

bpy.ops.wm.obj_export(
    filepath=OUT_OBJ,
    export_animation=False,
    forward_axis='NEGATIVE_Z',
    up_axis='Y',
    global_scale=1.0,
    apply_modifiers=True,
    export_selected_objects=False,
    export_uv=False,
    export_normals=True,
    export_colors=False,
    export_materials=True,
    export_pbr_extensions=True,
    path_mode='AUTO',
    export_triangulated_mesh=True,
    export_object_groups=True,
    export_material_groups=True,
    export_smooth_groups=False,
)
print("EXPORTED", OUT_OBJ)
