import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-27))
w1=cq.Workplane('ZX',origin=(0,-100,0))
r=w0.sketch().segment((-33,-100),(-20,-99)).segment((-18,-77)).segment((-20,49)).segment((-33,51)).close().assemble().finalize().extrude(19.5).union(w0.workplane(offset=54/2).moveTo(-30,98.5).box(2.5,3,54.5)).union(w1.workplane(offset=73/2).moveTo(24,30).cylinder(73,2)).union(w1.workplane(offset=2/2).moveTo(-20,-29.5).box(3,4,1))