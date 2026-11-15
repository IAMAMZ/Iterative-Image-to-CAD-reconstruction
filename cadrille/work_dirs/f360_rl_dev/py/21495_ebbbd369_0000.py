import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,2))
r=w0.workplane(offset=-4.5/2).box(200,156,4.5).union(w0.workplane(offset=-4/2).box(196,150.5,4))