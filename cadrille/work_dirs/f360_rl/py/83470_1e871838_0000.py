import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,18.5,0))
r=w0.workplane(offset=-37/2).moveTo(0,0).box(200,100,37).union(w0.workplane(offset=-6/2).box(186.5,89.5,6))