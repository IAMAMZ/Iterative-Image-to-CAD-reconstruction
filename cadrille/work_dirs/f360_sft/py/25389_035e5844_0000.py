import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-23,0))
r=w0.workplane(offset=33/2).box(200,200,33).union(w0.workplane(offset=47/2).cylinder(47,41))