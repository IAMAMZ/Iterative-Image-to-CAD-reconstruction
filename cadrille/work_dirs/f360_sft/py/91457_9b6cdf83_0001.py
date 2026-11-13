import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-38))
r=w0.workplane(offset=-62/2).cylinder(62,22).union(w0.workplane(offset=-18/2).cylinder(18,39)).union(w0.workplane(offset=138/2).cylinder(138,31))