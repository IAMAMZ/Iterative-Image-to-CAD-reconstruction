import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,20,0))
r=w0.workplane(offset=-40/2).moveTo(0,0).box(200,40,40).union(w0.workplane(offset=-11/2).box(190,13.5,11))