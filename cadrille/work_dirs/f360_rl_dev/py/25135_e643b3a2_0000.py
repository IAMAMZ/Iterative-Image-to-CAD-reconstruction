import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
w1=cq.Workplane('XY',origin=(0,0,86))
r=w0.workplane(offset=14/2).cylinder(14,50).union(w0.workplane(offset=177/2).cylinder(177,38)).union(w1.workplane(offset=14/2).cylinder(14,50)).union(w1.workplane(offset=14/2).cylinder(14,48))