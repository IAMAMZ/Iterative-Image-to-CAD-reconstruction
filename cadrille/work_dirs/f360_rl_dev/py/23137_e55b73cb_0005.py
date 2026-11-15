import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
r=w0.workplane(offset=200/2).moveTo(0,0).cylinder(200,12.5).union(w0.workplane(offset=20/2).box(1.5,1.5,10))