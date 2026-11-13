import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-100,0))
r=w0.workplane(offset=4/2).cylinder(4,12.5).union(w0.workplane(offset=200/2).cylinder(200,8.5)).union(w0.workplane(offset=2/2).box(1.5,1.5,1))