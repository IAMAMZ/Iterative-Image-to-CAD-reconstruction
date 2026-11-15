import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.workplane(offset=-200/2).cylinder(200,52.5).union(w0.workplane(offset=-89/2).cylinder(89,51))