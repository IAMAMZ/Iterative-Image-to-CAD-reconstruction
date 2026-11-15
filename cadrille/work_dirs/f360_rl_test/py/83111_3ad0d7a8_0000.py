import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,35))
w1=cq.Workplane('ZX',origin=(0,-100,0))
r=w0.workplane(offset=-70/2).moveTo(0,38.5).box(50,117.5,70).union(w0.sketch().segment((-23,-22),(25,-22)).segment((25,-18.5)).segment((-23,-17)).close().assemble().finalize().extrude(-8.5)).union(w0.workplane(offset=-6/2).moveTo(0,70).cylinder(6,28.5)).union(w1.workplane(offset=89/2).cylinder(89,7.5)).union(w1.workplane(offset=1/2).moveTo(-30.5,0).box(8.5,40.5,1))