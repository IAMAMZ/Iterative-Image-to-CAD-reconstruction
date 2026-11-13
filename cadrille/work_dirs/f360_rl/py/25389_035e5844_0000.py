import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,11,0))
r=w0.workplane(offset=-34/2).box(200,200,34).union(w0.workplane(offset=12/2).cylinder(12,40))