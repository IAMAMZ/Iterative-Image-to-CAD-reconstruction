import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
r=w0.workplane(offset=33/2).moveTo(-0,0).box(18.5,17,33).union(w0.workplane(offset=200/2).cylinder(200,13)).union(w0.workplane(offset=20/2).box(1.5,1.5,7))