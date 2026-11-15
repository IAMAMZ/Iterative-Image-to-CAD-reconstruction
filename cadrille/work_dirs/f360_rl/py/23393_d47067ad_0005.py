import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.workplane(offset=2/2).moveTo(0,0).box(1.5,200,2).union(w0.workplane(offset=26/2).moveTo(0,-99).box(1,1,26))