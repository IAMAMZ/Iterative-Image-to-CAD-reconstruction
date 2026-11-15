import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-4,0))
r=w0.workplane(offset=-96/2).cylinder(96,78).union(w0.workplane(offset=104/2).cylinder(104,32.5)).union(w0.workplane(offset=104/2).box(1.5,1.5,104))