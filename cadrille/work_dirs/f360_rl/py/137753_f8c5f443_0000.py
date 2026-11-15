import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,0,0))
r=w0.workplane(offset=-89/2).cylinder(89,19.5).union(w0.workplane(offset=89/2).box(66.5,200,89)).union(w0.workplane(offset=1/2).box(1,1.5,1))