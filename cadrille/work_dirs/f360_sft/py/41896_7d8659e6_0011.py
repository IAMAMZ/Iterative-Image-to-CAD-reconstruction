import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-70))
w1=cq.Workplane('XY',origin=(0,0,-100))
r=w0.workplane(offset=-17/2).cylinder(17,25).union(w0.workplane(offset=170/2).cylinder(170,9)).union(w1.workplane(offset=35/2).cylinder(35,22))