import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-90,0))
r=w0.workplane(offset=-10/2).cylinder(10,18).union(w0.workplane(offset=190/2).cylinder(190,12))