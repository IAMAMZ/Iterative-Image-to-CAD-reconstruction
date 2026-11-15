import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,57,0))
r=w0.workplane(offset=-113/2).moveTo(0,0).box(200,125,113).union(w0.workplane(offset=-5/2).box(196.5,117.5,5))