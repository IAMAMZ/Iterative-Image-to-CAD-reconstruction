import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,78,0))
w1=cq.Workplane('XY',origin=(0,0,-100))
r=w0.sketch().segment((-84,-37),(95,-86.5)).arc((98,-57),(83,-44)).segment((-50,-3)).segment((-52,31)).segment((-40,59)).segment((-50,74.5)).segment((-69,86)).segment((-73.5,74.5)).segment((-84,59.5)).close().assemble().finalize().extrude(-156).union(w1.workplane(offset=10/2).moveTo(12,0).cylinder(10,12.5)).union(w1.workplane(offset=9/2).moveTo(12,76.5).box(1.5,1.5,1))