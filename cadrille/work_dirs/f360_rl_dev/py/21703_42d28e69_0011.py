import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,83))
r=w0.workplane(offset=-167/2).cylinder(167,100).union(w0.workplane(offset=-100/2).cylinder(100,9))