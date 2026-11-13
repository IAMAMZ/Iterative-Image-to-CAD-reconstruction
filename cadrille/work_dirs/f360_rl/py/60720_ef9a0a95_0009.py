import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,40,0))
r=w0.workplane(offset=-80/2).cylinder(80,100).union(w0.workplane(offset=-49/2).cylinder(49,96))