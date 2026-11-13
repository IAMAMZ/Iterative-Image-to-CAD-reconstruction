import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,96,0))
r=w0.workplane(offset=-196/2).box(76,30,196).union(w0.workplane(offset=4/2).box(136,60,4))