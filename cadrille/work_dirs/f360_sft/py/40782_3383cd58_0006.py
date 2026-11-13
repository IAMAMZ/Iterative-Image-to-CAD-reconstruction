import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,58))
r=w0.workplane(offset=-158/2).cylinder(158,28).union(w0.workplane(offset=42/2).cylinder(42,62))