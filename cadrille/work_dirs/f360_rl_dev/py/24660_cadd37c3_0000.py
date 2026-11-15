import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,69))
r=w0.workplane(offset=-169/2).cylinder(169,32.5).union(w0.workplane(offset=31/2).cylinder(31,22))