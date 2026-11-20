import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,67))
r=w0.workplane(offset=-140/2).moveTo(0,0).box(200,55,140).union(w0.workplane(offset=4/2).moveTo(80.5,26.5).box(1.5,1.5,4))