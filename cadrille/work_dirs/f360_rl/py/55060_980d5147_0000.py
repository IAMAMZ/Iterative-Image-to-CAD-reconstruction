import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,25,0))
r=w0.workplane(offset=-50/2).moveTo(0,0).box(100,200,50).union(w0.workplane(offset=-13/2).box(94,182.5,13))