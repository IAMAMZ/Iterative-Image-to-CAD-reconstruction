import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
r=w0.workplane(offset=109/2).cylinder(109,49.5).union(w0.workplane(offset=200/2).cylinder(200,50))