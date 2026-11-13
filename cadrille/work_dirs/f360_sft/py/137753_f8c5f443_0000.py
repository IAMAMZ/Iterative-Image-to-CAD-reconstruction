import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,89,0))
r=w0.workplane(offset=-178/2).cylinder(178,19).union(w0.workplane(offset=-89/2).box(66,200,89))