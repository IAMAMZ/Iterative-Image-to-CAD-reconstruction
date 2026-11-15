import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
r=w0.workplane(offset=200/2).moveTo(0,0).cylinder(200,3.5).union(w0.workplane(offset=200/2).cylinder(200,3))