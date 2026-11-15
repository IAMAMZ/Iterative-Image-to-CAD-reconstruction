import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-57))
r=w0.workplane(offset=-43/2).cylinder(43,22).union(w0.workplane(offset=19/2).cylinder(19,38)).union(w0.workplane(offset=157/2).cylinder(157,30))