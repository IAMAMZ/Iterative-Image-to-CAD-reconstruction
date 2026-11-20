import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,34))
r=w0.workplane(offset=-67/2).cylinder(67,100).union(w0.workplane(offset=-39/2).cylinder(39,96))